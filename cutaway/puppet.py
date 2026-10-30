"""Characters as bendable puppets: weight maps, pivots and motion presets.

A character is one image on a subdivided mesh. The weight map says how much
each vertex follows the head (1 at the head, fading through the neck to 0 in
the body), so a head turn bends the neck instead of hinging at a seam.
Motion presets use overshoot and settle, so gestures don't move like hinges.
"""
import random

import numpy as np
from PIL import Image, ImageFilter

GRID = (193, 109)  # vertices across, up: 192 x 108 quads over the full frame


def build(char_mask, head_mask, weights_path, blur_px=24):
    """Write the weight grid (.npy, rows bottom-to-top) and return pivots in image pixels.

    char_mask, head_mask: full-frame boolean arrays for the character and its head.
    """
    h, w = char_mask.shape
    head = Image.fromarray((head_mask & char_mask).astype(np.uint8) * 255)
    soft = np.asarray(head.filter(ImageFilter.GaussianBlur(blur_px)), dtype=np.float32) / 255
    if soft.max() > 0:
        soft = np.clip(soft / soft.max() * 1.6, 0, 1)  # fully rigid head, falloff only through the neck
    grid = np.asarray(Image.fromarray((soft * 255).astype(np.uint8)).resize(GRID, Image.BILINEAR),
                      dtype=np.float32) / 255
    np.save(weights_path, np.flipud(grid))

    # Neck: where the head meets the body. Feet: the lowest point of the character.
    rows = np.where(char_mask.any(axis=1))[0]
    near_head = np.asarray(head.filter(ImageFilter.MaxFilter(9))) > 127
    seam = near_head & char_mask & ~head_mask
    if seam.any():
        ys, xs = np.nonzero(seam)
        neck = [int(xs.mean()), int(ys.mean())]
    else:  # no head found: a nominal pivot near the top; the weights are all zero anyway
        top = int(rows.min())
        neck = [int(np.where(char_mask[top])[0].mean()), top]
    feet_y = int(rows.max())
    feet = [int(np.where(char_mask[feet_y])[0].mean()), feet_y]
    return {"neck": neck, "feet": feet}


def _gesture(t0, target, rise=0.35, overshoot=0.18, settle=0.3):
    """Keys for one head move to `target` degrees starting at t0: rise, overshoot, settle."""
    return [[t0, None], [t0 + rise, target * (1 + overshoot)], [t0 + rise + settle, target]]


def motion(action, seconds, seed=0, facing=1):
    """Animation keys for a puppet. facing=+1 if the character faces right, -1 if left.

    Bend angles are counter-clockwise; a character facing left lowers its head
    with a counter-clockwise bend.
    """
    rnd = random.Random(seed)
    down = 1 if facing < 0 else -1  # sign of a bend that lowers the beak
    anim = {"breathe": {"amp": 0.8, "period": rnd.uniform(2.4, 3.2), "phase": rnd.uniform(0, 6.3)}}
    keys = [[0.0, 0.0]]

    def add(gesture):
        start = gesture[0][0]
        prev = keys[-1][1]
        keys.append([start, prev])
        keys.extend(gesture[1:])

    if action == "idle":
        t = rnd.uniform(0.8, 1.5)
        while t < seconds - 1.0:
            add(_gesture(t, rnd.uniform(-2.0, 2.0), rise=0.6, overshoot=0.1, settle=0.5))
            t += rnd.uniform(1.6, 2.6)
    elif action == "look_around":
        t = 0.6
        for target in (6 * down, -5 * down, 2.5 * down):
            if t > seconds - 0.8:
                break
            add(_gesture(t, target))
            t += rnd.uniform(1.1, 1.6)
    elif action == "head_tilt":
        add(_gesture(min(1.0, seconds * 0.25), 8 * down, rise=0.4))
        if seconds > 3.5:
            add(_gesture(seconds * 0.65, 3 * down, rise=0.5))
    elif action == "look_down":
        add(_gesture(min(0.8, seconds * 0.2), 10 * down, rise=0.6, overshoot=0.08, settle=0.5))
    elif action == "look_up":
        add(_gesture(min(0.8, seconds * 0.2), -9 * down, rise=0.5))
    elif action == "startle":
        t = min(0.7, seconds * 0.2)
        add(_gesture(t, -12 * down, rise=0.1, overshoot=0.4, settle=0.3))
        # A quick crouch, a jump and a landing that settles: big enough to read at film speed.
        anim["hop"] = [[0.0, 0.0], [t - 0.12, 0.0], [t - 0.04, -0.06], [t + 0.12, 0.45], [t + 0.3, 0.0],
                       [t + 0.38, -0.04], [t + 0.5, 0.0]]
        if seconds > 2.5:
            add(_gesture(t + 1.0, 2 * down, rise=0.5))
    else:
        raise ValueError(f"unknown action {action}")
    anim["bend"] = keys
    return anim


ACTIONS = ["idle", "look_around", "head_tilt", "look_down", "look_up", "startle"]


def facing_from_mask(char_mask, head_mask):
    """+1 if the head is right of the body's centre (facing right), else -1."""
    cx = np.nonzero(char_mask)[1].mean()
    hx = np.nonzero(head_mask & char_mask)[1].mean() if (head_mask & char_mask).any() else cx
    return 1 if hx > cx else -1
