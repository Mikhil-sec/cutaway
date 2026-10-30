"""Render one 2.5D shot in Blender from a shot spec (JSON).

Run headless:
    blender -b --factory-startup -P cutaway/blender_shot.py -- shot.json out_dir

Each layer is an unlit, alpha-blended image plane placed at its depth and sized
so that, from the reference camera (origin, 35 mm), every layer lines up
exactly with the original still. Moving the camera gives true parallax.

Everything that moves is keyed on every frame from Python, so easing, shake and
puppet motion don't depend on Blender's animation-curve API.

Shot spec:
    fps, seconds, resolution [w, h], image_size [w, h] (pixels of the stills)
    layers: [{name, image, depth, pivot?: [px, py], follow?: layer name, anim?: {...}}]
        anim.rot:     [[t, degrees counter-clockwise], ...]  (around pivot)
        anim.breathe: {amp, period}                          (vertical scale around pivot)
      or puppet layers (characters), which bend smoothly instead of hinging:
        {name, image, depth, puppet: {weights, pivot, feet},
         anim?: {bend: [[t, deg], ...], breathe: {amp, period, phase?}, hop: [[t, units], ...]}}
      or wind layers (plants, umbrellas): {name, image, depth, wind: {amp, period}}
    fog: [{depth, opacity, speed, color?: [r, g, b]}]
    shadows: [{feet: [px, py], width_px, depth, opacity?}]   (contact shadows under characters)
    effects: [{type: "motes", depth, opacity?, scale?, drift?: [u/s, v/s]}
              | {type: "flashes", depth, count?, rate? (per second each), peak?, seed?}]
    camera: {keys: [{t, pos: [x, y, z], lens?, focus?: layer name, pitch?, yaw?, roll?}],
             fstop?, shake?: {deg, units, hz}}
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cutaway.camera import REF_LENS_MM, SENSOR_MM, edge_overshoot, layer_size, pixel_to_world  # noqa: E402

BEND_MAX_DEG = 10.0  # the bend shape key at value 1; keyed values scale it


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:]
    # Absolute paths: Blender resolves relative ones against its own directory, not the shell's.
    return json.loads(Path(argv[0]).resolve().read_text()), Path(argv[1]).resolve()


def set_engine(scene):
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            return
        except TypeError:
            continue


def smooth(a, b, u):
    u = u * u * (3 - 2 * u)  # ease in and out
    return a + (b - a) * u


def keyed(keys, t):
    """Value at time t from [[t, value], ...] with eased interpolation; holds at the ends."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return smooth(v0, v1, (t - t0) / (t1 - t0))
    return keys[-1][1]


def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    else:
        mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    mat.node_tree.nodes.clear()
    return mat


def finish_unlit(nt, color_out, alpha_out):
    emit = nt.nodes.new("ShaderNodeEmission")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if isinstance(color_out, tuple):
        emit.inputs["Color"].default_value = (*color_out, 1)
    else:
        nt.links.new(color_out, emit.inputs["Color"])
    nt.links.new(alpha_out, mix.inputs["Fac"])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(emit.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def image_material(name, path):
    mat = new_material(name)
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path))
    tex.extension = "EXTEND"
    finish_unlit(nt, tex.outputs["Color"], tex.outputs["Alpha"])
    return mat


def fog_material(name, opacity, color):
    """Soft animated noise; returns the material and the noise node's W socket to key."""
    mat = new_material(name)
    nt = mat.node_tree
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 2.2
    noise.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.8
    strength = nt.nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = opacity
    nt.links.new(coord.outputs["UV"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], strength.inputs[0])
    finish_unlit(nt, tuple(color), strength.outputs[0])
    return mat, noise.inputs["W"]


def add_plane(name, depth, aspect, mat):
    w, h = layer_size(depth, aspect)
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, depth, 0), rotation=(math.pi / 2, 0, 0))
    plane = bpy.context.active_object
    plane.name = name
    plane.scale = (w / 2, h / 2, 1)
    plane.data.materials.append(mat)
    return plane


