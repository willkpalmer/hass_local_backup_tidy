"""Generate a skeuomorphic icon combining an ESPHome-style chip with a
classic backup floppy disk, rendered procedurally with Pillow at high
resolution then downsampled for anti-aliasing.
"""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024  # working canvas size (supersampled)


def lerp(a, b, t):
    return a + (b - a) * t


def linear_gradient_rgba(size, c1, c2, vertical=True):
    w, h = size
    n = h if vertical else w
    t = np.linspace(0, 1, n).reshape(-1, 1) if vertical else np.linspace(0, 1, n).reshape(1, -1)
    c1a = np.array(c1, dtype=np.float32)
    c2a = np.array(c2, dtype=np.float32)
    if vertical:
        grad = c1a[None, None, :] + (c2a - c1a)[None, None, :] * t[:, :, None]
        grad = np.repeat(grad, w, axis=1)
    else:
        grad = c1a[None, None, :] + (c2a - c1a)[None, None, :] * t[:, :, None]
        grad = np.repeat(grad, h, axis=0)
    return Image.fromarray(grad.astype(np.uint8), mode="RGBA")


def masked_layer(mask: Image.Image, fill_img: Image.Image) -> Image.Image:
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(fill_img, (0, 0), mask)
    return out


def rounded_mask(size, box, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle(box, radius=radius, fill=255)
    return m


def soft_shadow_from_mask(mask: Image.Image, offset=(0, 18), blur=22, opacity=130):
    shadow = Image.new("L", mask.size, 0)
    shadow.paste(mask, offset)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    arr = np.array(shadow).astype(np.float32) * (opacity / 255.0)
    shadow = Image.fromarray(arr.astype(np.uint8), mode="L")
    rgba = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    black = Image.new("RGBA", mask.size, (0, 0, 0, 255))
    rgba.paste(black, (0, 0), shadow)
    return rgba


def radial_glow(size, center, radius, color, max_alpha):
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2)
    a = np.clip(1 - d / radius, 0, 1) ** 1.6
    a = (a * max_alpha).astype(np.uint8)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    rgba[..., 3] = a
    return Image.fromarray(rgba, "RGBA")


def rotate_layer(layer: Image.Image, angle: float, center=None):
    return layer.rotate(angle, resample=Image.BICUBIC, center=center, expand=False)


