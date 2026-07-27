#!/usr/bin/env python3
"""百家号封面图生成器 —— 无文字抽象封面，规避平台对封面文字/水印的降权。

用法:
    python3 make_cover.py <slug> [输出路径]

设计取向：阴郁、克制、不华丽（见记忆 feedback_visual_style_yinyu）。
以 slug 做种子，同一篇稿子重跑得到同一张图，不同稿子自动换配色与构图。
输出 1200x800（3:2），JPEG，质量 88 —— 百家号单图封面的安全规格。
"""
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 800

# 阴郁系配色：(背景暗色, 背景亮色, 线条色, 强调色)
PALETTES = [
    ((18, 24, 33), (43, 57, 74), (108, 128, 152), (176, 148, 106)),   # 石板蓝 + 暗金
    ((22, 22, 26), (56, 52, 58), (126, 118, 128), (150, 120, 112)),   # 炭灰 + 陶土
    ((16, 28, 28), (38, 62, 60), (100, 134, 128), (168, 156, 116)),   # 墨绿 + 苔黄
    ((24, 20, 30), (52, 44, 66), (120, 108, 140), (158, 140, 168)),   # 暗紫
    ((20, 26, 30), (46, 60, 68), (112, 132, 142), (170, 160, 140)),   # 铅灰蓝
]


def seed_of(slug: str) -> int:
    return int(hashlib.sha256(slug.encode("utf-8")).hexdigest()[:12], 16)


def vertical_gradient(top, bottom):
    img = Image.new("RGB", (1, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return img.resize((W, H), Image.BILINEAR)


def build(slug: str) -> Image.Image:
    s = seed_of(slug)
    dark, light, line, accent = PALETTES[s % len(PALETTES)]

    # 底：自上而下由亮到暗，暗部在下，视觉重心压低
    img = vertical_gradient(light, dark)

    # 弥散光斑，位置由种子决定
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx = 200 + (s >> 4) % (W - 400)
    cy = 120 + (s >> 9) % 320
    gd.ellipse([cx - 380, cy - 380, cx + 380, cy + 380], fill=tuple(min(255, c + 46) for c in light))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(190)), 0.42)

    d = ImageDraw.Draw(img, "RGBA")

    # 分层横线：呼应「按位阶分层」这类结构性内容，也让画面有秩序感
    n = 5 + (s >> 14) % 3
    base_y = int(H * 0.52)
    gap = (s >> 18) % 26 + 42
    for i in range(n):
        y = base_y + i * gap
        if y > H - 40:
            break
        inset = 120 + i * (60 + (s >> (20 + i)) % 40)
        alpha = 150 - i * 20
        d.line([(inset, y), (W - 110, y)], fill=(*line, max(alpha, 40)), width=2)

    # 一条强调短线，位置随种子浮动，打破规整
    ay = base_y - 58 - (s >> 24) % 40
    d.line([(120, ay), (120 + 210 + (s >> 26) % 160, ay)], fill=(*accent, 225), width=5)

    # 细竖线，做出栏目分隔的暗示
    vx = int(W * 0.74) + (s >> 28) % 60
    d.line([(vx, 90), (vx, H - 90)], fill=(*line, 70), width=1)

    # 极轻噪点，避免大面积色带
    noise = Image.effect_noise((W, H), 12).convert("L").point(lambda v: 128 + (v - 128) // 6)
    img = Image.composite(img, img.point(lambda v: v), noise).convert("RGB")

    # 四周压暗，收住视线
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-int(W * 0.22), -int(H * 0.30), int(W * 1.22), int(H * 1.30)], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    img = Image.composite(img, Image.new("RGB", (W, H), dark), vig)

    return img


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    slug = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / f"wenshucha-seo/content/covers/{slug}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    build(slug).save(out, "JPEG", quality=88)
    print(out)


if __name__ == "__main__":
    main()