def add_grid_layer(name, depth, aspect, mat, cols=64, rows=36):
    """An image layer as a grid mesh (object at its depth) so it can deform, e.g. sway in the wind."""
    w, h = layer_size(depth, aspect)
    us, vs = np.linspace(0, 1, cols), np.linspace(0, 1, rows)
    verts = [((u - 0.5) * w, 0.0, (v - 0.5) * h) for v in vs for u in us]
    faces = [(r * cols + c, r * cols + c + 1, (r + 1) * cols + c + 1, (r + 1) * cols + c)
             for r in range(rows - 1) for c in range(cols - 1)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv.data[li].uv = (us[vi % cols], vs[vi // cols])
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (0.0, depth, 0.0)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj, verts, w


def add_wind_layer(i, layer, aspect):
    """A layer whose upper parts sway more than their base: plants, umbrellas, hanging things."""
    depth = float(layer["depth"])
    obj, verts, w = add_grid_layer(layer.get("name", f"layer_{i}"), depth, aspect,
                                   image_material(f"mat_{i}", layer["image"]))
    obj.shape_key_add(name="Basis")
    sway = obj.shape_key_add(name="sway")
    sway.slider_min, sway.slider_max = -2.0, 2.0
    zs = [z for _, _, z in verts]
    z0, z1 = min(zs), max(zs)
    reach = 0.012 * w  # sway at the very top, in scene units
    for vi, (x, y, z) in enumerate(verts):
        v = (z - z0) / (z1 - z0)
        sway.data[vi].co = (x + reach * v ** 1.6, y, z - 0.15 * reach * v ** 2)
    return obj, sway


def motes_material(name, opacity, scale, seed):
    """Small soft specks (dust, pollen) from a Voronoi texture; returns material and mapping Location socket."""
    mat = new_material(name)
    nt = mat.node_tree
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale * 16 / 9, scale, 1)
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 1.0
    vor.inputs["Randomness"].default_value = 1.0
    if "W" in vor.inputs:
        vor.voronoi_dimensions = "4D"
        vor.inputs["W"].default_value = seed
    ramp = nt.nodes.new("ShaderNodeValToRGB")  # distance 0 -> opaque speck, fading to clear by 0.05
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.05
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    strength = nt.nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = opacity
    nt.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], strength.inputs[0])
    finish_unlit(nt, (1.0, 0.95, 0.85), strength.outputs[0])
    return mat, mapping.inputs["Location"]


def glow_material(name):
    """A soft round glow (a camera flash seen from afar); returns material and its strength socket."""
    mat = new_material(name)
    nt = mat.node_tree
    coord = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    centre = nt.nodes.new("ShaderNodeMapping")  # move the gradient's centre to the plane's middle
    centre.inputs["Location"].default_value = (-1, -1, 0)
    centre.inputs["Scale"].default_value = (2, 2, 1)
    strength = nt.nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = 0.0
    nt.links.new(coord.outputs["UV"], centre.inputs["Vector"])
    nt.links.new(centre.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], strength.inputs[0])
    finish_unlit(nt, (1.0, 1.0, 1.0), strength.outputs[0])
    return mat, strength.inputs[1]


def add_shadow(i, layer, aspect, image_size):
    """A soft contact shadow under a character's feet, on the ground just behind the character."""
    depth = float(layer["depth"]) + 0.05
    fx, _, fz = pixel_to_world(*layer["feet"], depth, image_size, aspect)
    w = layer["width_px"] / image_size[0] * layer_size(depth, aspect)[0] * 0.95
    mat, strength = glow_material(f"shadow_{i}")
    nt = mat.node_tree
    emit = next(n for n in nt.nodes if n.type == "EMISSION")
    emit.inputs["Color"].default_value = (0, 0, 0, 1)
    strength.default_value = layer.get("opacity", 0.45)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(fx, depth, fz), rotation=(math.pi / 2, 0, 0))
    plane = bpy.context.active_object
    plane.name = f"shadow_{i}"
    plane.scale = (w, w * 0.16, 1)
    plane.data.materials.append(mat)
    return plane


