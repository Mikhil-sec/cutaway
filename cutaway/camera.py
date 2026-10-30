"""Camera vocabulary and frame geometry, shared by the director and the Blender renderer.

Muse Spark chooses a named move with an intensity; this module turns it into
exact camera keyframes, then shrinks the move until the camera never sees past
the edge of the background painting. Pure Python: Blender imports it too.
"""
import math

SENSOR_MM = 36.0
REF_LENS_MM = 35.0
OVERSCAN = 1.25  # every layer is this much larger than the reference frame; set per shot with use_overscan()


def use_overscan(value):
    """Set the margin for the shot being built: more margin = more room to move, but the reference
    frame crops more of the painting's edges (a character near an edge needs less)."""
    global OVERSCAN
    OVERSCAN = value

MOVES = ["push_in", "pull_out", "truck_left", "truck_right", "crane_up", "crane_down",
         "drift", "dolly_zoom", "orbit_left", "orbit_right"]
INTENSITY = {"subtle": 0.45, "medium": 0.75, "strong": 1.0}


def layer_size(depth, aspect):
    width = depth * SENSOR_MM / REF_LENS_MM * OVERSCAN
    return width, width / aspect


def pixel_to_world(px, py, depth, image_size, aspect):
    """Where pixel (px, py) of a still lands on the plane at this depth."""
    w, h = layer_size(depth, aspect)
    iw, ih = image_size
    return ((px / iw - 0.5) * w, depth, (0.5 - py / ih) * h)


def edge_overshoot(back_depth, aspect, pos, lens, pitch=0.0, yaw=0.0):
    """How far (scene units) the view at this camera pose extends past the background plate; <= 0 is safe."""
    pw, ph = layer_size(back_depth, aspect)
    dist = back_depth - pos[1]
    half_w = dist * (SENSOR_MM / 2) / lens
    half_h = half_w / aspect
    cx = pos[0] - dist * math.tan(math.radians(yaw))  # positive yaw turns left
    cz = pos[2] + dist * math.tan(math.radians(pitch))
    return max(abs(cx) + half_w - pw / 2, abs(cz) + half_h - ph / 2)


def move_keys(move, intensity, seconds, subject_xz=(0.0, 0.0), subject_depth=12.0,
              focus_from="subject", focus_to="subject"):
    """Camera keys for a named move. subject_xz is the subject's world position on its plane."""
    k = INTENSITY[intensity]
    sx, sz = subject_xz
    push = 0.28 * subject_depth * k  # travel toward the subject, as a share of its distance
    lean = 0.18 * k  # how far the camera's path bends toward the subject sideways
    lens0 = REF_LENS_MM
    a, b = {"pos": [0.0, 0.0, 0.0], "lens": lens0}, {"pos": [0.0, 0.0, 0.0], "lens": lens0}
    if move == "push_in":
        b = {"pos": [sx * lean, push, sz * lean], "lens": lens0 + 6 * k}
    elif move == "pull_out":
        a = {"pos": [sx * lean, push, sz * lean], "lens": lens0 + 6 * k}
    elif move in ("truck_left", "truck_right"):
        s = 1.6 * k * (-1 if move == "truck_left" else 1)
        a = {"pos": [-s / 2, push * 0.3, 0.0], "lens": lens0 + 3}
        b = {"pos": [s / 2, push * 0.3, 0.0], "lens": lens0 + 3}
    elif move in ("crane_up", "crane_down"):
        s = 1.2 * k * (1 if move == "crane_up" else -1)
        a = {"pos": [0.0, push * 0.2, -s / 2], "lens": lens0 + 2, "pitch": 2.5 * k * (1 if s > 0 else -1)}
        b = {"pos": [sx * lean, push * 0.6, s / 2], "lens": lens0 + 4, "pitch": -1.0 * k * (1 if s > 0 else -1)}
    elif move == "drift":
        a = {"pos": [-0.25 * k, 0.0, 0.0], "lens": lens0 + 1}
        b = {"pos": [0.25 * k, push * 0.25, 0.05], "lens": lens0 + 2}
    elif move == "dolly_zoom":
        # Move in while widening, so the subject keeps its size and the background stretches.
        travel = push * 1.3
        a = {"pos": [0.0, 0.0, 0.0], "lens": lens0 + 14 * k}
        lens_b = (lens0 + 14 * k) * (subject_depth - travel) / subject_depth
        b = {"pos": [sx * lean * 0.5, travel, 0.0], "lens": max(lens_b, lens0)}
    elif move in ("orbit_left", "orbit_right"):
        s = (-1 if move == "orbit_left" else 1) * 1.4 * k
        a = {"pos": [-s / 2, push * 0.4, 0.0], "lens": lens0 + 5, "yaw": s * 1.6}
        b = {"pos": [s / 2, push * 0.4, 0.0], "lens": lens0 + 5, "yaw": -s * 1.6}
    else:
        raise ValueError(f"unknown move {move}")
    a.update(t=0.0, focus=focus_from)
    b.update(t=seconds, focus=focus_to)
    return [a, b]


