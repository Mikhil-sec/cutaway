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
    fog: [{depth, opacity, speed, color?: [r, g, b]}]
    camera: {keys: [{t, pos: [x, y, z], lens?, focus?: layer name, pitch?, yaw?, roll?}],
             fstop?, shake?: {deg, units, hz}}
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy

SENSOR_MM = 36.0
REF_LENS_MM = 35.0
OVERSCAN = 1.25  # same factor on every layer: alignment holds, and moves have room before the edges show


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


def layer_size(depth, aspect):
    width = depth * SENSOR_MM / REF_LENS_MM * OVERSCAN
    return width, width / aspect


def add_plane(name, depth, aspect, mat):
    w, h = layer_size(depth, aspect)
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, depth, 0), rotation=(math.pi / 2, 0, 0))
    plane = bpy.context.active_object
    plane.name = name
    plane.scale = (w / 2, h / 2, 1)
    plane.data.materials.append(mat)
    return plane


def pixel_to_world(px, py, depth, image_size, aspect):
    """Where pixel (px, py) of a still lands on the plane at this depth."""
    w, h = layer_size(depth, aspect)
    iw, ih = image_size
    return ((px / iw - 0.5) * w, depth, (0.5 - py / ih) * h)


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
    pw, ph = layer_size(back, aspect)
    worst = 0.0
    for t, pos, lens, pitch, yaw in frames:
        dist = back - pos[1]
        half_w = dist * (SENSOR_MM / 2) / lens
        half_h = half_w / aspect
        cx = pos[0] - dist * math.tan(math.radians(yaw))  # positive yaw turns left
        cz = pos[2] + dist * math.tan(math.radians(pitch))
        over = max(abs(cx) + half_w - pw / 2, abs(cz) + half_h - ph / 2)
        worst = max(worst, over)
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
    for i, layer in enumerate(spec["layers"]):
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
        for socket, speed in fog_sockets:
            socket.default_value = t * speed
            socket.keyframe_insert("default_value", frame=f)
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
