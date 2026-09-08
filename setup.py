"""Настроить бота на мини-апп. Запускается один раз, потом ничего не крутится.

    python setup.py https://<логин>.github.io/<репозиторий>/

Кнопка меню у бота указывает прямо на веб-приложение, поэтому процесс-бот
не нужен вовсе: Telegram открывает страницу сам. Единственное, что здесь
делается ещё, это описание и команда /start, чтобы бот не выглядел пустым.

Ключ берётся из `.env`, в репозиторий он не попадает.
"""
from __future__ import annotations

import io
import pathlib
import sys
import urllib.parse
import urllib.request
import json

КОРЕНЬ = pathlib.Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def ключ() -> str:
    for строка in io.open(КОРЕНЬ / ".env", encoding="utf-8"):
        if строка.startswith("REVO_BOT_TOKEN="):
            return строка.split("=", 1)[1].strip()
    raise SystemExit("REVO_BOT_TOKEN не найден в .env")


def вызов(метод: str, **поля):
    данные = urllib.parse.urlencode(
        {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
         for k, v in поля.items()}).encode()
    адрес = f"https://api.telegram.org/bot{ключ()}/{метод}"
    with urllib.request.urlopen(urllib.request.Request(адрес, данные), timeout=30) as r:
        ответ = json.load(r)
    состояние = "ок" if ответ.get("ok") else "ОШИБКА"
    print(f"  {метод}: {состояние}"
          f"{'' if ответ.get('ok') else ' — ' + str(ответ.get('description'))}")
    return ответ


def главная() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    url = sys.argv[1].strip()
    if not url.startswith("https://"):
        raise SystemExit("Telegram принимает только https")

    print("настраиваю бота на", url)
    вызов("setChatMenuButton",
          menu_button={"type": "web_app", "text": "Открыть",
                       "web_app": {"url": url}})
    вызов("setMyDescription",
          description="Считает, сколько рево ты не выпил. Слушает сёрбанье "
                      "и смотрит в камеру, чтобы поймать тебя на глотке.")
    вызов("setMyShortDescription",
          short_description="Трекер невыпитого рево")
    вызов("setMyCommands", commands=[{"command": "start", "description": "Открыть трекер"}])
    print("готово. Кнопка меню у бота ведёт на приложение, процесс держать не надо.")
    return 0


if __name__ == "__main__":
    raise SystemExit(главная())