def subject_cut(box, depth, aspect, pos, lens, pitch=0.0, yaw=0.0, margin=0.12):
    """How far (as a share of the frame) the subject's box sticks out of the view; <= 0 means fully in frame.

    box: (x0, z0, x1, z1) in world units on the subject's plane at `depth`.
    """
    dist = depth - pos[1]
    if dist <= 0.5:
        return 1.0
    half_w = dist * (SENSOR_MM / 2) / lens
    half_h = half_w / aspect
    cx = pos[0] - dist * math.tan(math.radians(yaw))
    cz = pos[2] + dist * math.tan(math.radians(pitch))
    x0, z0, x1, z1 = box
    lim_w, lim_h = half_w * (1 - margin), half_h * (1 - margin)
    return max((cx - lim_w - x0) / half_w, (x1 - cx - lim_w) / half_w,
               (cz - lim_h - z0) / half_h, (z1 - cz - lim_h) / half_h)


def _poses(keys, steps):
    for k0, k1 in zip(keys, keys[1:]):
        for i in range(steps + 1):
            u = i / steps
            yield ([p0 + (p1 - p0) * u for p0, p1 in zip(k0["pos"], k1["pos"])],
                   k0["lens"] + (k1["lens"] - k0["lens"]) * u,
                   k0.get("pitch", 0) + (k1.get("pitch", 0) - k0.get("pitch", 0)) * u,
                   k0.get("yaw", 0) + (k1.get("yaw", 0) - k0.get("yaw", 0)) * u)


def fit_keys(keys, back_depth, aspect, subject=None, edge_depths=(), steps=48):
    """Adjust a move until (1) the camera never sees past the background plate, nor past any layer in
    `edge_depths` (layers whose content reaches the frame border, like foreground plants or a road),
    and (2) the subject, if given as (box, depth), stays wholly in frame.

    Tries the full move first, then shifts the whole path toward the subject and pulls it back,
    then scales the move down; if the subject can't be framed without showing an edge, clean edges
    win. Returns (keys, scale applied, whether the subject stays framed).
    """
    depths = [back_depth, *edge_depths]
    def variant(s, shift, back):
        out = []
        for key in keys:
            k2 = dict(key)
            k2["pos"] = [key["pos"][0] * s + shift[0], key["pos"][1] * s - back, key["pos"][2] * s + shift[1]]
            k2["lens"] = REF_LENS_MM + (key.get("lens", REF_LENS_MM) - REF_LENS_MM) * s
            for ang in ("pitch", "yaw", "roll"):
                if ang in key:
                    k2[ang] = key[ang] * s
            out.append(k2)
        return out

    margin = subject[2] if subject and len(subject) > 2 else 0.12

    def ok(cand, framing=True):
        for pos, lens, pitch, yaw in _poses(cand, steps):
            if any(edge_overshoot(d, aspect, pos, lens, pitch, yaw) > -0.05 * d / 40 for d in depths):
                return False
            if framing and subject and subject_cut(subject[0], subject[1], aspect, pos, lens, pitch, yaw,
                                                   margin) > 0:
                return False
        return True

    centre = (0.0, 0.0)
    if subject:
        (x0, z0, x1, z1), d = subject[:2]
        # Shifting the camera by c moves the view at the subject's depth by c: aim part-way at the subject.
        centre = ((x0 + x1) / 2, (z0 + z1) / 2)
    for framing in (True, False):
        s = 1.0
        while s > 0.05:
            for frac in (0.0, 0.35, 0.7):
                for back in (0.0, 1.0, 2.0, 3.5, 5.0, 7.0):
                    cand = variant(s, (centre[0] * frac, centre[1] * frac), back)
                    if ok(cand, framing):
                        return cand, s, framing or not subject
            s *= 0.85
    return variant(0.0, (0.0, 0.0), 0.0), 0.0, False
