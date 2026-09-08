"""Нарисовать подпрыгивающую стрелку, которая показывает на кнопку меню.

Кнопка меню в Telegram сидит слева от поля ввода, то есть под сообщением.
Значит стрелка смотрит вниз и прыгает по вертикали: отскок с придавливанием
в нижней точке, как мяч.

    python make_arrow.py

Пишет `arrow.mp4`. Telegram принимает его в sendAnimation и крутит по кругу.
"""
from __future__ import annotations

import math
import pathlib
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

КОРЕНЬ = pathlib.Path(__file__).resolve().parent
РАЗМЕР = 360
КАДРОВ = 30          # один оборот прыжка
ЧАСТОТА = 30

ФОН = (23, 33, 43)          # тёмная тема Telegram
СТРЕЛКА = (232, 193, 90)    # золото, чтобы не сливаться с синей кнопкой

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def отскок(t: float) -> float:
    """0 вверху, 1 внизу. Быстрое падение, мягкий подъём."""
    # |sin| даёт симметрию, возведение в степень утяжеляет низ
    return abs(math.sin(math.pi * t)) ** 0.65


def кадр(t: float) -> Image.Image:
    им = Image.new("RGB", (РАЗМЕР, РАЗМЕР), ФОН)
    d = ImageDraw.Draw(им)

    низ = отскок(t)
    смещение = int(70 * низ)
    # придавливание у самой земли: чуть шире и ниже
    жим = max(0.0, (низ - 0.86) / 0.14)
    ширина = 1.0 + 0.18 * жим
    высота = 1.0 - 0.22 * жим

    цx = РАЗМЕР // 2
    верх = 74 + смещение

    древко_ш = int(30 * ширина)
    древко_в = int(112 * высота)
    d.rounded_rectangle(
        (цx - древко_ш // 2, верх, цx + древко_ш // 2, верх + древко_в),
        radius=древко_ш // 2, fill=СТРЕЛКА)

    крыло = int(66 * ширина)
    остриё = верх + древко_в + int(76 * высота)
    d.polygon([(цx - крыло, верх + древко_в - 6),
               (цx + крыло, верх + древко_в - 6),
               (цx, остриё)], fill=СТРЕЛКА)

    # тень-пятно на земле: темнеет и сжимается по мере подъёма
    тень_y = РАЗМЕР - 46
    r = int(52 * (0.55 + 0.45 * низ))
    a = int(70 * низ)
    слой = Image.new("RGBA", им.size, (0, 0, 0, 0))
    ImageDraw.Draw(слой).ellipse((цx - r, тень_y - r // 4, цx + r, тень_y + r // 4),
                                 fill=(0, 0, 0, a))
    им = Image.alpha_composite(им.convert("RGBA"), слой).convert("RGB")
    return им


def главная() -> int:
    if not shutil.which("ffmpeg"):
        raise SystemExit("нужен ffmpeg в PATH")
    врем = pathlib.Path(tempfile.mkdtemp())
    for i in range(КАДРОВ):
        кадр(i / КАДРОВ).save(врем / f"{i:03d}.png")

    цель = КОРЕНЬ / "arrow.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-framerate", str(ЧАСТОТА), "-i", str(врем / "%03d.png"),
        "-filter_complex", "[0]loop=loop=3:size=30:start=0[v]", "-map", "[v]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "baseline",
        "-movflags", "+faststart", str(цель)], check=True)
    shutil.rmtree(врем, ignore_errors=True)
    print(f"готово: {цель}  {цель.stat().st_size // 1000} КБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(главная())