def build_chip(canvas_size):
    chip_box = (150, 150, 760, 760)
    cx0, cy0, cx1, cy1 = chip_box
    cw, ch = cx1 - cx0, cy1 - cy0
    radius = 90

    mask_full = Image.new("L", canvas_size, 0)
    d = ImageDraw.Draw(mask_full)
    d.rounded_rectangle(chip_box, radius=radius, fill=255)

    shadow = soft_shadow_from_mask(mask_full, offset=(10, 30), blur=26, opacity=140)

    body_grad = linear_gradient_rgba(canvas_size, (232, 236, 241, 255), (150, 160, 174, 255), vertical=True)
    body = masked_layer(mask_full, body_grad)

    inset = 46
    die_box = (cx0 + inset, cy0 + inset, cx1 - inset, cy1 - inset)
    die_mask = Image.new("L", canvas_size, 0)
    dd = ImageDraw.Draw(die_mask)
    dd.rounded_rectangle(die_box, radius=44, fill=255)
    die_grad = linear_gradient_rgba(canvas_size, (18, 32, 54, 255), (10, 18, 30, 255), vertical=True)
    die = masked_layer(die_mask, die_grad)

    die_inner_shadow = Image.new("L", canvas_size, 0)
    did = ImageDraw.Draw(die_inner_shadow)
    did.rounded_rectangle(die_box, radius=44, outline=255, width=18)
    die_inner_shadow = die_inner_shadow.filter(ImageFilter.GaussianBlur(10))
    inner_shade = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    black = Image.new("RGBA", canvas_size, (0, 0, 0, 255))
    inner_shade.paste(black, (0, 0), die_inner_shadow)
    r, g, b, a = inner_shade.split()
    a = a.point(lambda v: int(v * 0.35))
    inner_shade = Image.merge("RGBA", (r, g, b, a))

    trace_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    td = ImageDraw.Draw(trace_layer)
    glow_color = (72, 190, 255, 255)
    dx0, dy0, dx1, dy1 = die_box
    dcx, dcy = (dx0 + dx1) / 2, (dy0 + dy1) / 2
    node_r = 10
    ring_r = (dx1 - dx0) * 0.30
    n_nodes = 6
    pts = []
    for i in range(n_nodes):
        ang = math.pi * 2 * i / n_nodes - math.pi / 2
        px = dcx + ring_r * math.cos(ang)
        py = dcy + ring_r * math.sin(ang)
        pts.append((px, py))
    for (px, py) in pts:
        td.line([(dcx, dcy), (px, py)], fill=glow_color, width=7)
    for (px, py) in pts:
        td.ellipse([px - node_r, py - node_r, px + node_r, py + node_r], fill=glow_color)
    td.ellipse([dcx - 16, dcy - 16, dcx + 16, dcy + 16], fill=(255, 255, 255, 255))
    glow_blur = trace_layer.filter(ImageFilter.GaussianBlur(9))
    r, g, b, a = glow_blur.split()
    a = a.point(lambda v: int(v * 0.9))
    glow_soft = Image.merge("RGBA", (r, g, b, a))
    trace_final = Image.alpha_composite(glow_soft, trace_layer)
    trace_final = masked_layer(die_mask, trace_final)

    pins = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(pins)
    pin_grad_img = linear_gradient_rgba(canvas_size, (210, 216, 224, 255), (120, 128, 138, 255), vertical=True)
    n_pins = 6
    pin_len = 34
    pin_w = 26
    pin_gap = 8
    span = ch - 120
    start = cy0 + 60
    step = span / (n_pins - 1)
    pin_mask = Image.new("L", canvas_size, 0)
    pmd = ImageDraw.Draw(pin_mask)
    for i in range(n_pins):
        y = start + step * i
        pmd.rounded_rectangle([cx0 - pin_len, y - pin_w / 2, cx0, y + pin_w / 2], radius=6, fill=255)
        pmd.rounded_rectangle([cx1, y - pin_w / 2, cx1 + pin_len, y + pin_w / 2], radius=6, fill=255)
    span2 = cw - 120
    start2 = cx0 + 60
    step2 = span2 / (n_pins - 1)
    for i in range(n_pins):
        x = start2 + step2 * i
        pmd.rounded_rectangle([x - pin_w / 2, cy0 - pin_len, x + pin_w / 2, cy0], radius=6, fill=255)
        pmd.rounded_rectangle([x - pin_w / 2, cy1, x + pin_w / 2, cy1 + pin_len], radius=6, fill=255)
    pins = masked_layer(pin_mask, pin_grad_img)
    pins_shadow = soft_shadow_from_mask(pin_mask, offset=(0, 6), blur=8, opacity=90)

    gloss = radial_glow(canvas_size, (cx0 + cw * 0.32, cy0 + ch * 0.18), cw * 0.62, (255, 255, 255), 130)
    gloss = masked_layer(mask_full, gloss)

    notch = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    nd = ImageDraw.Draw(notch)
    nx, ny = cx0 + 60, cy0 + 60
    nd.ellipse([nx - 14, ny - 14, nx + 14, ny + 14], fill=(90, 98, 108, 255))
    nd.ellipse([nx - 14, ny - 14, nx + 6, ny + 6], fill=(200, 206, 214, 255))

    layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    for l in (pins_shadow, shadow, pins, body, die, inner_shade, trace_final, gloss, notch):
        layer = Image.alpha_composite(layer, l)
    return layer