def add_puppet(i, layer, aspect, image_size):
    """A character as one subdivided mesh that bends smoothly instead of hinging.

    layer.puppet: {weights: .npy grid (rows bottom-to-top) of how much each vertex
    follows the head, pivot: [px, py] (neck), feet: [px, py]}. Shape keys:
    'bend' rotates each vertex around the neck by BEND_MAX_DEG x its weight;
    'breathe' swells the body up from the feet.
    """
    pup = layer["puppet"]
    depth = float(layer["depth"])
    weights = np.load(pup["weights"])
    rows, cols = weights.shape
    w, h = layer_size(depth, aspect)
    us = np.linspace(0, 1, cols)
    vs = np.linspace(0, 1, rows)
    # Local coordinates with the object at its depth: Eevee sorts see-through objects
    # by origin, so an origin at the camera would draw the puppet over nearer layers.
    verts = [((u - 0.5) * w, 0.0, (v - 0.5) * h) for v in vs for u in us]
    faces = [(r * cols + c, r * cols + c + 1, (r + 1) * cols + c + 1, (r + 1) * cols + c)
             for r in range(rows - 1) for c in range(cols - 1)]
    mesh = bpy.data.meshes.new(f"puppet_{i}")
    mesh.from_pydata(verts, [], faces)
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv.data[li].uv = (us[vi % cols], vs[vi // cols])
    obj = bpy.data.objects.new(layer.get("name", f"puppet_{i}"), mesh)
    obj.location = (0.0, depth, 0.0)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(image_material(f"mat_{i}", layer["image"]))

    nx, _, nz = pixel_to_world(*pup["pivot"], depth, image_size, aspect)
    fx, _, fz = pixel_to_world(*pup["feet"], depth, image_size, aspect)
    obj.shape_key_add(name="Basis")
    bend = obj.shape_key_add(name="bend")
    breathe = obj.shape_key_add(name="breathe")
    th = math.radians(BEND_MAX_DEG)
    flat = weights.reshape(-1)
    for vi, (x, y, z) in enumerate(verts):
        a = th * flat[vi]
        dx, dz = x - nx, z - nz
        bend.data[vi].co = (nx + dx * math.cos(a) - dz * math.sin(a), y, nz + dx * math.sin(a) + dz * math.cos(a))
        breathe.data[vi].co = (fx + (x - fx) * 0.994, y, fz + (z - fz) * 1.02)
    for key in (bend, breathe):
        key.slider_min, key.slider_max = -2.0, 2.0
    return obj, {"bend": bend, "breathe": breathe}


def add_image_layer(i, layer, aspect, image_size):
    depth = float(layer["depth"])
    plane = add_plane(layer.get("name", f"layer_{i}"), depth, aspect, image_material(f"mat_{i}", layer["image"]))
    if "pivot" not in layer:
        return plane, None
    # Parent to an empty at the pivot so rotation and scale happen around it.
    piv = bpy.data.objects.new(f"{plane.name}_pivot", None)
    bpy.context.scene.collection.objects.link(piv)
    piv.location = pixel_to_world(*layer["pivot"], depth, image_size, aspect)
    plane.parent = piv
    plane.location = (plane.location.x - piv.location.x, 0, plane.location.z - piv.location.z)
    return plane, piv


class Shake:
    """Smooth pseudo-random handheld motion: a few incommensurate sines per channel."""

    def __init__(self, hz, seed=7):
        rnd = random.Random(seed)
        self.ch = [[(hz * rnd.uniform(0.5, 1.6), rnd.uniform(0, 6.3)) for _ in range(3)] for _ in range(6)]

    def __call__(self, i, t):
        return sum(math.sin(2 * math.pi * f * t + p) for f, p in self.ch[i]) / 3


def check_edges(spec, aspect, frames):
    """Warn when the camera would see past the background painting's edge."""
    back = max(spec["layers"], key=lambda l: l["depth"])["depth"]
    worst = max(edge_overshoot(back, aspect, pos, lens, pitch, yaw) for t, pos, lens, pitch, yaw in frames)
    if worst > 0:
        print(f"EDGE WARNING: the camera sees {worst:.2f} units past the background edge")
    else:
        print("edge check: ok")
    return worst


def main():
    spec, out_dir = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    set_engine(scene)
    w, h = spec["resolution"]
    aspect = w / h
    image_size = spec.get("image_size", [2048, 1152])
    fps = spec["fps"]
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.fps = fps
    scene.frame_start, scene.frame_end = 1, int(fps * spec["seconds"])
    scene.view_settings.view_transform = "Standard"  # keep the painting's colours as painted
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out_dir / "frame_")
    world = bpy.data.worlds.new("world")
    world.color = (0, 0, 0)
    scene.world = world

    cam_data = bpy.data.cameras.new("cam")
    cam_data.sensor_width = SENSOR_MM
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.clip_start = 0.05
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    depths = {}
    pivots = {}
    animated = []
    puppets, winds = [], []
    for i, layer in enumerate(spec["layers"]):
        if "puppet" in layer:
            obj, shape_keys = add_puppet(i, layer, aspect, image_size)
            depths[obj.name] = float(layer["depth"])
            puppets.append((obj, shape_keys, layer.get("anim", {})))
            continue
        if "wind" in layer:
            obj, sway = add_wind_layer(i, layer, aspect)
            depths[obj.name] = float(layer["depth"])
            winds.append((sway, layer["wind"], random.Random(i).uniform(0, 6.3)))
            continue
        plane, piv = add_image_layer(i, layer, aspect, image_size)
        depths[plane.name] = float(layer["depth"])
        if piv is not None:
            pivots[plane.name] = piv
            if "anim" in layer:
                animated.append((piv, layer["anim"]))
    for layer in spec["layers"]:
        if "follow" in layer:  # e.g. the head rides on the breathing body
            piv, parent = pivots[layer["name"]], pivots[layer["follow"]]
            piv.parent = parent
            piv.location = piv.location - parent.location

    fog_sockets = []
    for j, fog in enumerate(spec.get("fog", [])):
        mat, w_socket = fog_material(f"fog_{j}", fog["opacity"], fog.get("color", [0.82, 0.86, 0.9]))
        add_plane(f"fog_{j}", float(fog["depth"]), aspect, mat)
        fog_sockets.append((w_socket, fog.get("speed", 0.08)))

    for j, sh in enumerate(spec.get("shadows", [])):
        add_shadow(j, sh, aspect, image_size)

    motes, flashes = [], []
    for j, fx in enumerate(spec.get("effects", [])):
        depth = float(fx["depth"])
        if fx["type"] == "motes":
            mat, loc = motes_material(f"motes_{j}", fx.get("opacity", 0.5), fx.get("scale", 26), j + 1)
            add_plane(f"motes_{j}", depth, aspect, mat)
            motes.append((loc, fx.get("drift", [0.02, -0.012])))
        elif fx["type"] == "flashes":
            rnd = random.Random(fx.get("seed", 5))
            w, h = layer_size(depth, aspect)
            for n in range(fx.get("count", 6)):
                mat, strength = glow_material(f"flash_{j}_{n}")
                size = w * rnd.uniform(0.05, 0.1)
                bpy.ops.mesh.primitive_plane_add(size=1, location=(rnd.uniform(-0.4, 0.4) * w, depth,
                                                                   rnd.uniform(-0.15, 0.3) * h),
                                                 rotation=(math.pi / 2, 0, 0))
                plane = bpy.context.active_object
                plane.name = f"flash_{j}_{n}"
                plane.scale = (size, size, 1)
                plane.data.materials.append(mat)
                t, events = rnd.uniform(0.2, 1.5), []
                while t < spec["seconds"]:
                    events.append(t)
                    t += rnd.expovariate(fx.get("rate", 0.35))
                flashes.append((strength, events, fx.get("peak", 0.9)))

    c = spec["camera"]
    keys = c["keys"]
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = c.get("fstop", 2.8)
    shake = Shake(c.get("shake", {}).get("hz", 0.6))
    sh_deg = c.get("shake", {}).get("deg", 0.0)
    sh_units = c.get("shake", {}).get("units", 0.0)

    def track(field, default):
        return [[k["t"], k.get(field, default)] for k in keys]

    pos_tracks = [[[k["t"], k["pos"][a]] for k in keys] for a in range(3)]
    lens_t, pitch_t, yaw_t, roll_t = track("lens", REF_LENS_MM), track("pitch", 0), track("yaw", 0), track("roll", 0)
    focus_keys = [[k["t"], depths[k["focus"]]] for k in keys if "focus" in k]

    sampled = []
    for f in range(scene.frame_start, scene.frame_end + 1):
        t = (f - 1) / fps
        pos = [keyed(tr, t) + sh_units * shake(a, t) for a, tr in enumerate(pos_tracks)]
        lens = keyed(lens_t, t)
        pitch = keyed(pitch_t, t) + sh_deg * shake(3, t)
        yaw = keyed(yaw_t, t) + sh_deg * shake(4, t)
        roll = keyed(roll_t, t) + sh_deg * 0.5 * shake(5, t)
        cam.location = pos
        cam.rotation_euler = (math.radians(90 + pitch), math.radians(roll), math.radians(yaw))
        cam_data.lens = lens
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        cam_data.keyframe_insert("lens", frame=f)
        if focus_keys:
            cam_data.dof.focus_distance = max(0.1, keyed(focus_keys, t) - pos[1])
            cam_data.dof.keyframe_insert("focus_distance", frame=f)
        for piv, anim in animated:
            if "rot" in anim:
                piv.rotation_euler = (0, -math.radians(keyed(anim["rot"], t)), 0)
                piv.keyframe_insert("rotation_euler", frame=f)
            if "breathe" in anim:
                b = anim["breathe"]
                piv.scale = (1, 1, 1 + b["amp"] * math.sin(2 * math.pi * t / b["period"]))
                piv.keyframe_insert("scale", frame=f)
        for obj, shape_keys, anim in puppets:
            if "bend" in anim:  # [[t, degrees counter-clockwise], ...]
                shape_keys["bend"].value = keyed(anim["bend"], t) / BEND_MAX_DEG
                shape_keys["bend"].keyframe_insert("value", frame=f)
            b = anim.get("breathe")
            if b:
                shape_keys["breathe"].value = b["amp"] * math.sin(2 * math.pi * t / b["period"] + b.get("phase", 0))
                shape_keys["breathe"].keyframe_insert("value", frame=f)
            if "hop" in anim:  # [[t, scene units up], ...]
                obj.location.z = keyed(anim["hop"], t)  # x and y stay at (0, depth)
                obj.keyframe_insert("location", frame=f)
        for socket, speed in fog_sockets:
            socket.default_value = t * speed
            socket.keyframe_insert("default_value", frame=f)
        for sway, wind, phase in winds:
            p = wind.get("period", 3.2)
            sway.value = wind.get("amp", 1.0) * (math.sin(2 * math.pi * t / p + phase)
                                                 + 0.35 * math.sin(2 * math.pi * t / (p * 0.37) + 2 * phase))
            sway.keyframe_insert("value", frame=f)
        for loc, drift in motes:
            loc.default_value = (drift[0] * t, drift[1] * t, 0)
            loc.keyframe_insert("default_value", frame=f)
        for strength, events, peak in flashes:
            strength.default_value = peak * sum(math.exp(-(t - e) / 0.07) for e in events if 0 <= t - e < 0.5)
            strength.keyframe_insert("default_value", frame=f)
        sampled.append((t, pos, lens, pitch, yaw))

    check_edges(spec, aspect, sampled)
    if "--check-only" in sys.argv:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    if "--stills" in sys.argv:  # quick look: render only the listed frames
        for f in map(int, sys.argv[sys.argv.index("--stills") + 1].split(",")):
            scene.frame_set(f)
            scene.render.filepath = str(out_dir / f"still_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    bpy.ops.render.render(animation=True)


main()
