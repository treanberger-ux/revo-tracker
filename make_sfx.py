"""Синтезировать звуки глотка. Шесть вариантов, чтобы не повторялись подряд.

Свои, а не вырезанные из чужого трека: выкладывать чужую музыку на
публичный сайт нельзя, и нарезка на короткие куски этого не меняет.

Модель глотка: два или три импульса, у каждого высота падает с ~420 до
~110 Гц за десятки миллисекунд, плюс короткий призвук в начале. Ухо
слышит это как «глюк-глюк».

Плеер в приложении рассчитан на клипы до двух секунд и сам делает
плавный вход и затухание. Значит сюда же можно положить лицензированные
клипы под теми же именами, и код менять не придётся.

    python make_sfx.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import numpy as np

КОРЕНЬ = pathlib.Path(__file__).resolve().parent
ПАПКА = КОРЕНЬ / "sfx"
ЧАСТОТА = 44100
ШТУК = 6

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def импульс(длина: float, сверху: float, снизу: float, громкость: float,
            генератор: np.random.Generator) -> np.ndarray:
    t = np.linspace(0, длина, int(ЧАСТОТА * длина), endpoint=False)
    # высота падает по экспоненте, фаза берётся интегралом, иначе слышен щелчок
    k = 18.0
    f = снизу + (сверху - снизу) * np.exp(-k * t)
    фаза = 2 * np.pi * (снизу * t + (сверху - снизу) / k * (1 - np.exp(-k * t)))
    тон = np.sin(фаза)

    огиб = np.exp(-11 * t)
    атака = np.minimum(1.0, t / 0.004)          # 4 мс, чтобы не щёлкало
    тело = тон * огиб * атака

    # призвук жидкости: короткий шум, придавленный сверху
    шум = генератор.normal(0, 1, len(t)) * np.exp(-70 * t) * 0.35
    return (тело + шум) * громкость


def глоток(номер: int) -> np.ndarray:
    г = np.random.default_rng(1000 + номер)
    сколько = int(г.integers(2, 4))
    куски, пауза = [], 0.0
    for i in range(сколько):
        д = float(г.uniform(0.10, 0.17))
        верх = float(г.uniform(360, 470)) * (0.88 ** i)
        низ = float(г.uniform(95, 125))
        гр = float(г.uniform(0.55, 0.85)) * (0.85 ** i)
        куски.append((пауза, импульс(д, верх, низ, гр, г)))
        пауза += д + float(г.uniform(0.045, 0.095))

    длина = int(ЧАСТОТА * (пауза + 0.35))
    звук = np.zeros(длина)
    for сдвиг, кусок in куски:
        a = int(сдвиг * ЧАСТОТА)
        звук[a:a + len(кусок)] += кусок

    пик = np.max(np.abs(звук)) or 1.0
    return (звук / пик * 0.85).astype(np.float32)


def главная() -> int:
    ПАПКА.mkdir(exist_ok=True)
    for i in range(1, ШТУК + 1):
        сырое = ПАПКА / f"_{i}.raw"
        цель = ПАПКА / f"sip{i}.mp3"
        глоток(i).tofile(сырое)
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "f32le", "-ar", str(ЧАСТОТА), "-ac", "1", "-i", str(сырое),
            "-c:a", "libmp3lame", "-b:a", "96k", str(цель)], check=True)
        сырое.unlink()
        print(f"  {цель.name}: {цель.stat().st_size // 1000} КБ")
    print(f"готово, {ШТУК} звуков в {ПАПКА}")
    return 0


if __name__ == "__main__":
    raise SystemExit(главная())