def build_floppy(canvas_size):
    layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    fx0, fy0, fx1, fy1 = 560, 560, 960, 960
    cut = 60

    body_mask = Image.new("L", canvas_size, 0)
    bd = ImageDraw.Draw(body_mask)
    bd.polygon(
        [
            (fx0 + 24, fy0),
            (fx1 - cut, fy0),
            (fx1, fy0 + cut),
            (fx1, fy1 - 24),
            (fx1 - 24, fy1),
            (fx0 + 24, fy1),
            (fx0, fy1 - 24),
            (fx0, fy0 + 24),
        ],
        fill=255,
    )
    bd.rounded_rectangle([fx0, fy0, fx1, fy1], radius=26, fill=255)

    shadow = soft_shadow_from_mask(body_mask, offset=(14, 26), blur=24, opacity=150)

    body_grad = linear_gradient_rgba(canvas_size, (58, 78, 110, 255), (22, 32, 48, 255), vertical=True)
    body = masked_layer(body_mask, body_grad)

    fw, fh = fx1 - fx0, fy1 - fy0
    shx0, shy0 = fx0 + fw * 0.16, fy0 + fh * 0.08
    shx1, shy1 = fx0 + fw * 0.84, fy0 + fh * 0.5
    shutter_mask = Image.new("L", canvas_size, 0)
    sd = ImageDraw.Draw(shutter_mask)
    sd.rounded_rectangle([shx0, shy0, shx1, shy1], radius=10, fill=255)
    shutter_grad = linear_gradient_rgba(canvas_size, (224, 229, 235, 255), (150, 158, 168, 255), vertical=True)
    shutter = masked_layer(shutter_mask, shutter_grad)

    hole_w, hole_h = fw * 0.16, fh * 0.14
    hx0 = shx1 - hole_w - fw * 0.06
    hy0 = shy0 + (shy1 - shy0 - hole_h) / 2
    hole_mask = Image.new("L", canvas_size, 0)
    hd = ImageDraw.Draw(hole_mask)
    hd.rectangle([hx0, hy0, hx0 + hole_w, hy0 + hole_h], fill=255)
    hole_grad = linear_gradient_rgba(canvas_size, (40, 46, 54, 255), (70, 78, 88, 255), vertical=True)
    hole = masked_layer(hole_mask, hole_grad)

    label_x0, label_y0 = fx0 + fw * 0.14, fy0 + fh * 0.58
    label_x1, label_y1 = fx1 - fw * 0.14, fy1 - fh * 0.12
    label_mask = Image.new("L", canvas_size, 0)
    ld = ImageDraw.Draw(label_mask)
    ld.rounded_rectangle([label_x0, label_y0, label_x1, label_y1], radius=8, fill=255)
    label_grad = linear_gradient_rgba(canvas_size, (250, 250, 248, 255), (222, 224, 222, 255), vertical=True)
    label = masked_layer(label_mask, label_grad)

    lines = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    lnd = ImageDraw.Draw(lines)
    ly = label_y0 + (label_y1 - label_y0) * 0.35
    lnd.line([(label_x0 + 14, ly), (label_x1 - 14, ly)], fill=(150, 155, 160, 255), width=5)
    ly2 = label_y0 + (label_y1 - label_y0) * 0.62
    lnd.line([(label_x0 + 14, ly2), (label_x1 - 40, ly2)], fill=(150, 155, 160, 255), width=5)

    gloss = radial_glow(canvas_size, (shx0 + (shx1 - shx0) * 0.3, shy0 + (shy1 - shy0) * 0.25), (shx1 - shx0) * 0.7, (255, 255, 255), 150)
    gloss = masked_layer(shutter_mask, gloss)

    body_gloss = radial_glow(canvas_size, (fx0 + fw * 0.28, fy0 + fh * 0.15), fw * 0.55, (255, 255, 255), 55)
    body_gloss = masked_layer(body_mask, body_gloss)

    for l in (shadow, body, body_gloss, shutter, gloss, hole, label, lines):
        layer = Image.alpha_composite(layer, l)

    return layer, body_mask


def compose():
    canvas_size = (S, S)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    chip = build_chip(canvas_size)
    canvas = Image.alpha_composite(canvas, chip)

    floppy, floppy_mask = build_floppy(canvas_size)
    angle = -10
    center = (760, 760)
    floppy = rotate_layer(floppy, angle, center=center)
    canvas = Image.alpha_composite(canvas, floppy)

    return canvas


def main():
    img = compose()
    bbox = img.getbbox()
    if bbox:
        pad = 24
        l, t, r, b = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        r = min(img.width, r + pad)
        b = min(img.height, b + pad)
        side = max(r - l, b - t)
        cx, cy = (l + r) / 2, (t + b) / 2
        l = int(cx - side / 2)
        t = int(cy - side / 2)
        img = img.crop((l, t, l + side, t + side))

    out_512 = img.resize((512, 512), Image.LANCZOS)
    out_256 = img.resize((256, 256), Image.LANCZOS)

    brand_dir = "../custom_components/local_backup_tidy/brand"
    os.makedirs(brand_dir, exist_ok=True)
    for path in ("../icon.png", f"{brand_dir}/icon.png"):
        out_256.save(path)
    for path in ("../icon@2x.png", f"{brand_dir}/icon@2x.png"):
        out_512.save(path)
    print("saved icon.png / icon@2x.png to repo root and custom_components/local_backup_tidy/brand/")


if __name__ == "__main__":
    main()
