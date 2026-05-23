#!/usr/bin/env python3
"""
OpenBook 2 Cover Generator — Field Cartography aesthetic
Sister piece to OpenBook 1's Neural Cartography.
Center: FDE. Equation: OUTCOME = HARNESS x CUSTOMER. 8 orbital stages.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

W, H = 1600, 2240
FONTS_DIR = os.path.expanduser("~/.claude/skills/canvas-design/canvas-fonts")

# === COLOR PALETTE — strict 3-color discipline (matches OpenBook 1) ===
BG       = (245, 245, 248)
CYAN     = (0, 140, 180)     # machine / harness
ORANGE   = (220, 90, 30)     # customer / boundary / urgency
DIM      = (200, 205, 215)
MUTED    = (120, 130, 150)
TEXT     = (25, 30, 40)
FAINT    = (230, 232, 238)


def alpha_color(base, alpha):
    return (*base, alpha)


def load_font(name, size):
    path = os.path.join(FONTS_DIR, name)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# === LOAD FONTS (matched to OpenBook 1) ===
font_title_large  = load_font("BigShoulders-Bold.ttf", 148)
font_title_sub    = load_font("Tektur-Medium.ttf", 54)
font_equation     = load_font("JetBrainsMono-Bold.ttf", 36)
font_label        = load_font("JetBrainsMono-Regular.ttf", 17)
font_label_bold   = load_font("JetBrainsMono-Bold.ttf", 17)
font_small        = load_font("GeistMono-Regular.ttf", 13)
font_tiny         = load_font("GeistMono-Regular.ttf", 11)
font_tag          = load_font("GeistMono-Regular.ttf", 14)
font_meta         = load_font("DMMono-Regular.ttf", 15)
font_badge        = load_font("GeistMono-Bold.ttf", 13)

# CJK font discovery
CJK_FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]

font_cjk_large = None
font_cjk_medium = None
font_cjk_small = None

for p in CJK_FONT_PATHS:
    if os.path.exists(p):
        font_cjk_large = ImageFont.truetype(p, 68)
        font_cjk_medium = ImageFont.truetype(p, 28)
        font_cjk_small = ImageFont.truetype(p, 22)
        break

if font_cjk_large is None:
    import subprocess
    try:
        result = subprocess.run(['fc-list', ':lang=zh', 'file'], capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                fp = line.split(':')[0].strip()
                if os.path.exists(fp):
                    font_cjk_large = ImageFont.truetype(fp, 68)
                    font_cjk_medium = ImageFont.truetype(fp, 28)
                    font_cjk_small = ImageFont.truetype(fp, 22)
                    break
    except:
        pass

if font_cjk_large is None:
    font_cjk_large = font_title_sub
    font_cjk_medium = font_label
    font_cjk_small = font_small


# === CREATE IMAGE ===
img = Image.new('RGBA', (W, H), BG + (255,))
draw = ImageDraw.Draw(img, 'RGBA')

# === Radial vignette ===
vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
vdraw = ImageDraw.Draw(vignette, 'RGBA')
cx, cy = W // 2, H // 2 - 60
for r in range(max(W, H), 0, -2):
    alpha = max(0, min(255, int(100 * (r / max(W, H)) ** 2.0)))
    vdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 222, 230, alpha))
img = Image.alpha_composite(img, vignette)
draw = ImageDraw.Draw(img, 'RGBA')

# === CIRCUIT TRACES — sparse, precise (kept identical to OpenBook 1 for series identity) ===
traces = [
    ((0, 340), (350, 340)),
    ((420, 340), (580, 340)),
    ((0, 1860), (280, 1860)),
    ((1320, 1860), (1600, 1860)),
    ((350, 340), (350, 480)),
    ((1400, 600), (1400, 820)),
    ((200, 1700), (200, 1860)),
]
for (x1, y1), (x2, y2) in traces:
    draw.line([(x1, y1), (x2, y2)], fill=alpha_color(CYAN, 50), width=1)

trace_nodes = [(350, 340), (350, 480), (580, 340), (1400, 600), (1400, 820), (200, 1700), (280, 1860)]
for nx, ny in trace_nodes:
    draw.ellipse([nx-4, ny-4, nx+4, ny+4], outline=alpha_color(CYAN, 70), width=1)
    draw.ellipse([nx-2, ny-2, nx+2, ny+2], fill=alpha_color(CYAN, 50))


# === CENTRAL FDE GRAVITY WELL ===
center_x, center_y = W // 2, H // 2 - 40

# Concentric rings — 4 layers, no labels (orbital node labels carry semantics)
rings = [
    (420, CYAN,   30, False),
    (360, ORANGE, 40, True),
    (300, CYAN,   50, False),
    (240, ORANGE, 35, True),
]

for radius, color, alpha, dashed in rings:
    if dashed:
        segments = 72
        for i in range(segments):
            if i % 2 == 0:
                a1 = (2 * math.pi * i) / segments
                a2 = (2 * math.pi * (i + 1)) / segments
                x1 = center_x + radius * math.cos(a1)
                y1 = center_y + radius * math.sin(a1)
                x2 = center_x + radius * math.cos(a2)
                y2 = center_y + radius * math.sin(a2)
                draw.line([(x1, y1), (x2, y2)], fill=alpha_color(color, alpha), width=1)
    else:
        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            outline=alpha_color(color, alpha), width=1
        )

# === 8 ORBITAL NODES — the FDE work cycle ===
connectors = [
    (0,    "DISCOVERY",    CYAN),
    (45,   "EVAL",         ORANGE),
    (90,   "SCAFFOLDING",  CYAN),
    (135,  "VPC / DATA",   ORANGE),
    (180,  "GUARDRAILS",   CYAN),
    (225,  "AGENT / MCP",  ORANGE),
    (270,  "HANDOFF",      CYAN),
    (315,  "PATTERNS",     ORANGE),
]

node_radius = 470
for angle_deg, label, color in connectors:
    angle = math.radians(angle_deg - 90)
    nx = center_x + node_radius * math.cos(angle)
    ny = center_y + node_radius * math.sin(angle)

    draw.ellipse([nx-6, ny-6, nx+6, ny+6], outline=alpha_color(color, 180), width=2)
    draw.ellipse([nx-3, ny-3, nx+3, ny+3], fill=alpha_color(color, 220))

    inner_r = 240
    ix = center_x + inner_r * math.cos(angle)
    iy = center_y + inner_r * math.sin(angle)
    draw.line([(ix, iy), (nx, ny)], fill=alpha_color(color, 18), width=1)

    bbox = draw.textbbox((0, 0), label, font=font_label)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    if angle_deg == 0:
        lx = nx - tw // 2
        ly = ny - th - 18
    elif angle_deg == 180:
        lx = nx - tw // 2
        ly = ny + 18
    elif angle_deg == 45:
        lx = nx + 16
        ly = ny - th - 8
    elif angle_deg == 135:
        lx = nx + 16
        ly = ny + 8
    elif angle_deg == 225:
        lx = nx - tw - 16
        ly = ny + 8
    elif angle_deg == 315:
        lx = nx - tw - 16
        ly = ny - th - 8
    elif angle_deg < 180:
        lx = nx + 16
        ly = ny - th // 2
    else:
        lx = nx - tw - 16
        ly = ny - th // 2

    draw.text((lx, ly), label, fill=alpha_color(color, 220), font=font_label)


# === CENTRAL CORE: "FDE" (instead of OpenBook 1's "LLM") ===
core_r = 120

for gr in range(160, core_r, -5):
    alpha = max(0, int(3 * (1 - (gr - core_r) / (160 - core_r))))
    draw.ellipse(
        [center_x - gr, center_y - gr, center_x + gr, center_y + gr],
        outline=alpha_color(CYAN, alpha), width=1
    )

draw.ellipse(
    [center_x - core_r, center_y - core_r, center_x + core_r, center_y + core_r],
    outline=alpha_color(CYAN, 180), width=2
)

for ir, a in [(110, 40), (90, 30), (65, 22), (40, 16)]:
    draw.ellipse(
        [center_x - ir, center_y - ir, center_x + ir, center_y + ir],
        outline=alpha_color(CYAN, a), width=1
    )

ch = 20
draw.line([(center_x - ch, center_y), (center_x + ch, center_y)], fill=alpha_color(CYAN, 30), width=1)
draw.line([(center_x, center_y - ch), (center_x, center_y + ch)], fill=alpha_color(CYAN, 30), width=1)

draw.ellipse([center_x-3, center_y-3, center_x+3, center_y+3], fill=alpha_color(CYAN, 50))

# "FDE" in the center — use larger title font for visual weight
font_fde_core = load_font("BigShoulders-Bold.ttf", 84)
fde_text = "FDE"
bbox = draw.textbbox((0, 0), fde_text, font=font_fde_core)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
draw.text(
    (center_x - tw // 2, center_y - th // 2 - 14),
    fde_text, fill=(*CYAN, 255), font=font_fde_core
)

sub = "forward deployed engineer"
bbox = draw.textbbox((0, 0), sub, font=font_small)
tw = bbox[2] - bbox[0]
draw.text(
    (center_x - tw // 2, center_y + 22),
    sub, fill=alpha_color(MUTED, 160), font=font_small
)


# === TOP SECTION ===

# Series badge — distinguishes from OpenBook 1's "TECHNICAL DEEP DIVE"
badge_text = "OPENBOOK · VOL II"
badge_x, badge_y = 100, 100
bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
pad_x, pad_y = 18, 10
draw.rectangle(
    [badge_x, badge_y, badge_x + bw + pad_x * 2, badge_y + bh + pad_y * 2],
    outline=alpha_color(ORANGE, 80), width=1
)
draw.text(
    (badge_x + pad_x, badge_y + pad_y),
    badge_text, fill=alpha_color(ORANGE, 180), font=font_badge
)

# Main title
title_y = 180
draw.text((96, title_y), "OPENBOOK", fill=alpha_color(TEXT, 240), font=font_title_large)

# English subtitle
en_subtitle = "Forward Deployed Engineer"
draw.text((100, title_y + 156), en_subtitle, fill=alpha_color(MUTED, 220), font=font_title_sub)

# Chinese subtitle
cn_y = title_y + 240
cn_line1 = "AI 应用的"
cn_line2 = "落地工程学"

draw.text((100, cn_y), cn_line1, fill=alpha_color(TEXT, 200), font=font_cjk_large)

# "落地" in cyan accent — the keyword
fde_zh = "落地"
rest_zh = "工程学"

bbox_h = draw.textbbox((0, 0), fde_zh, font=font_cjk_large)
hw = bbox_h[2] - bbox_h[0]
draw.text((100, cn_y + 80), fde_zh, fill=alpha_color(CYAN, 240), font=font_cjk_large)
draw.text((100 + hw, cn_y + 80), rest_zh, fill=alpha_color(TEXT, 200), font=font_cjk_large)

# Underline beneath 落地
draw.rectangle([100, cn_y + 80 + 72, 100 + hw, cn_y + 80 + 75], fill=alpha_color(CYAN, 60))


# === EQUATION BAR: OUTCOME = HARNESS × CUSTOMER ===
eq_y = H - 520

draw.line([(0, eq_y), (W, eq_y)], fill=alpha_color(CYAN, 15), width=1)
draw.line([(0, eq_y + 70), (W, eq_y + 70)], fill=alpha_color(CYAN, 15), width=1)

eq_parts = [
    ("OUTCOME",  CYAN,   False),
    ("=",        MUTED,  False),
    ("HARNESS",  MUTED,  False),
    (chr(0x00D7), MUTED, False),  # ×
    ("CUSTOMER", ORANGE, True),
]

eq_widths = []
eq_total_w = 0
for text, _, _ in eq_parts:
    bbox = draw.textbbox((0, 0), text, font=font_equation)
    w = bbox[2] - bbox[0]
    eq_widths.append(w)
    eq_total_w += w

gap = 32
eq_total_w += gap * (len(eq_parts) - 1)
eq_start_x = (W - eq_total_w) // 2

pad = 12
for i, (text, color, highlight) in enumerate(eq_parts):
    bbox = draw.textbbox((0, 0), text, font=font_equation)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tx = eq_start_x
    ty = eq_y + 16

    if text in ["=", chr(0x00D7)]:
        draw.text((tx, ty), text, fill=alpha_color(color, 220), font=font_equation)
    else:
        box_alpha = 140 if not highlight else 200
        # Highlighted box: subtle tinted bg first, then border, then text on top
        if highlight:
            tint = Image.new('RGBA', (int(tw + pad * 2), int(th + pad * 1.5)), (255, 240, 230, 90))
            img.paste(tint, (int(tx - pad), int(ty - pad // 2)), tint)
            draw = ImageDraw.Draw(img, 'RGBA')
        draw.rectangle(
            [tx - pad, ty - pad//2, tx + tw + pad, ty + th + pad],
            outline=alpha_color(color, box_alpha), width=2
        )
        draw.text((tx, ty), text, fill=(*color, 255), font=font_equation)

    eq_start_x += tw + gap


# === BOTTOM SECTION ===

sub_y = H - 400
sub_line1 = "Harness 提供能力,客户提供约束"
sub_line2_a = "FDE"
sub_line2_b = " 把 Harness 装到客户身上"
sub_line3 = "这本书讲的就是怎么做这件事"

if font_cjk_medium:
    draw.text((100, sub_y), sub_line1, fill=(*TEXT, 255), font=font_cjk_medium)

    draw.text((100, sub_y + 44), sub_line2_a, fill=(*ORANGE, 255), font=font_meta)
    bbox = draw.textbbox((0, 0), sub_line2_a, font=font_meta)
    hw2 = bbox[2] - bbox[0]
    draw.text((100 + hw2, sub_y + 44), sub_line2_b, fill=(*TEXT, 220), font=font_cjk_small)

    draw.text((100, sub_y + 86), sub_line3, fill=(*MUTED, 255), font=font_cjk_small)


# === DIVIDER + TAGS ===
div_y = H - 280
draw.line([(100, div_y), (W - 100, div_y)], fill=alpha_color(MUTED, 60), width=1)

tags = ["DISCOVERY", "EVAL", "SCAFFOLDING", "VPC", "GUARDRAILS", "AGENT", "HANDOFF", "T-SHAPE"]
tag_x = 100
tag_y = div_y + 24

for tag in tags:
    bbox = draw.textbbox((0, 0), tag, font=font_tag)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_tx, pad_ty = 12, 7
    draw.rectangle(
        [tag_x, tag_y, tag_x + tw + pad_tx * 2, tag_y + th + pad_ty * 2],
        outline=alpha_color(CYAN, 120), width=1
    )
    draw.text((tag_x + pad_tx, tag_y + pad_ty), tag, fill=(*CYAN, 255), font=font_tag)

    tag_x += tw + pad_tx * 2 + 10
    if tag_x > W - 300:
        tag_x = 100
        tag_y += th + pad_ty * 2 + 10


# === META ===
meta_y = div_y + 90
meta_lines = [
    "17 chapters + 4 appendices",
    "7 parts · Field Engineering",
]
for i, line in enumerate(meta_lines):
    bbox = draw.textbbox((0, 0), line, font=font_meta)
    tw = bbox[2] - bbox[0]
    draw.text((W - 100 - tw, meta_y + i * 28), line, fill=(*MUTED, 255), font=font_meta)


# === CORNER MARKS ===
corner_size = 36
corner_alpha = 30
corners = [
    (44, 44, 44 + corner_size, 44, 44, 44 + corner_size),
    (W - 44, 44, W - 44 - corner_size, 44, W - 44, 44 + corner_size),
    (44, H - 44, 44 + corner_size, H - 44, 44, H - 44 - corner_size),
    (W - 44, H - 44, W - 44 - corner_size, H - 44, W - 44, H - 44 - corner_size),
]

for x, y, x2, y2, x3, y3 in corners:
    draw.line([(x2, y2), (x, y), (x3, y3)], fill=alpha_color(CYAN, corner_alpha), width=2)


# === SAVE ===
final = img.convert('RGB')
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover.png")
final.save(output_path, "PNG", quality=95)
print(f"Cover saved to {output_path}")
print(f"Size: {final.size}")
