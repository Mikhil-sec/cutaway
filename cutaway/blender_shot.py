"""Render one 2.5D shot in Blender from a shot spec (JSON).

Run headless:
    blender -b --factory-startup -P cutaway/blender_shot.py -- shot.json out_dir

Each layer is an unlit, alpha-blended image plane placed at its depth and sized
so that, from the camera's start position, every layer lines up exactly with
the original still. Moving the camera then gives true parallax between layers.
"""
import json
import math
import sys
from pathlib import Path

import bpy

SENSOR_MM = 36.0
FOCAL_MM = 35.0
OVERSCAN = 1.12  # same factor on every layer, so alignment holds and edges stay hidden


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:]
    # Absolute paths: Blender resolves relative ones against its own directory, not the shell's.
    return json.loads(Path(argv[0]).resolve().read_text()), Path(argv[1]).resolve()


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def set_engine(scene):
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            return
        except TypeError:
            continue


def image_material(name, path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    else:
        mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path))
    tex.extension = "EXTEND"
    emit = nt.nodes.new("ShaderNodeEmission")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(emit.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat, tex.image


def add_layer(i, layer, aspect):
    depth = float(layer["depth"])
    width = depth * SENSOR_MM / FOCAL_MM * OVERSCAN
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, depth, 0), rotation=(math.pi / 2, 0, 0))
    plane = bpy.context.active_object
    plane.name = f"layer_{i}"
    plane.scale = (width / 2, width / aspect / 2, 1)
    mat, _ = image_material(f"mat_{i}", layer["image"])
    plane.data.materials.append(mat)
    return plane


def main():
    spec, out_dir = parse_args()
    scene = reset_scene()
    set_engine(scene)
    w, h = spec["resolution"]
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.fps = spec["fps"]
    scene.frame_start, scene.frame_end = 1, int(spec["fps"] * spec["seconds"])
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"  # keep the painting's colours as painted
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out_dir / "frame_")

    world = bpy.data.worlds.new("world")
    world.color = (0, 0, 0)
    scene.world = world

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = FOCAL_MM
    cam_data.sensor_width = SENSOR_MM
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.rotation_euler = (math.pi / 2, 0, 0)  # look along +Y

    aspect = w / h
    focus = None
    for i, layer in enumerate(spec["layers"]):
        plane = add_layer(i, layer, aspect)
        if layer.get("focus"):
            focus = plane

    c = spec["camera"]
    if focus is not None:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_object = focus
        cam_data.dof.aperture_fstop = c.get("fstop", 4.0)

    for frame, loc in ((scene.frame_start, c["from"]), (scene.frame_end, c["to"])):
        cam.location = loc
        cam.keyframe_insert("location", frame=frame)

    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(animation=True)


main()
