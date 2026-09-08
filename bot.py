"""Ответ на /start: подпрыгивающая стрелка на кнопку меню.

    python bot.py

Держится длинным опросом, значит **живёт только пока запущен**. Всё
остальное в этом проекте работает и без него: кнопка меню ведёт на
страницу напрямую, а состояние лежит в облаке Telegram. Этот процесс
нужен ровно для приветствия.

Гифка не заливается файлом, а берётся по адресу с GitHub Pages: Telegram
скачивает её сам и дальше отдаёт из своего кеша.

Сеть на этой машине рвётся, поэтому каждый вызов делается с повторами,
а опрос переживает разрыв и продолжает с того же смещения.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

КОРЕНЬ = pathlib.Path(__file__).resolve().parent
СТРАНИЦА = "https://treanberger-ux.github.io/revo-tracker/"
СТРЕЛКА = СТРАНИЦА + "arrow.mp4"

ПРИВЕТ = (
    "Тут считается, сколько рево ты <b>не</b> выпил.\n\n"
    "Жми <b>Revo</b> внизу слева, у поля ввода. Внутри включаются микрофон "
    "и камера: звук ловит сёрбанье, камера ищет банку в кадре. Совпали за "
    "четыре секунды, глоток засчитан подтверждённым."
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def ключ() -> str:
    for строка in io.open(КОРЕНЬ / ".env", encoding="utf-8"):
        if строка.startswith("REVO_BOT_TOKEN="):
            return строка.split("=", 1)[1].strip()
    raise SystemExit("REVO_BOT_TOKEN не найден в .env")


ТОКЕН = ключ()


def зов(метод: str, тело: dict, попыток: int = 3, таймаут: int = 45):
    """Вызов API телом в UTF-8. Через argv кириллицу на Windows слать нельзя:
    аргументы нативных программ конвертируются, и буквы становятся '?'."""
    данные = json.dumps(тело, ensure_ascii=False).encode("utf-8")
    запрос = urllib.request.Request(
        f"https://api.telegram.org/bot{ТОКЕН}/{метод}", данные,
        {"Content-Type": "application/json; charset=utf-8"})
    for попытка in range(попыток):
        try:
            with urllib.request.urlopen(запрос, timeout=таймаут) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8", "replace"))
        except Exception as сбой:
            if попытка == попыток - 1:
                print(f"  {метод}: сеть не дала, {type(сбой).__name__}")
                return {"ok": False}
            time.sleep(3)


def поздороваться(чат: int) -> None:
    кнопка = {"inline_keyboard": [[
        {"text": "Открыть трекер", "web_app": {"url": СТРАНИЦА}}]]}
    ответ = зов("sendAnimation", {
        "chat_id": чат, "animation": СТРЕЛКА, "caption": ПРИВЕТ,
        "parse_mode": "HTML", "reply_markup": кнопка})
    if not ответ.get("ok"):
        # если гифка не дошла, приветствие всё равно должно прийти
        print("   гифка не ушла:", ответ.get("description"))
        зов("sendMessage", {"chat_id": чат, "text": ПРИВЕТ,
                            "parse_mode": "HTML", "reply_markup": кнопка})


def главная() -> int:
    я = зов("getMe", {})
    if not я.get("ok"):
        raise SystemExit("бот не отзывается")
    print(f"слушаю @{я['result']['username']}. Ctrl+C чтобы остановить.")

    смещение = 0
    while True:
        ответ = зов("getUpdates", {"offset": смещение, "timeout": 25},
                    попыток=1, таймаут=40)
        if not ответ.get("ok"):
            time.sleep(3)
            continue
        for u in ответ.get("result", []):
            смещение = u["update_id"] + 1
            сообщение = u.get("message") or {}
            текст = (сообщение.get("text") or "").strip()
            чат = (сообщение.get("chat") or {}).get("id")
            если_старт = текст.startswith("/start") or текст == ""
            if чат and (если_старт or текст):
                кто = (сообщение.get("from") or {}).get("username", "без имени")
                print(f"  {кто}: {текст[:40]!r}")
                поздороваться(чат)


if __name__ == "__main__":
    try:
        raise SystemExit(главная())
    except KeyboardInterrupt:
        print("\nостановлен")
