#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Multi-Tool v2.0
Файл: tg_tool.py
Требования: pip install telethon python-socks aiohttp cryptg
Структура:
  sessions/  — папка с .session файлами
  proxies.txt — прокси (socks5://user:pass@ip:port или http://ip:port)
  config.json — API_ID, API_HASH
"""

# ═══════════════════════════════════════════════════════════════
# ЧАСТЬ 1 — ЯДРО: импорты, конфиг, утилиты, менеджер, меню
# ═══════════════════════════════════════════════════════════════

import os
import sys
import json
import glob
import time
import random
import asyncio
import hashlib
import re
import struct
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

try:
    from telethon import TelegramClient, events, errors, functions, types
    from telethon.tl.functions.messages import (
        GetMessagesViewsRequest, SendReactionRequest, ForwardMessagesRequest,
        SendVoteRequest, GetBotCallbackAnswerRequest, ReportRequest,
        DeleteMessagesRequest, EditMessageRequest, SearchRequest,
        GetHistoryRequest, ReadHistoryRequest, SendMessageRequest,
        UpdatePinnedMessageRequest, SendMediaRequest,
        GetScheduledHistoryRequest, SendScheduledMessagesRequest,
    )
    from telethon.tl.functions.channels import (
        JoinChannelRequest, LeaveChannelRequest, InviteToChannelRequest,
        EditBannedRequest, EditAdminRequest, CreateChannelRequest,
        EditPhotoRequest, EditTitleRequest, DeleteChannelRequest,
        GetParticipantsRequest, GetFullChannelRequest,
    )
    from telethon.tl.functions.account import (
        UpdateProfileRequest, UpdateUsernameRequest,
        GetAuthorizationsRequest, ResetAuthorizationRequest,
        DeleteAccountRequest, UpdateStatusRequest,
        GetPasswordRequest,
    )
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
    from telethon.tl.functions.messages import (
        StartBotRequest, RequestWebViewRequest,
    )
    from telethon.tl.types import (
        ReactionEmoji, ReactionCustomEmoji,
        ChannelParticipantsSearch, ChannelParticipantsRecent,
        ChatBannedRights, ChatAdminRights,
        InputPeerChannel, InputPeerUser, InputChannel,
        InputReportReasonSpam, InputReportReasonViolence,
        InputReportReasonPornography, InputReportReasonChildAbuse,
        InputReportReasonOther, InputReportReasonFake,
        InputReportReasonGeoIrrelevant, InputReportReasonIllegalDrugs,
        InputReportReasonPersonalDetails,
        DocumentAttributeFilename,
        InputMediaUploadedDocument, InputMediaUploadedPhoto,
        MessageMediaDocument, MessageMediaPhoto,
        KeyboardButtonUrl, KeyboardButtonCallback,
        KeyboardButtonRequestPhone, ReplyInlineMarkup,
        PeerChannel, PeerUser, PeerChat,
        UpdateNewChannelMessage, UpdateNewMessage,
        Channel, Chat, User,
    )
    from telethon.errors import (
        SessionPasswordNeededError, FloodWaitError,
        UserAlreadyParticipantError, UserNotParticipantError,
        ChatWriteForbiddenError, ChannelPrivateError,
        ReactionInvalidError, PeerIdInvalidError,
        PhoneNumberBannedError, AuthKeyUnregisteredError,
        UserDeactivatedBanError, UserDeactivatedError,
    )
except ImportError:
    print("❌ Установите зависимости: pip install telethon python-socks aiohttp")
    sys.exit(1)

# ─── Логирование ───
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("TG-Tool")

# ─── Пути ───
BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"
PROXIES_FILE = BASE_DIR / "proxies.txt"
CONFIG_FILE = BASE_DIR / "config.json"
SCENARIOS_DIR = BASE_DIR / "scenarios"

SESSIONS_DIR.mkdir(exist_ok=True)
SCENARIOS_DIR.mkdir(exist_ok=True)

# ─── Цвета терминала ───
class C:
    R = "\033[91m"   # red
    G = "\033[92m"   # green
    Y = "\033[93m"   # yellow
    B = "\033[94m"   # blue
    M = "\033[95m"   # magenta
    CY = "\033[96m"  # cyan
    W = "\033[97m"   # white
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RST = "\033[0m"
    UNDERLINE = "\033[4m"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print(f"""{C.CY}{C.BOLD}
  ╔══════════════════════════════════════════════════╗
  ║        ⚡ TELEGRAM MULTI-TOOL v2.0 ⚡           ║
  ║            Telethon + Proxy Engine               ║
  ╚══════════════════════════════════════════════════╝{C.RST}
""")

# ═══════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_api_credentials() -> Tuple[int, str]:
    cfg = load_config()
    api_id = cfg.get("api_id")
    api_hash = cfg.get("api_hash")
    if not api_id or not api_hash:
        print(f"{C.Y}⚠ Первый запуск — нужны API_ID и API_HASH{C.RST}")
        print(f"{C.DIM}  Получить: https://my.telegram.org/apps{C.RST}")
        api_id = int(input(f"{C.CY}  API_ID: {C.RST}").strip())
        api_hash = input(f"{C.CY}  API_HASH: {C.RST}").strip()
        cfg["api_id"] = api_id
        cfg["api_hash"] = api_hash
        save_config(cfg)
        print(f"{C.G}✅ Сохранено в config.json{C.RST}")
    return int(api_id), str(api_hash)

# ═══════════════════════════════════════════════════════════════
# ПРОКСИ
# ═══════════════════════════════════════════════════════════════

def load_proxies() -> List[dict]:
    """
    Формат proxies.txt (по одному на строку):
      socks5://user:pass@ip:port
      socks5://ip:port
      http://user:pass@ip:port
      http://ip:port
      socks4://ip:port
    """
    proxies = []
    if not PROXIES_FILE.exists():
        return proxies
    with open(PROXIES_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                p = parse_proxy(line)
                if p:
                    proxies.append(p)
            except Exception:
                pass
    return proxies

def parse_proxy(url: str) -> Optional[dict]:
    """Парсит строку прокси в dict для telethon"""
    url = url.strip()
    if "://" not in url:
        url = "socks5://" + url

    scheme = url.split("://")[0].lower()
    rest = url.split("://")[1]

    proxy_type = {
        "socks5": 2,  # python-socks SOCKS5
        "socks4": 1,
        "http": 3,
        "https": 3,
    }.get(scheme, 2)

    username = None
    password = None
    if "@" in rest:
        creds, hostport = rest.rsplit("@", 1)
        if ":" in creds:
            username, password = creds.split(":", 1)
        else:
            username = creds
    else:
        hostport = rest

    if ":" in hostport:
        host, port = hostport.rsplit(":", 1)
        port = int(port)
    else:
        host = hostport
        port = 1080

    return {
        "proxy_type": scheme,
        "addr": host,
        "port": port,
        "username": username,
        "password": password,
        "rdns": True,
    }

def proxy_to_telethon(p: dict) -> tuple:
    """Конвертирует proxy dict в формат для TelegramClient"""
    import socks
    ptype_map = {
        "socks5": socks.SOCKS5,
        "socks4": socks.SOCKS4,
        "http": socks.HTTP,
        "https": socks.HTTP,
    }
    return (
        ptype_map.get(p["proxy_type"], socks.SOCKS5),
        p["addr"],
        p["port"],
        p.get("rdns", True),
        p.get("username"),
        p.get("password"),
    )

def proxy_str(p: dict) -> str:
    if not p:
        return "без прокси"
    s = f"{p['proxy_type']}://"
    if p.get("username"):
        s += f"{p['username']}:***@"
    s += f"{p['addr']}:{p['port']}"
    return s

# ═══════════════════════════════════════════════════════════════
# МЕНЕДЖЕР СЕССИЙ
# ═══════════════════════════════════════════════════════════════

def get_sessions() -> List[str]:
    """Возвращает список имён .session файлов (без расширения)"""
    files = glob.glob(str(SESSIONS_DIR / "*.session"))
    return [Path(f).stem for f in sorted(files)]

def list_sessions():
    sessions = get_sessions()
    if not sessions:
        print(f"{C.R}❌ Нет .session файлов в папке sessions/{C.RST}")
        return []
    print(f"\n{C.CY}{'─'*50}")
    print(f"  📋 Найдено сессий: {len(sessions)}")
    print(f"{'─'*50}{C.RST}")
    for i, s in enumerate(sessions, 1):
        print(f"  {C.W}{i:3}. {C.G}{s}{C.RST}")
    print(f"{C.CY}{'─'*50}{C.RST}")
    return sessions

def select_sessions(prompt="Выбери сессии") -> List[str]:
    """
    Выбор сессий: all / 1,2,3 / 1-5 / конкретный номер
    """
    sessions = list_sessions()
    if not sessions:
        return []
    print(f"\n{C.Y}  {prompt}")
    print(f"  (all = все, 1,3,5 = конкретные, 1-10 = диапазон){C.RST}")
    choice = input(f"{C.CY}  > {C.RST}").strip().lower()

    if choice == "all":
        return sessions

    selected = set()
    parts = choice.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            try:
                a, b = part.split("-")
                for i in range(int(a), int(b) + 1):
                    if 1 <= i <= len(sessions):
                        selected.add(sessions[i - 1])
            except ValueError:
                pass
        else:
            try:
                idx = int(part)
                if 1 <= idx <= len(sessions):
                    selected.add(sessions[idx - 1])
            except ValueError:
                pass
    return list(selected)

# ═══════════════════════════════════════════════════════════════
# СОЗДАНИЕ КЛИЕНТА
# ═══════════════════════════════════════════════════════════════

async def create_client(session_name: str, proxy: dict = None) -> Optional[TelegramClient]:
    api_id, api_hash = get_api_credentials()
    session_path = str(SESSIONS_DIR / session_name)

    kwargs = {}
    if proxy:
        try:
            kwargs["proxy"] = proxy_to_telethon(proxy)
        except Exception as e:
            logger.warning(f"Proxy error: {e}")

    client = TelegramClient(
        session_path,
        api_id,
        api_hash,
        device_model="Samsung Galaxy S23",
        system_version="Android 14",
        app_version="10.14.5",
        lang_code="ru",
        system_lang_code="ru-RU",
        **kwargs
    )
    return client

async def safe_connect(client: TelegramClient, session_name: str) -> bool:
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"  {C.R}❌ {session_name} — не авторизован{C.RST}")
            await client.disconnect()
            return False
        return True
    except (PhoneNumberBannedError, UserDeactivatedBanError, UserDeactivatedError):
        print(f"  {C.R}💀 {session_name} — аккаунт забанен/удалён{C.RST}")
        return False
    except (AuthKeyUnregisteredError,):
        print(f"  {C.R}🔑 {session_name} — сессия невалидна{C.RST}")
        return False
    except Exception as e:
        print(f"  {C.R}⚠ {session_name} — ошибка: {e}{C.RST}")
        return False

# ═══════════════════════════════════════════════════════════════
# УТИЛИТЫ ПАРСИНГА ССЫЛОК
# ═══════════════════════════════════════════════════════════════

def parse_tg_link(link: str) -> dict:
    """
    Парсит ссылку вида:
      https://t.me/channel/123
      https://t.me/c/1234567890/123
      https://t.me/channel
      https://t.me/+invite_hash
      @channel
      t.me/bot?start=ref
    Возвращает dict с ключами: channel, post_id, invite_hash, bot, start_param
    """
    result = {"channel": None, "post_id": None, "invite_hash": None,
              "bot": None, "start_param": None, "startapp": None}

    link = link.strip()

    # @channel
    if link.startswith("@"):
        result["channel"] = link[1:]
        return result

    # Нормализация
    link = link.replace("https://t.me/", "").replace("http://t.me/", "")
    link = link.replace("t.me/", "")

    # Инвайт
    if link.startswith("+") or link.startswith("joinchat/"):
        result["invite_hash"] = link.replace("joinchat/", "").lstrip("+")
        return result

    parts = link.split("?")
    path = parts[0].strip("/")
    params = {}
    if len(parts) > 1:
        for kv in parts[1].split("&"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                params[k] = v

    segments = path.split("/")

    # bot?start=ref
    if "start" in params:
        result["bot"] = segments[0]
        result["start_param"] = params["start"]
        return result

    # webapp startapp
    if "startapp" in params:
        result["bot"] = segments[0]
        result["startapp"] = params["startapp"]
        return result

    # c/1234567890/123 (приватный канал)
    if len(segments) >= 3 and segments[0] == "c":
        result["channel"] = int(segments[1])
        result["post_id"] = int(segments[2])
        return result

    # channel/123
    if len(segments) >= 2:
        result["channel"] = segments[0]
        try:
            result["post_id"] = int(segments[1])
        except ValueError:
            pass
        return result

    # channel
    if len(segments) == 1:
        result["channel"] = segments[0]
        return result

    return result

async def resolve_channel(client, channel_input):
    """Резолвит канал по username, id или ссылке"""
    if isinstance(channel_input, int):
        try:
            entity = await client.get_entity(PeerChannel(channel_input))
            return entity
        except Exception:
            entity = await client.get_entity(channel_input)
            return entity
    return await client.get_entity(channel_input)

def random_delay(min_s=1.0, max_s=3.0):
    return random.uniform(min_s, max_s)

async def human_delay(min_s=0.5, max_s=2.5):
    await asyncio.sleep(random_delay(min_s, max_s))

def format_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

# ═══════════════════════════════════════════════════════════════
# EXECUTOR — запуск задач по сессиям
# ═══════════════════════════════════════════════════════════════

async def execute_on_sessions(
    sessions: List[str],
    task_func,
    task_name: str = "задача",
    max_concurrent: int = 5,
    delay_between: Tuple[float, float] = (1.0, 3.0),
    **kwargs
):
    """
    Запускает task_func(client, session_name, **kwargs) для каждой сессии
    с ограничением параллельности и задержками.
    """
    proxies = load_proxies()
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {"success": 0, "fail": 0, "total": len(sessions)}

    print(f"\n{C.CY}{'═'*50}")
    print(f"  🚀 {task_name}")
    print(f"  📊 Сессий: {len(sessions)} | Прокси: {len(proxies)}")
    print(f"{'═'*50}{C.RST}\n")

    async def worker(session_name, index):
        async with semaphore:
            proxy = proxies[index % len(proxies)] if proxies else None
            client = await create_client(session_name, proxy)
            if not client:
                results["fail"] += 1
                return

            try:
                ok = await safe_connect(client, session_name)
                if not ok:
                    results["fail"] += 1
                    return

                await task_func(client, session_name, **kwargs)
                results["success"] += 1
                print(f"  {C.G}✅ {session_name} — OK{C.RST}")
            except FloodWaitError as e:
                wait = e.seconds
                print(f"  {C.Y}⏳ {session_name} — FloodWait {wait}s{C.RST}")
                if wait < 120:
                    await asyncio.sleep(wait)
                    try:
                        await task_func(client, session_name, **kwargs)
                        results["success"] += 1
                        print(f"  {C.G}✅ {session_name} — OK (после ожидания){C.RST}")
                    except Exception as e2:
                        results["fail"] += 1
                        print(f"  {C.R}❌ {session_name} — {e2}{C.RST}")
                else:
                    results["fail"] += 1
            except Exception as e:
                results["fail"] += 1
                print(f"  {C.R}❌ {session_name} — {e}{C.RST}")
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

            await asyncio.sleep(random_delay(*delay_between))

    tasks = [worker(s, i) for i, s in enumerate(sessions)]
    await asyncio.gather(*tasks)

    print(f"\n{C.CY}{'═'*50}")
    print(f"  📊 Результат: {C.G}✅ {results['success']}{C.RST}"
          f" | {C.R}❌ {results['fail']}{C.RST}"
          f" | 📊 {results['total']} всего")
    print(f"{C.CY}{'═'*50}{C.RST}")

    return results

# ═══════════════════════════════════════════════════════════════
# МЕНЮ
# ═══════════════════════════════════════════════════════════════

def print_menu():
    clear()
    banner()
    menu = f"""
{C.CY}┌────┬─────────────────────────────────────────────────────┐
│    │ {C.BOLD}НАКРУТКА{C.RST}{C.CY}                                                │
│{C.W}  1 {C.CY}│ 👁  Просмотр поста                                     │
│{C.W}  2 {C.CY}│ 👍 Реакция                                             │
│{C.W}  3 {C.CY}│ 📢 Подписка                                            │
│{C.W}  4 {C.CY}│ 🚀 Всё сразу                                           │
│{C.W}  5 {C.CY}│ 💬 Комментарий                                         │
│{C.W}  6 {C.CY}│ 📤 Пересылка                                           │
│{C.W}  7 {C.CY}│ 📊 Голосование                                         │
│{C.W}  8 {C.CY}│ 🔘 Inline кнопки                                       │
│{C.W}  9 {C.CY}│ 💥 Массовая реакция на N постов                        │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}БОТЫ / WEBAPP{C.RST}{C.CY}                                          │
│{C.W} 10 {C.CY}│ 🤖 Авто-старт бота + реферальная ссылка               │
│{C.W} 11 {C.CY}│ 📋 Сценарий бота из JSON                               │
│{C.W} 12 {C.CY}│ 🌐 WebApp + startapp параметр                          │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}РАССЫЛКА{C.RST}{C.CY}                                               │
│{C.W} 13 {C.CY}│ 📨 Рассылка в ЛС                                      │
│{C.W} 14 {C.CY}│ 👥 Инвайт                                              │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}СООБЩЕНИЯ{C.RST}{C.CY}                                              │
│{C.W} 15 {C.CY}│ 📝 Отправка с медиа + Markdown                         │
│{C.W} 16 {C.CY}│ ⏰ Отложенная отправка                                 │
│{C.W} 17 {C.CY}│ ✏️  Редактирование                                      │
│{C.W} 18 {C.CY}│ 📌 Закреп/откреп                                       │
│{C.W} 19 {C.CY}│ 🗑  Удалить свои сообщения                             │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}КАНАЛЫ{C.RST}{C.CY}                                                 │
│{C.W} 20 {C.CY}│ ➕ Создать канал/группу                                 │
│{C.W} 21 {C.CY}│ ⚙️  Настройка (название/описание/фото/username)         │
│{C.W} 22 {C.CY}│ 👑 Назначить админа (с выбором прав)                   │
│{C.W} 23 {C.CY}│ 🔨 Массовый бан/кик                                    │
│{C.W} 24 {C.CY}│ 🧹 Очистка (удалить все посты)                         │
│{C.W} 25 {C.CY}│ 📋 Копировать настройки канала                          │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}РЕПОРТЫ{C.RST}{C.CY}                                                │
│{C.W} 26 {C.CY}│ 🚨 Репорт на юзера/канал (8 причин)                    │
│{C.W} 27 {C.CY}│ 🚨 Репорт на сообщение                                 │
│{C.W} 28 {C.CY}│ 🚫 Массовая блокировка                                 │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}ПАРСИНГ{C.RST}{C.CY}                                                │
│{C.W} 29 {C.CY}│ 🔍 Парсер участников                                   │
│{C.W} 30 {C.CY}│ 📊 Статистика канала                                   │
│{C.W} 31 {C.CY}│ 📥 Скачивание медиа                                    │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}АВТОМАТИЗАЦИЯ{C.RST}{C.CY}                                          │
│{C.W} 32 {C.CY}│ 👀 Мониторинг (авто-реакции на новые посты)            │
│{C.W} 33 {C.CY}│ 🤖 Авто-ответчик по ключевым словам                   │
│{C.W} 34 {C.CY}│ 📝 Авто-постинг                                        │
│{C.W} 35 {C.CY}│ 📋 Задачи из JSON                                      │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}АНТИДЕТЕКТ{C.RST}{C.CY}                                             │
│{C.W} 36 {C.CY}│ 🔥 Прогрев (чтение, скролл, профили)                  │
│{C.W} 37 {C.CY}│ 🟢 Имитация онлайна (параллельно)                     │
├────┼─────────────────────────────────────────────────────────┤
│    │ {C.BOLD}АККАУНТЫ{C.RST}{C.CY}                                               │
│{C.W} 38 {C.CY}│ ✅ Чекер                                               │
│{C.W} 39 {C.CY}│ 📱 Активные сессии                                     │
│{C.W} 40 {C.CY}│ 💀 Сброс ВСЕХ сессий                                   │
│{C.W} 41 {C.CY}│ 🎯 Выборочный сброс                                    │
│{C.W} 42 {C.CY}│ 🔑 Запрос кода + 2FA                                   │
│{C.W} 43 {C.CY}│ ℹ️  Инфо                                                │
│{C.W} 44 {C.CY}│ ✏️  Имя/био                                             │
│{C.W} 45 {C.CY}│ 🖼  Фото                                               │
│{C.W} 46 {C.CY}│ 🔐 2FA                                                 │
│{C.W} 47 {C.CY}│ 🚪 Отписка от каналов                                  │
│{C.W} 48 {C.CY}│ ☠️  Удалить аккаунт                                     │
├────┼─────────────────────────────────────────────────────────┤
│{C.W} 49 {C.CY}│ 📋 Список сессий                                       │
│{C.W} 50 {C.CY}│ 🌐 Список прокси                                       │
│{C.R}  0 {C.CY}│ ❌ Выход                                               │
└────┴─────────────────────────────────────────────────────────┘{C.RST}"""
    print(menu)

def pause():
    input(f"\n{C.DIM}  Нажми Enter для продолжения...{C.RST}")

def ask(prompt: str, default: str = "") -> str:
    val = input(f"{C.CY}  {prompt}{C.RST}").strip()
    return val if val else default

def ask_int(prompt: str, default: int = 0) -> int:
    val = ask(prompt, str(default))
    try:
        return int(val)
    except ValueError:
        return default

def ask_reaction() -> str:
    print(f"\n{C.Y}  Доступные реакции:")
    reactions = ["👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔",
                 "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
                 "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳",
                 "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌", "🏆",
                 "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈",
                 "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈",
                 "😇", "😨", "🤝", "✍️", "🤗", "🫡", "🎅", "🎄",
                 "☃️", "💅", "🤪", "🗿", "🆒", "💘", "🙉", "🦄",
                 "😘", "💊", "🙊", "😎", "👾", "🤷‍♂️", "🤷", "🤷‍♀️",
                 "😡"]
    for i in range(0, len(reactions), 10):
        chunk = reactions[i:i+10]
        print(f"  {' '.join(chunk)}")
    print(f"{C.RST}")
    r = ask("Реакция (emoji): ")
    return r if r else "👍"

# ═══════════════════════════════════════════════════════════════
# КОНЕЦ ЧАСТИ 1
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# ЧАСТЬ 2 — ФУНКЦИИ 1-35
# ═══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# 1. ПРОСМОТР ПОСТА
# ─────────────────────────────────────────────────────────────

async def task_view_post(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    entity = await resolve_channel(client, channel)
    await client(GetMessagesViewsRequest(
        peer=entity,
        id=[post_id],
        increment=True
    ))
    await human_delay(0.5, 1.5)

async def action_view_post():
    link = ask("Ссылка на пост (t.me/channel/123): ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Неверная ссылка. Нужен формат: t.me/channel/123{C.RST}")
        return
    sessions = select_sessions("Выбери аккаунты для просмотра")
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_view_post,
        task_name="👁 Просмотр поста",
        channel=parsed["channel"],
        post_id=parsed["post_id"]
    )

# ─────────────────────────────────────────────────────────────
# 2. РЕАКЦИЯ
# ─────────────────────────────────────────────────────────────

async def task_send_reaction(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    reaction = kw["reaction"]
    entity = await resolve_channel(client, channel)

    # Сначала просмотр
    await client(GetMessagesViewsRequest(
        peer=entity, id=[post_id], increment=True
    ))
    await human_delay(0.5, 1.5)

    react_obj = ReactionEmoji(emoticon=reaction)
    await client(SendReactionRequest(
        peer=entity,
        msg_id=post_id,
        reaction=[react_obj]
    ))
    await human_delay(0.3, 1.0)

async def action_send_reaction():
    link = ask("Ссылка на пост: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Неверная ссылка{C.RST}")
        return
    reaction = ask_reaction()
    sessions = select_sessions("Выбери аккаунты для реакции")
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_send_reaction,
        task_name=f"👍 Реакция {reaction}",
        channel=parsed["channel"],
        post_id=parsed["post_id"],
        reaction=reaction
    )

# ─────────────────────────────────────────────────────────────
# 3. ПОДПИСКА
# ─────────────────────────────────────────────────────────────

async def task_subscribe(client, session_name, **kw):
    channel = kw["channel"]
    invite_hash = kw.get("invite_hash")

    if invite_hash:
        from telethon.tl.functions.messages import ImportChatInviteRequest
        try:
            await client(ImportChatInviteRequest(invite_hash))
        except UserAlreadyParticipantError:
            pass
    else:
        entity = await resolve_channel(client, channel)
        try:
            await client(JoinChannelRequest(entity))
        except UserAlreadyParticipantError:
            pass
    await human_delay(1.0, 3.0)

async def action_subscribe():
    link = ask("Ссылка на канал/группу (или @username): ")
    parsed = parse_tg_link(link)
    sessions = select_sessions("Выбери аккаунты для подписки")
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_subscribe,
        task_name="📢 Подписка",
        channel=parsed["channel"],
        invite_hash=parsed.get("invite_hash")
    )

# ─────────────────────────────────────────────────────────────
# 4. ВСЁ СРАЗУ (просмотр + реакция + подписка)
# ─────────────────────────────────────────────────────────────

async def task_all_in_one(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    reaction = kw["reaction"]
    invite_hash = kw.get("invite_hash")

    # Подписка
    if invite_hash:
        from telethon.tl.functions.messages import ImportChatInviteRequest
        try:
            await client(ImportChatInviteRequest(invite_hash))
        except UserAlreadyParticipantError:
            pass
    else:
        entity = await resolve_channel(client, channel)
        try:
            await client(JoinChannelRequest(entity))
        except UserAlreadyParticipantError:
            pass

    await human_delay(1.0, 2.5)

    # Просмотр
    entity = await resolve_channel(client, channel)
    await client(GetMessagesViewsRequest(
        peer=entity, id=[post_id], increment=True
    ))
    await human_delay(0.5, 1.5)

    # Реакция
    react_obj = ReactionEmoji(emoticon=reaction)
    await client(SendReactionRequest(
        peer=entity, msg_id=post_id,
        reaction=[react_obj]
    ))
    await human_delay(0.3, 1.0)

async def action_all_in_one():
    link = ask("Ссылка на пост: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Нужна ссылка на пост{C.RST}")
        return
    reaction = ask_reaction()
    sessions = select_sessions("Выбери аккаунты")
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_all_in_one,
        task_name="🚀 Подписка + Просмотр + Реакция",
        channel=parsed["channel"],
        post_id=parsed["post_id"],
        reaction=reaction,
        invite_hash=parsed.get("invite_hash")
    )

# ─────────────────────────────────────────────────────────────
# 5. КОММЕНТАРИЙ
# ─────────────────────────────────────────────────────────────

async def task_comment(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    comments = kw["comments"]
    entity = await resolve_channel(client, channel)

    comment_text = random.choice(comments)
    await client.send_message(
        entity=entity,
        message=comment_text,
        comment_to=post_id
    )
    await human_delay(1.0, 3.0)

async def action_comment():
    link = ask("Ссылка на пост: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Нужна ссылка на пост{C.RST}")
        return
    print(f"{C.Y}  Введи комментарии (каждый с новой строки, пустая строка = конец):{C.RST}")
    comments = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        comments.append(line)
    if not comments:
        print(f"{C.R}❌ Нет комментариев{C.RST}")
        return
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_comment,
        task_name="💬 Комментарий",
        channel=parsed["channel"],
        post_id=parsed["post_id"],
        comments=comments
    )

# ─────────────────────────────────────────────────────────────
# 6. ПЕРЕСЫЛКА
# ─────────────────────────────────────────────────────────────

async def task_forward(client, session_name, **kw):
    from_channel = kw["from_channel"]
    post_id = kw["post_id"]
    to_channel = kw["to_channel"]

    from_entity = await resolve_channel(client, from_channel)
    to_entity = await resolve_channel(client, to_channel)

    await client.forward_messages(
        entity=to_entity,
        messages=post_id,
        from_peer=from_entity
    )
    await human_delay(1.0, 2.0)

async def action_forward():
    link = ask("Ссылка на пост для пересылки: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Нужна ссылка на пост{C.RST}")
        return
    to_link = ask("Куда переслать (канал/группа/@username): ")
    to_parsed = parse_tg_link(to_link)
    if not to_parsed["channel"]:
        print(f"{C.R}❌ Неверный получатель{C.RST}")
        return
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_forward,
        task_name="📤 Пересылка",
        from_channel=parsed["channel"],
        post_id=parsed["post_id"],
        to_channel=to_parsed["channel"]
    )

# ─────────────────────────────────────────────────────────────
# 7. ГОЛОСОВАНИЕ
# ─────────────────────────────────────────────────────────────

async def task_vote(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    options = kw["options"]
    entity = await resolve_channel(client, channel)

    # Просмотр
    await client(GetMessagesViewsRequest(
        peer=entity, id=[post_id], increment=True
    ))
    await human_delay(0.3, 1.0)

    await client(SendVoteRequest(
        peer=entity,
        msg_id=post_id,
        options=[bytes([o]) for o in options]
    ))
    await human_delay(0.5, 1.5)

async def action_vote():
    link = ask("Ссылка на пост с опросом: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Нужна ссылка на пост{C.RST}")
        return
    opts_str = ask("Номера вариантов через запятую (0,1,2...): ", "0")
    try:
        options = [int(x.strip()) for x in opts_str.split(",")]
    except ValueError:
        options = [0]
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_vote,
        task_name="📊 Голосование",
        channel=parsed["channel"],
        post_id=parsed["post_id"],
        options=options
    )

# ─────────────────────────────────────────────────────────────
# 8. INLINE КНОПКИ
# ─────────────────────────────────────────────────────────────

async def task_click_button(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    button_idx = kw["button_idx"]
    entity = await resolve_channel(client, channel)

    msgs = await client.get_messages(entity, ids=post_id)
    msg = msgs
    if not msg or not msg.reply_markup:
        return

    buttons = []
    if hasattr(msg.reply_markup, 'rows'):
        for row in msg.reply_markup.rows:
            for btn in row.buttons:
                buttons.append(btn)

    if button_idx >= len(buttons):
        return

    btn = buttons[button_idx]
    if isinstance(btn, KeyboardButtonCallback):
        await client(GetBotCallbackAnswerRequest(
            peer=entity,
            msg_id=post_id,
            data=btn.data
        ))
    elif isinstance(btn, KeyboardButtonUrl):
        pass  # URL кнопки просто открываем через просмотр
    await human_delay(0.5, 1.5)

async def action_click_button():
    link = ask("Ссылка на пост с кнопками: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Нужна ссылка на пост{C.RST}")
        return

    # Показываем кнопки через первый аккаунт
    sessions = get_sessions()
    if not sessions:
        print(f"{C.R}❌ Нет сессий{C.RST}")
        return

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    await safe_connect(client, sessions[0])

    try:
        entity = await resolve_channel(client, parsed["channel"])
        msg = await client.get_messages(entity, ids=parsed["post_id"])
        if not msg or not msg.reply_markup:
            print(f"{C.R}❌ Нет кнопок в этом посте{C.RST}")
            return

        buttons = []
        if hasattr(msg.reply_markup, 'rows'):
            for row in msg.reply_markup.rows:
                for btn in row.buttons:
                    buttons.append(btn)

        print(f"\n{C.Y}  Кнопки в посте:{C.RST}")
        for i, btn in enumerate(buttons):
            btype = "callback" if isinstance(btn, KeyboardButtonCallback) else "url"
            print(f"  {C.W}{i}. {btn.text} [{btype}]{C.RST}")

    finally:
        await client.disconnect()

    button_idx = ask_int("Номер кнопки: ", 0)
    sel_sessions = select_sessions()
    if not sel_sessions:
        return
    await execute_on_sessions(
        sel_sessions, task_click_button,
        task_name="🔘 Клик по inline кнопке",
        channel=parsed["channel"],
        post_id=parsed["post_id"],
        button_idx=button_idx
    )

# ─────────────────────────────────────────────────────────────
# 9. МАССОВАЯ РЕАКЦИЯ НА N ПОСТОВ
# ─────────────────────────────────────────────────────────────

async def task_mass_reaction(client, session_name, **kw):
    channel = kw["channel"]
    count = kw["count"]
    reaction = kw["reaction"]
    entity = await resolve_channel(client, channel)

    messages = await client.get_messages(entity, limit=count)
    react_obj = ReactionEmoji(emoticon=reaction)

    for msg in messages:
        if msg and msg.id:
            try:
                await client(GetMessagesViewsRequest(
                    peer=entity, id=[msg.id], increment=True
                ))
                await client(SendReactionRequest(
                    peer=entity, msg_id=msg.id,
                    reaction=[react_obj]
                ))
                await human_delay(0.5, 1.5)
            except Exception:
                pass

async def action_mass_reaction():
    channel_link = ask("Канал (@username или ссылка): ")
    parsed = parse_tg_link(channel_link)
    if not parsed["channel"]:
        print(f"{C.R}❌ Неверный канал{C.RST}")
        return
    count = ask_int("Количество последних постов: ", 10)
    reaction = ask_reaction()
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_mass_reaction,
        task_name=f"💥 Массовая реакция {reaction} на {count} постов",
        channel=parsed["channel"],
        count=count,
        reaction=reaction
    )

# ─────────────────────────────────────────────────────────────
# 10. АВТО-СТАРТ БОТА + РЕФЕРАЛЬНАЯ ССЫЛКА
# ─────────────────────────────────────────────────────────────

async def task_start_bot(client, session_name, **kw):
    bot = kw["bot"]
    start_param = kw.get("start_param", "")

    entity = await client.get_entity(bot)

    if start_param:
        await client(StartBotRequest(
            bot=entity,
            peer=entity,
            start_param=start_param
        ))
    else:
        await client.send_message(entity, "/start")
    await human_delay(1.5, 3.0)

async def action_start_bot():
    link = ask("Ссылка на бота (t.me/bot?start=ref или @bot): ")
    parsed = parse_tg_link(link)

    bot = parsed.get("bot") or parsed.get("channel")
    if not bot:
        print(f"{C.R}❌ Неверная ссылка на бота{C.RST}")
        return
    start_param = parsed.get("start_param", "")
    if not start_param:
        start_param = ask("Start параметр (пусто = просто /start): ", "")
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_start_bot,
        task_name="🤖 Старт бота",
        bot=bot,
        start_param=start_param
    )

# ─────────────────────────────────────────────────────────────
# 11. СЦЕНАРИЙ БОТА ИЗ JSON
# ─────────────────────────────────────────────────────────────

async def task_bot_scenario(client, session_name, **kw):
    """
    JSON формат:
    {
      "bot": "@botusername",
      "steps": [
        {"action": "send", "text": "/start"},
        {"action": "wait", "seconds": 2},
        {"action": "send", "text": "Hello"},
        {"action": "click_button", "index": 0},
        {"action": "wait", "seconds": 1}
      ]
    }
    """
    scenario = kw["scenario"]
    bot = scenario["bot"]
    entity = await client.get_entity(bot)

    for step in scenario.get("steps", []):
        action = step.get("action", "")
        if action == "send":
            await client.send_message(entity, step["text"])
        elif action == "wait":
            await asyncio.sleep(step.get("seconds", 1))
        elif action == "click_button":
            # Получаем последнее сообщение от бота
            msgs = await client.get_messages(entity, limit=1)
            if msgs and msgs[0].reply_markup:
                buttons = []
                for row in msgs[0].reply_markup.rows:
                    for btn in row.buttons:
                        buttons.append(btn)
                idx = step.get("index", 0)
                if idx < len(buttons) and isinstance(buttons[idx], KeyboardButtonCallback):
                    await client(GetBotCallbackAnswerRequest(
                        peer=entity,
                        msg_id=msgs[0].id,
                        data=buttons[idx].data
                    ))
        elif action == "start":
            param = step.get("param", "")
            if param:
                await client(StartBotRequest(bot=entity, peer=entity, start_param=param))
            else:
                await client.send_message(entity, "/start")
        await human_delay(0.5, 1.5)

async def action_bot_scenario():
    print(f"\n{C.Y}  Файлы сценариев в папке scenarios/:{C.RST}")
    files = list(SCENARIOS_DIR.glob("*.json"))
    if not files:
        print(f"{C.R}  Нет JSON файлов в scenarios/{C.RST}")
        print(f"{C.DIM}  Создай файл формата:")
        print(f'  {{"bot":"@botname","steps":[{{"action":"send","text":"/start"}}]}}{C.RST}')
        return
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    idx = ask_int("Номер файла: ", 1) - 1
    if idx < 0 or idx >= len(files):
        return

    with open(files[idx]) as f:
        scenario = json.load(f)

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_bot_scenario,
        task_name="📋 Сценарий бота",
        scenario=scenario
    )

# ─────────────────────────────────────────────────────────────
# 12. WEBAPP + STARTAPP
# ─────────────────────────────────────────────────────────────

async def task_webapp(client, session_name, **kw):
    bot = kw["bot"]
    startapp = kw.get("startapp", "")
    url = kw.get("url", "")

    entity = await client.get_entity(bot)

    if startapp:
        await client(StartBotRequest(
            bot=entity, peer=entity, start_param=startapp
        ))
    await human_delay(1.0, 2.0)

    # Запрос WebView если есть URL
    if url:
        try:
            await client(RequestWebViewRequest(
                peer=entity,
                bot=entity,
                url=url,
                platform="android",
            ))
        except Exception:
            pass
    await human_delay(1.0, 2.0)

async def action_webapp():
    link = ask("Ссылка (t.me/bot?startapp=param или t.me/bot/app): ")
    parsed = parse_tg_link(link)
    bot = parsed.get("bot") or parsed.get("channel")
    if not bot:
        print(f"{C.R}❌ Неверная ссылка{C.RST}")
        return
    startapp = parsed.get("startapp", "")
    if not startapp:
        startapp = ask("Startapp параметр (пусто = без параметра): ")
    url = ask("URL WebApp (пусто = пропустить): ")
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_webapp,
        task_name="🌐 WebApp",
        bot=bot, startapp=startapp, url=url
    )

# ─────────────────────────────────────────────────────────────
# 13. РАССЫЛКА В ЛС
# ─────────────────────────────────────────────────────────────

async def task_send_dm(client, session_name, **kw):
    usernames = kw["usernames"]
    message = kw["message"]
    media_path = kw.get("media_path")

    for username in usernames:
        try:
            entity = await client.get_entity(username)
            if media_path and os.path.exists(media_path):
                await client.send_file(entity, media_path, caption=message)
            else:
                await client.send_message(entity, message)
            await human_delay(3.0, 8.0)
        except Exception as e:
            print(f"  {C.R}  ↳ {session_name} -> {username}: {e}{C.RST}")

async def action_send_dm():
    print(f"{C.Y}  Введи юзернеймы (по одному на строку, пустая = конец):{C.RST}")
    usernames = []
    while True:
        u = input("  @").strip().lstrip("@")
        if not u:
            break
        usernames.append(u)
    if not usernames:
        # Или из файла
        file_path = ask("Или путь к файлу с юзернеймами: ")
        if file_path and os.path.exists(file_path):
            with open(file_path) as f:
                usernames = [l.strip().lstrip("@") for l in f if l.strip()]
    if not usernames:
        print(f"{C.R}❌ Нет юзернеймов{C.RST}")
        return
    message = ask("Сообщение: ")
    media_path = ask("Путь к медиа (пусто = без медиа): ")
    sessions = select_sessions()
    if not sessions:
        return

    # Распределяем юзернеймов по сессиям
    chunk_size = max(1, len(usernames) // len(sessions))
    chunks = [usernames[i:i+chunk_size] for i in range(0, len(usernames), chunk_size)]

    for i, session_name in enumerate(sessions):
        if i >= len(chunks):
            break
        chunk = chunks[i]
        proxies = load_proxies()
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)
        if not await safe_connect(client, session_name):
            continue
        try:
            await task_send_dm(client, session_name,
                             usernames=chunk, message=message,
                             media_path=media_path if media_path else None)
            print(f"  {C.G}✅ {session_name} — отправлено {len(chunk)} сообщ.{C.RST}")
        except Exception as e:
            print(f"  {C.R}❌ {session_name} — {e}{C.RST}")
        finally:
            await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 14. ИНВАЙТ
# ─────────────────────────────────────────────────────────────

async def task_invite(client, session_name, **kw):
    target_channel = kw["target_channel"]
    usernames = kw["usernames"]

    entity = await resolve_channel(client, target_channel)

    for username in usernames:
        try:
            user = await client.get_entity(username)
            await client(InviteToChannelRequest(
                channel=entity,
                users=[user]
            ))
            await human_delay(5.0, 15.0)
        except FloodWaitError as e:
            print(f"  {C.Y}  ↳ FloodWait {e.seconds}s{C.RST}")
            if e.seconds < 60:
                await asyncio.sleep(e.seconds)
            else:
                break
        except Exception as e:
            print(f"  {C.R}  ↳ {username}: {e}{C.RST}")

async def action_invite():
    target = ask("Канал/группа для инвайта (@username): ")
    parsed = parse_tg_link(target)
    if not parsed["channel"]:
        print(f"{C.R}❌ Неверный канал{C.RST}")
        return
    print(f"{C.Y}  Юзернеймы для инвайта (по одному, пустая = конец):{C.RST}")
    usernames = []
    while True:
        u = input("  @").strip().lstrip("@")
        if not u:
            break
        usernames.append(u)
    if not usernames:
        file_path = ask("Файл с юзернеймами: ")
        if file_path and os.path.exists(file_path):
            with open(file_path) as f:
                usernames = [l.strip().lstrip("@") for l in f if l.strip()]
    if not usernames:
        return
    sessions = select_sessions()
    if not sessions:
        return

    chunk_size = max(1, len(usernames) // len(sessions))
    chunks = [usernames[i:i+chunk_size] for i in range(0, len(usernames), chunk_size)]

    for i, session_name in enumerate(sessions):
        if i >= len(chunks):
            break
        proxies = load_proxies()
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)
        if not await safe_connect(client, session_name):
            continue
        try:
            await task_invite(client, session_name,
                            target_channel=parsed["channel"],
                            usernames=chunks[i])
        except Exception as e:
            print(f"  {C.R}❌ {session_name} — {e}{C.RST}")
        finally:
            await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 15. ОТПРАВКА С МЕДИА + MARKDOWN
# ─────────────────────────────────────────────────────────────

async def task_send_message(client, session_name, **kw):
    target = kw["target"]
    message = kw["message"]
    media_path = kw.get("media_path")
    parse_mode = kw.get("parse_mode", "md")

    entity = await client.get_entity(target)

    if media_path and os.path.exists(media_path):
        await client.send_file(
            entity, media_path,
            caption=message,
            parse_mode=parse_mode
        )
    else:
        await client.send_message(
            entity, message,
            parse_mode=parse_mode
        )
    await human_delay(0.5, 1.5)

async def action_send_message():
    target = ask("Куда отправить (@username/id): ")
    message = ask("Сообщение (Markdown): ")
    media_path = ask("Путь к файлу/фото (пусто = без медиа): ")
    print(f"{C.Y}  Формат: 1=Markdown, 2=HTML{C.RST}")
    fmt = ask_int("Формат: ", 1)
    parse_mode = "md" if fmt == 1 else "html"

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_send_message,
        task_name="📝 Отправка сообщения",
        target=target, message=message,
        media_path=media_path if media_path else None,
        parse_mode=parse_mode
    )

# ─────────────────────────────────────────────────────────────
# 16. ОТЛОЖЕННАЯ ОТПРАВКА
# ─────────────────────────────────────────────────────────────

async def task_scheduled_send(client, session_name, **kw):
    target = kw["target"]
    message = kw["message"]
    schedule_time = kw["schedule_time"]

    entity = await client.get_entity(target)
    await client.send_message(
        entity, message,
        schedule=schedule_time
    )

async def action_scheduled_send():
    target = ask("Куда (@username): ")
    message = ask("Сообщение: ")
    minutes = ask_int("Через сколько минут: ", 5)
    schedule_time = datetime.now() + timedelta(minutes=minutes)
    print(f"{C.G}  Запланировано на: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}{C.RST}")

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_scheduled_send,
        task_name="⏰ Отложенная отправка",
        target=target, message=message,
        schedule_time=schedule_time
    )

# ─────────────────────────────────────────────────────────────
# 17. РЕДАКТИРОВАНИЕ СООБЩЕНИЯ
# ─────────────────────────────────────────────────────────────

async def task_edit_message(client, session_name, **kw):
    target = kw["target"]
    msg_id = kw["msg_id"]
    new_text = kw["new_text"]

    entity = await client.get_entity(target)
    await client.edit_message(entity, msg_id, new_text)

async def action_edit_message():
    target = ask("Канал/чат (@username): ")
    msg_id = ask_int("ID сообщения: ")
    new_text = ask("Новый текст: ")
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_edit_message,
        task_name="✏️ Редактирование",
        target=target, msg_id=msg_id, new_text=new_text
    )

# ─────────────────────────────────────────────────────────────
# 18. ЗАКРЕП/ОТКРЕП
# ─────────────────────────────────────────────────────────────

async def task_pin_message(client, session_name, **kw):
    target = kw["target"]
    msg_id = kw["msg_id"]
    unpin = kw.get("unpin", False)

    entity = await client.get_entity(target)
    await client.pin_message(entity, msg_id, notify=False)

async def task_unpin_message(client, session_name, **kw):
    target = kw["target"]
    msg_id = kw.get("msg_id")
    entity = await client.get_entity(target)
    await client.unpin_message(entity, msg_id)

async def action_pin_unpin():
    target = ask("Канал/чат: ")
    msg_id = ask_int("ID сообщения: ")
    print(f"  1. Закрепить  2. Открепить")
    choice = ask_int("Выбор: ", 1)
    sessions = select_sessions()
    if not sessions:
        return
    if choice == 1:
        await execute_on_sessions(
            sessions, task_pin_message,
            task_name="📌 Закрепление",
            target=target, msg_id=msg_id
        )
    else:
        await execute_on_sessions(
            sessions, task_unpin_message,
            task_name="📌 Открепление",
            target=target, msg_id=msg_id
        )

# ─────────────────────────────────────────────────────────────
# 19. УДАЛИТЬ СВОИ СООБЩЕНИЯ
# ─────────────────────────────────────────────────────────────

async def task_delete_own_messages(client, session_name, **kw):
    target = kw["target"]
    limit = kw.get("limit", 100)

    entity = await client.get_entity(target)
    me = await client.get_me()

    deleted = 0
    async for msg in client.iter_messages(entity, limit=limit, from_user=me):
        try:
            await msg.delete()
            deleted += 1
            await human_delay(0.1, 0.3)
        except Exception:
            pass
    print(f"  {C.DIM}  ↳ {session_name}: удалено {deleted}{C.RST}")

async def action_delete_own():
    target = ask("Канал/чат: ")
    limit = ask_int("Макс. кол-во: ", 100)
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_delete_own_messages,
        task_name="🗑 Удаление своих сообщений",
        target=target, limit=limit
    )

# ─────────────────────────────────────────────────────────────
# 20. СОЗДАТЬ КАНАЛ/ГРУППУ
# ─────────────────────────────────────────────────────────────

async def task_create_channel(client, session_name, **kw):
    title = kw["title"]
    about = kw.get("about", "")
    megagroup = kw.get("megagroup", False)

    result = await client(CreateChannelRequest(
        title=title,
        about=about,
        megagroup=megagroup
    ))
    channel = result.chats[0]
    print(f"  {C.G}  ↳ {session_name}: создан {'группа' if megagroup else 'канал'} "
          f"id={channel.id}{C.RST}")

async def action_create_channel():
    title = ask("Название: ")
    about = ask("Описание: ", "")
    print(f"  1. Канал  2. Группа (мегагруппа)")
    ch = ask_int("Тип: ", 1)
    megagroup = ch == 2
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_create_channel,
        task_name="➕ Создание канала/группы",
        title=title, about=about, megagroup=megagroup
    )

# ─────────────────────────────────────────────────────────────
# 21. НАСТРОЙКА КАНАЛА
# ─────────────────────────────────────────────────────────────

async def task_setup_channel(client, session_name, **kw):
    target = kw["target"]
    entity = await resolve_channel(client, target)
    channel = await client.get_input_entity(entity)

    new_title = kw.get("new_title")
    new_about = kw.get("new_about")
    new_username = kw.get("new_username")
    photo_path = kw.get("photo_path")

    if new_title:
        await client(EditTitleRequest(channel=channel, title=new_title))
    if new_about:
        from telethon.tl.functions.channels import EditAboutRequest  # noqa
        # Используем messages.editChatAbout через прямой вызов
        await client(functions.messages.EditChatAboutRequest(
            peer=entity, about=new_about
        ))
    if new_username:
        await client(UpdateUsernameRequest(username=new_username))
    if photo_path and os.path.exists(photo_path):
        photo = await client.upload_file(photo_path)
        await client(EditPhotoRequest(
            channel=channel,
            photo=types.InputChatUploadedPhoto(file=photo)
        ))

async def action_setup_channel():
    target = ask("Канал (@username): ")
    new_title = ask("Новое название (пусто = не менять): ")
    new_about = ask("Новое описание (пусто = не менять): ")
    new_username = ask("Новый username (пусто = не менять): ")
    photo_path = ask("Путь к фото (пусто = не менять): ")

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_setup_channel,
        task_name="⚙️ Настройка канала",
        target=target,
        new_title=new_title if new_title else None,
        new_about=new_about if new_about else None,
        new_username=new_username if new_username else None,
        photo_path=photo_path if photo_path else None
    )

# ─────────────────────────────────────────────────────────────
# 22. НАЗНАЧИТЬ АДМИНА
# ─────────────────────────────────────────────────────────────

async def task_promote_admin(client, session_name, **kw):
    target = kw["target"]
    user = kw["user"]
    rights = kw["rights"]

    entity = await resolve_channel(client, target)
    user_entity = await client.get_entity(user)

    await client(EditAdminRequest(
        channel=entity,
        user_id=user_entity,
        admin_rights=rights,
        rank=kw.get("rank", "Admin")
    ))

async def action_promote_admin():
    target = ask("Канал (@username): ")
    user = ask("Юзер для назначения (@username): ")
    rank = ask("Титул (Admin): ", "Admin")

    print(f"\n{C.Y}  Выбери права:{C.RST}")
    print(f"  1. Полные права")
    print(f"  2. Только посты")
    print(f"  3. Модератор (бан, удаление)")
    print(f"  4. Кастомные")
    ch = ask_int("Выбор: ", 1)

    if ch == 1:
        rights = ChatAdminRights(
            change_info=True, post_messages=True, edit_messages=True,
            delete_messages=True, ban_users=True, invite_users=True,
            pin_messages=True, add_admins=True, manage_call=True
        )
    elif ch == 2:
        rights = ChatAdminRights(post_messages=True, edit_messages=True)
    elif ch == 3:
        rights = ChatAdminRights(
            delete_messages=True, ban_users=True, pin_messages=True
        )
    else:
        print(f"  {C.DIM}Введи y/n для каждого права:{C.RST}")
        rights = ChatAdminRights(
            change_info=ask("change_info (y/n): ", "n") == "y",
            post_messages=ask("post_messages (y/n): ", "n") == "y",
            edit_messages=ask("edit_messages (y/n): ", "n") == "y",
            delete_messages=ask("delete_messages (y/n): ", "n") == "y",
            ban_users=ask("ban_users (y/n): ", "n") == "y",
            invite_users=ask("invite_users (y/n): ", "n") == "y",
            pin_messages=ask("pin_messages (y/n): ", "n") == "y",
            add_admins=ask("add_admins (y/n): ", "n") == "y",
            manage_call=ask("manage_call (y/n): ", "n") == "y",
        )

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_promote_admin,
        task_name="👑 Назначение админа",
        target=target, user=user, rights=rights, rank=rank
    )

# ─────────────────────────────────────────────────────────────
# 23. МАССОВЫЙ БАН/КИК
# ─────────────────────────────────────────────────────────────

async def task_ban_users(client, session_name, **kw):
    target = kw["target"]
    usernames = kw["usernames"]
    kick_only = kw.get("kick_only", False)

    entity = await resolve_channel(client, target)

    ban_rights = ChatBannedRights(
        until_date=None if not kick_only else timedelta(seconds=30),
        view_messages=True,
        send_messages=True,
        send_media=True
    )

    for username in usernames:
        try:
            user = await client.get_entity(username)
            await client(EditBannedRequest(
                channel=entity,
                participant=user,
                banned_rights=ban_rights
            ))
            if kick_only:
                # Разбан через секунду (кик)
                await asyncio.sleep(1)
                await client(EditBannedRequest(
                    channel=entity,
                    participant=user,
                    banned_rights=ChatBannedRights(until_date=None)
                ))
            await human_delay(0.3, 0.8)
        except Exception as e:
            print(f"  {C.R}  ↳ {username}: {e}{C.RST}")

async def action_ban_kick():
    target = ask("Канал/группа: ")
    print(f"  1. Бан  2. Кик")
    mode = ask_int("Режим: ", 1)
    print(f"{C.Y}  Юзернеймы (по одному, пустая = конец):{C.RST}")
    usernames = []
    while True:
        u = input("  @").strip().lstrip("@")
        if not u:
            break
        usernames.append(u)
    if not usernames:
        file_path = ask("Файл: ")
        if file_path and os.path.exists(file_path):
            with open(file_path) as f:
                usernames = [l.strip().lstrip("@") for l in f if l.strip()]
    if not usernames:
        return
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions[:1], task_ban_users,
        task_name="🔨 Бан/кик",
        target=target, usernames=usernames,
        kick_only=(mode == 2)
    )

# ─────────────────────────────────────────────────────────────
# 24. ОЧИСТКА КАНАЛА
# ─────────────────────────────────────────────────────────────

async def task_clear_channel(client, session_name, **kw):
    target = kw["target"]
    entity = await resolve_channel(client, target)

    deleted = 0
    async for msg in client.iter_messages(entity, limit=None):
        try:
            await msg.delete()
            deleted += 1
            if deleted % 100 == 0:
                print(f"  {C.DIM}  ↳ удалено {deleted}...{C.RST}")
                await asyncio.sleep(0.5)
        except Exception:
            pass
    print(f"  {C.G}  ↳ Всего удалено: {deleted}{C.RST}")

async def action_clear_channel():
    target = ask("Канал для очистки: ")
    confirm = ask(f"⚠️ Удалить ВСЕ посты из {target}? (yes/no): ")
    if confirm.lower() != "yes":
        print(f"{C.Y}  Отменено{C.RST}")
        return
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions[:1], task_clear_channel,
        task_name="🧹 Очистка канала",
        target=target
    )

# ─────────────────────────────────────────────────────────────
# 25. КОПИРОВАТЬ НАСТРОЙКИ КАНАЛА
# ─────────────────────────────────────────────────────────────

async def task_copy_channel(client, session_name, **kw):
    source = kw["source"]
    dest = kw["dest"]

    src_entity = await resolve_channel(client, source)
    dst_entity = await resolve_channel(client, dest)
    dst_input = await client.get_input_entity(dst_entity)

    full = await client(GetFullChannelRequest(src_entity))

    # Копируем title
    await client(EditTitleRequest(channel=dst_input, title=src_entity.title))
    # Копируем about
    if full.full_chat.about:
        await client(functions.messages.EditChatAboutRequest(
            peer=dst_entity, about=full.full_chat.about
        ))
    # Копируем фото
    if src_entity.photo:
        photo = await client.download_profile_photo(src_entity, file=bytes)
        if photo:
            uploaded = await client.upload_file(photo)
            await client(EditPhotoRequest(
                channel=dst_input,
                photo=types.InputChatUploadedPhoto(file=uploaded)
            ))

async def action_copy_channel():
    source = ask("Исходный канал (@source): ")
    dest = ask("Целевой канал (@dest): ")
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions[:1], task_copy_channel,
        task_name="📋 Копирование настроек",
        source=source, dest=dest
    )

# ─────────────────────────────────────────────────────────────
# 26. РЕПОРТ НА ЮЗЕРА/КАНАЛ
# ─────────────────────────────────────────────────────────────

REPORT_REASONS = {
    1: ("Спам", InputReportReasonSpam()),
    2: ("Насилие", InputReportReasonViolence()),
    3: ("Порнография", InputReportReasonPornography()),
    4: ("Детское насилие", InputReportReasonChildAbuse()),
    5: ("Наркотики", InputReportReasonIllegalDrugs()),
    6: ("Фейк", InputReportReasonFake()),
    7: ("Геонерелевант", InputReportReasonGeoIrrelevant()),
    8: ("Другое", InputReportReasonOther()),
}

async def task_report_channel(client, session_name, **kw):
    target = kw["target"]
    reason = kw["reason"]
    message = kw.get("message", "")

    entity = await resolve_channel(client, target)

    # Получаем последние сообщения для репорта
    msgs = await client.get_messages(entity, limit=5)
    msg_ids = [m.id for m in msgs if m]

    if msg_ids:
        await client(ReportRequest(
            peer=entity,
            id=msg_ids,
            reason=reason,
            message=message
        ))
    await human_delay(1.0, 2.0)

async def action_report_channel():
    target = ask("Канал/юзер для репорта: ")
    print(f"\n{C.Y}  Причины:{C.RST}")
    for k, (name, _) in REPORT_REASONS.items():
        print(f"  {k}. {name}")
    reason_idx = ask_int("Причина: ", 1)
    reason = REPORT_REASONS.get(reason_idx, REPORT_REASONS[8])[1]
    message = ask("Комментарий к репорту: ", "")
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_report_channel,
        task_name="🚨 Репорт",
        target=target, reason=reason, message=message
    )

# ─────────────────────────────────────────────────────────────
# 27. РЕПОРТ НА СООБЩЕНИЕ
# ─────────────────────────────────────────────────────────────

async def task_report_message(client, session_name, **kw):
    channel = kw["channel"]
    post_id = kw["post_id"]
    reason = kw["reason"]
    message = kw.get("message", "")

    entity = await resolve_channel(client, channel)
    await client(ReportRequest(
        peer=entity,
        id=[post_id],
        reason=reason,
        message=message
    ))
    await human_delay(1.0, 2.0)

async def action_report_message():
    link = ask("Ссылка на сообщение: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"] or not parsed["post_id"]:
        print(f"{C.R}❌ Нужна ссылка на конкретное сообщение{C.RST}")
        return
    print(f"\n{C.Y}  Причины:{C.RST}")
    for k, (name, _) in REPORT_REASONS.items():
        print(f"  {k}. {name}")
    reason_idx = ask_int("Причина: ", 1)
    reason = REPORT_REASONS.get(reason_idx, REPORT_REASONS[8])[1]
    message = ask("Комментарий: ", "")
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_report_message,
        task_name="🚨 Репорт на сообщение",
        channel=parsed["channel"],
        post_id=parsed["post_id"],
        reason=reason, message=message
    )

# ─────────────────────────────────────────────────────────────
# 28. МАССОВАЯ БЛОКИРОВКА
# ─────────────────────────────────────────────────────────────

async def task_block_user(client, session_name, **kw):
    usernames = kw["usernames"]
    for username in usernames:
        try:
            user = await client.get_entity(username)
            await client(functions.contacts.BlockRequest(id=user))
            await human_delay(0.3, 0.8)
        except Exception as e:
            print(f"  {C.R}  ↳ {username}: {e}{C.RST}")

async def action_block_users():
    print(f"{C.Y}  Юзернеймы для блокировки (пустая = конец):{C.RST}")
    usernames = []
    while True:
        u = input("  @").strip().lstrip("@")
        if not u:
            break
        usernames.append(u)
    if not usernames:
        return
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_block_user,
        task_name="🚫 Массовая блокировка",
        usernames=usernames
    )

# ─────────────────────────────────────────────────────────────
# 29. ПАРСЕР УЧАСТНИКОВ
# ─────────────────────────────────────────────────────────────

async def action_parse_members():
    target = ask("Канал/группа: ")
    parsed = parse_tg_link(target)
    if not parsed["channel"]:
        print(f"{C.R}❌ Неверный канал{C.RST}")
        return
    limit = ask_int("Макс. кол-во: ", 1000)

    sessions = get_sessions()
    if not sessions:
        print(f"{C.R}❌ Нет сессий{C.RST}")
        return

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    try:
        entity = await resolve_channel(client, parsed["channel"])
        members = []
        offset = 0
        batch = 200

        while len(members) < limit:
            participants = await client(GetParticipantsRequest(
                channel=entity,
                filter=ChannelParticipantsSearch(""),
                offset=offset,
                limit=min(batch, limit - len(members)),
                hash=0
            ))
            if not participants.users:
                break
            for user in participants.users:
                info = {
                    "id": user.id,
                    "username": user.username or "",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "phone": user.phone or "",
                    "bot": user.bot,
                }
                members.append(info)
            offset += len(participants.users)
            if len(participants.users) < batch:
                break

        # Сохраняем
        filename = f"members_{parsed['channel']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=2)

        # Также txt с юзернеймами
        txt_file = filename.replace(".json", ".txt")
        with open(txt_file, "w") as f:
            for m in members:
                if m["username"]:
                    f.write(f"@{m['username']}\n")

        print(f"\n{C.G}✅ Спарсено: {len(members)} участников{C.RST}")
        print(f"  JSON: {filename}")
        print(f"  TXT:  {txt_file}")

    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 30. СТАТИСТИКА КАНАЛА
# ─────────────────────────────────────────────────────────────

async def action_channel_stats():
    target = ask("Канал: ")
    parsed = parse_tg_link(target)
    if not parsed["channel"]:
        return

    sessions = get_sessions()
    if not sessions:
        return

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    try:
        entity = await resolve_channel(client, parsed["channel"])
        full = await client(GetFullChannelRequest(entity))

        print(f"\n{C.CY}{'═'*50}")
        print(f"  📊 Статистика: {entity.title}")
        print(f"{'═'*50}{C.RST}")
        print(f"  ID:           {entity.id}")
        print(f"  Username:     @{entity.username or 'нет'}")
        print(f"  Подписчики:   {format_count(full.full_chat.participants_count or 0)}")
        print(f"  Описание:     {(full.full_chat.about or '')[:100]}")
        print(f"  Создатель:    {'Да' if entity.creator else 'Нет'}")
        print(f"  Мегагруппа:   {'Да' if entity.megagroup else 'Нет'}")

        # Последние посты
        msgs = await client.get_messages(entity, limit=10)
        if msgs:
            total_views = sum(m.views or 0 for m in msgs)
            avg_views = total_views // len(msgs) if msgs else 0
            print(f"  Ср. просмотры: {format_count(avg_views)} (10 постов)")

        print(f"{C.CY}{'═'*50}{C.RST}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 31. СКАЧИВАНИЕ МЕДИА
# ─────────────────────────────────────────────────────────────

async def action_download_media():
    link = ask("Ссылка на пост или канал: ")
    parsed = parse_tg_link(link)
    if not parsed["channel"]:
        return

    limit = 1
    if parsed["post_id"]:
        limit = 1
    else:
        limit = ask_int("Кол-во последних постов: ", 10)

    output_dir = ask("Папка для сохранения: ", "downloads")
    os.makedirs(output_dir, exist_ok=True)

    sessions = get_sessions()
    if not sessions:
        return

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    try:
        entity = await resolve_channel(client, parsed["channel"])
        downloaded = 0

        if parsed["post_id"]:
            msg = await client.get_messages(entity, ids=parsed["post_id"])
            if msg and msg.media:
                path = await client.download_media(msg, file=output_dir)
                print(f"  {C.G}📥 {path}{C.RST}")
                downloaded += 1
        else:
            async for msg in client.iter_messages(entity, limit=limit):
                if msg.media:
                    try:
                        path = await client.download_media(msg, file=output_dir)
                        print(f"  {C.G}📥 {path}{C.RST}")
                        downloaded += 1
                    except Exception:
                        pass

        print(f"\n{C.G}✅ Скачано: {downloaded} файлов{C.RST}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 32. МОНИТОРИНГ (авто-реакции на новые посты)
# ─────────────────────────────────────────────────────────────

async def action_monitor():
    target = ask("Канал для мониторинга: ")
    parsed = parse_tg_link(target)
    if not parsed["channel"]:
        return
    reaction = ask_reaction()
    do_view = ask("Автопросмотр? (y/n): ", "y") == "y"

    sessions = get_sessions()
    if not sessions:
        return

    print(f"\n{C.G}👀 Мониторинг запущен. Ctrl+C для остановки{C.RST}")

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    try:
        entity = await resolve_channel(client, parsed["channel"])

        @client.on(events.NewMessage(chats=entity))
        async def handler(event):
            msg = event.message
            print(f"  {C.CY}📨 Новый пост #{msg.id}{C.RST}")

            if do_view:
                await client(GetMessagesViewsRequest(
                    peer=entity, id=[msg.id], increment=True
                ))

            react_obj = ReactionEmoji(emoticon=reaction)
            try:
                await client(SendReactionRequest(
                    peer=entity, msg_id=msg.id,
                    reaction=[react_obj]
                ))
                print(f"  {C.G}  ✅ Реакция {reaction} поставлена{C.RST}")
            except Exception as e:
                print(f"  {C.R}  ❌ {e}{C.RST}")

        await client.run_until_disconnected()
    except KeyboardInterrupt:
        print(f"\n{C.Y}⏹ Мониторинг остановлен{C.RST}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 33. АВТО-ОТВЕТЧИК ПО КЛЮЧЕВЫМ СЛОВАМ
# ─────────────────────────────────────────────────────────────

async def action_auto_responder():
    print(f"{C.Y}  Введи пары: ключевое_слово -> ответ (пустая = конец):{C.RST}")
    rules = {}
    while True:
        keyword = ask("Ключевое слово: ")
        if not keyword:
            break
        response = ask("Ответ: ")
        rules[keyword.lower()] = response

    if not rules:
        print(f"{C.R}❌ Нет правил{C.RST}")
        return

    sessions = get_sessions()
    if not sessions:
        return

    print(f"\n{C.G}🤖 Авто-ответчик запущен. Ctrl+C для остановки{C.RST}")
    print(f"  Правила: {len(rules)}")

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    try:
        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            if not event.message or not event.message.text:
                return
            text = event.message.text.lower()
            for keyword, response in rules.items():
                if keyword in text:
                    await event.reply(response)
                    print(f"  {C.G}↩️ Ответил на '{keyword}'{C.RST}")
                    break

        await client.run_until_disconnected()
    except KeyboardInterrupt:
        print(f"\n{C.Y}⏹ Авто-ответчик остановлен{C.RST}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 34. АВТО-ПОСТИНГ
# ─────────────────────────────────────────────────────────────

async def action_auto_posting():
    target = ask("Канал для постинга (@username): ")
    parsed = parse_tg_link(target)
    if not parsed["channel"]:
        return

    print(f"{C.Y}  Введи посты (каждый с новой строки, пустая = конец):{C.RST}")
    posts = []
    while True:
        p = input("  > ").strip()
        if not p:
            break
        posts.append(p)
    if not posts:
        return

    interval = ask_int("Интервал (минуты): ", 60)

    sessions = get_sessions()
    if not sessions:
        return

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    print(f"\n{C.G}📝 Авто-постинг запущен. Ctrl+C для остановки{C.RST}")
    print(f"  Постов: {len(posts)} | Интервал: {interval} мин")

    try:
        entity = await resolve_channel(client, parsed["channel"])
        idx = 0
        while True:
            post = posts[idx % len(posts)]
            await client.send_message(entity, post)
            print(f"  {C.G}📤 Пост #{idx+1}: {post[:50]}...{C.RST}")
            idx += 1
            await asyncio.sleep(interval * 60)
    except KeyboardInterrupt:
        print(f"\n{C.Y}⏹ Авто-постинг остановлен{C.RST}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 35. ЗАДАЧИ ИЗ JSON
# ─────────────────────────────────────────────────────────────

async def action_tasks_from_json():
    """
    Формат JSON:
    {
      "tasks": [
        {"action": "subscribe", "channel": "@test"},
        {"action": "view", "link": "t.me/test/123"},
        {"action": "react", "link": "t.me/test/123", "reaction": "👍"},
        {"action": "comment", "link": "t.me/test/123", "text": "Nice!"},
        {"action": "start_bot", "bot": "@bot", "param": "ref123"},
        {"action": "delay", "seconds": 5}
      ]
    }
    """
    file_path = ask("Путь к JSON файлу с задачами: ")
    if not file_path or not os.path.exists(file_path):
        print(f"{C.R}❌ Файл не найден{C.RST}")
        return

    with open(file_path) as f:
        data = json.load(f)

    tasks_list = data.get("tasks", [])
    if not tasks_list:
        print(f"{C.R}❌ Нет задач{C.RST}")
        return

    sessions = select_sessions()
    if not sessions:
        return

    proxies = load_proxies()

    print(f"\n{C.G}📋 Выполняю {len(tasks_list)} задач на {len(sessions)} сессиях{C.RST}")

    for i, session_name in enumerate(sessions):
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)
        if not await safe_connect(client, session_name):
            continue

        try:
            for task in tasks_list:
                action = task.get("action", "")
                try:
                    if action == "subscribe":
                        p = parse_tg_link(task.get("channel", ""))
                        entity = await resolve_channel(client, p["channel"])
                        await client(JoinChannelRequest(entity))

                    elif action == "view":
                        p = parse_tg_link(task.get("link", ""))
                        entity = await resolve_channel(client, p["channel"])
                        await client(GetMessagesViewsRequest(
                            peer=entity, id=[p["post_id"]], increment=True
                        ))

                    elif action == "react":
                        p = parse_tg_link(task.get("link", ""))
                        entity = await resolve_channel(client, p["channel"])
                        r = ReactionEmoji(emoticon=task.get("reaction", "👍"))
                        await client(SendReactionRequest(
                            peer=entity, msg_id=p["post_id"], reaction=[r]
                        ))

                    elif action == "comment":
                        p = parse_tg_link(task.get("link", ""))
                        entity = await resolve_channel(client, p["channel"])
                        await client.send_message(
                            entity, task.get("text", "👍"),
                            comment_to=p["post_id"]
                        )

                    elif action == "start_bot":
                        bot_entity = await client.get_entity(task["bot"])
                        param = task.get("param", "")
                        if param:
                            await client(StartBotRequest(
                                bot=bot_entity, peer=bot_entity, start_param=param
                            ))
                        else:
                            await client.send_message(bot_entity, "/start")

                    elif action == "delay":
                        await asyncio.sleep(task.get("seconds", 1))

                    print(f"  {C.G}  ✅ {session_name}: {action}{C.RST}")
                except Exception as e:
                    print(f"  {C.R}  ❌ {session_name}: {action} — {e}{C.RST}")

                await human_delay(1.0, 3.0)

        finally:
            await client.disconnect()

    print(f"\n{C.G}✅ Все задачи выполнены{C.RST}")

# ═══════════════════════════════════════════════════════════════
# КОНЕЦ ЧАСТИ 2
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# ЧАСТЬ 3 — ФУНКЦИИ 36-50 + ГЛАВНЫЙ ЦИКЛ
# ═══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# 36. ПРОГРЕВ (чтение, скролл, профили)
# ─────────────────────────────────────────────────────────────

async def task_warmup(client, session_name, **kw):
    intensity = kw.get("intensity", "medium")

    if intensity == "light":
        actions = 5
        delay_range = (3.0, 8.0)
    elif intensity == "heavy":
        actions = 25
        delay_range = (1.0, 4.0)
    else:
        actions = 12
        delay_range = (2.0, 6.0)

    me = await client.get_me()
    print(f"  {C.DIM}  ↳ {session_name}: прогрев ({intensity}, {actions} действий){C.RST}")

    dialogs = await client.get_dialogs(limit=30)
    random.shuffle(dialogs)

    action_count = 0
    for dialog in dialogs[:actions]:
        try:
            action_type = random.choice(["read", "scroll", "profile", "read", "scroll"])

            if action_type == "read":
                # Чтение последних сообщений
                msgs = await client.get_messages(dialog.entity, limit=random.randint(3, 15))
                if msgs:
                    await client(ReadHistoryRequest(
                        peer=dialog.entity,
                        max_id=msgs[0].id
                    ))
                action_count += 1

            elif action_type == "scroll":
                # Имитация скролла — загрузка сообщений пачками
                offset_id = 0
                for _ in range(random.randint(1, 4)):
                    history = await client(GetHistoryRequest(
                        peer=dialog.entity,
                        offset_id=offset_id,
                        offset_date=None,
                        add_offset=0,
                        limit=20,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    if history.messages:
                        offset_id = history.messages[-1].id
                    await asyncio.sleep(random.uniform(0.3, 1.0))
                action_count += 1

            elif action_type == "profile":
                # Просмотр профиля
                if isinstance(dialog.entity, User) and not dialog.entity.bot:
                    try:
                        await client(GetFullUserRequest(dialog.entity))
                    except Exception:
                        pass
                elif isinstance(dialog.entity, (Channel, Chat)):
                    try:
                        if hasattr(dialog.entity, 'megagroup') or hasattr(dialog.entity, 'broadcast'):
                            await client(GetFullChannelRequest(dialog.entity))
                    except Exception:
                        pass
                action_count += 1

            await asyncio.sleep(random.uniform(*delay_range))

        except FloodWaitError as e:
            await asyncio.sleep(min(e.seconds, 30))
        except Exception:
            pass

    # Имитация набора текста (в Избранное)
    try:
        saved = await client.get_entity("me")
        # Устанавливаем статус онлайн
        await client(UpdateStatusRequest(offline=False))
        await asyncio.sleep(random.uniform(2, 5))
        await client(UpdateStatusRequest(offline=True))
    except Exception:
        pass

    print(f"  {C.G}  ↳ {session_name}: выполнено {action_count} действий{C.RST}")

async def action_warmup():
    print(f"\n{C.Y}  Интенсивность прогрева:{C.RST}")
    print(f"  1. 🟢 Лёгкий (5 действий, большие паузы)")
    print(f"  2. 🟡 Средний (12 действий)")
    print(f"  3. 🔴 Тяжёлый (25 действий, малые паузы)")
    ch = ask_int("Выбор: ", 2)
    intensity = {1: "light", 2: "medium", 3: "heavy"}.get(ch, "medium")

    sessions = select_sessions("Выбери аккаунты для прогрева")
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_warmup,
        task_name="🔥 Прогрев аккаунтов",
        max_concurrent=3,
        delay_between=(2.0, 5.0),
        intensity=intensity
    )

# ─────────────────────────────────────────────────────────────
# 37. ИМИТАЦИЯ ОНЛАЙНА (параллельно)
# ─────────────────────────────────────────────────────────────

async def action_online_imitation():
    duration = ask_int("Длительность (минуты): ", 60)
    interval = ask_int("Интервал пинга (секунды): ", 30)

    sessions = select_sessions("Аккаунты для имитации онлайна")
    if not sessions:
        return

    proxies = load_proxies()
    clients = []

    print(f"\n{C.G}🟢 Запуск имитации онлайна на {len(sessions)} аккаунтах{C.RST}")
    print(f"  Длительность: {duration} мин | Интервал: {interval} сек")
    print(f"  Ctrl+C для остановки\n")

    # Подключаем все клиенты
    for i, session_name in enumerate(sessions):
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)
        if await safe_connect(client, session_name):
            clients.append((client, session_name))
            print(f"  {C.G}✅ {session_name} подключён{C.RST}")
        else:
            print(f"  {C.R}❌ {session_name} не подключился{C.RST}")

    if not clients:
        print(f"{C.R}❌ Нет подключённых клиентов{C.RST}")
        return

    end_time = time.time() + (duration * 60)

    try:
        cycle = 0
        while time.time() < end_time:
            cycle += 1
            for client, name in clients:
                try:
                    await client(UpdateStatusRequest(offline=False))
                except Exception:
                    pass

            remaining = int((end_time - time.time()) / 60)
            print(f"  {C.DIM}  Цикл {cycle} | Осталось ~{remaining} мин | "
                  f"{len(clients)} аккаунтов онлайн{C.RST}", end="\r")

            # Случайные действия для натуральности
            if cycle % 5 == 0:
                rc = random.choice(clients)
                try:
                    dialogs = await rc[0].get_dialogs(limit=3)
                    if dialogs:
                        d = random.choice(dialogs)
                        await rc[0].get_messages(d.entity, limit=3)
                except Exception:
                    pass

            await asyncio.sleep(interval + random.uniform(-5, 5))

    except KeyboardInterrupt:
        print(f"\n{C.Y}⏹ Остановка...{C.RST}")
    finally:
        for client, name in clients:
            try:
                await client(UpdateStatusRequest(offline=True))
                await client.disconnect()
            except Exception:
                pass
        print(f"\n{C.G}✅ Все аккаунты переведены в оффлайн{C.RST}")

# ─────────────────────────────────────────────────────────────
# 38. ЧЕКЕР АККАУНТОВ
# ─────────────────────────────────────────────────────────────

async def action_checker():
    sessions = get_sessions()
    if not sessions:
        print(f"{C.R}❌ Нет сессий{C.RST}")
        return

    proxies = load_proxies()
    alive = []
    dead = []
    banned = []

    print(f"\n{C.CY}{'═'*50}")
    print(f"  ✅ Чекер аккаунтов ({len(sessions)} сессий)")
    print(f"{'═'*50}{C.RST}\n")

    for i, session_name in enumerate(sessions):
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)

        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                phone = me.phone or "?"
                name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                username = f"@{me.username}" if me.username else ""
                print(f"  {C.G}✅ {session_name}: +{phone} {name} {username}{C.RST}")
                alive.append(session_name)
            else:
                print(f"  {C.Y}⚠️ {session_name}: не авторизован{C.RST}")
                dead.append(session_name)
        except (PhoneNumberBannedError, UserDeactivatedBanError, UserDeactivatedError):
            print(f"  {C.R}💀 {session_name}: ЗАБАНЕН{C.RST}")
            banned.append(session_name)
        except AuthKeyUnregisteredError:
            print(f"  {C.R}🔑 {session_name}: сессия невалидна{C.RST}")
            dead.append(session_name)
        except Exception as e:
            print(f"  {C.R}❌ {session_name}: {e}{C.RST}")
            dead.append(session_name)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    print(f"\n{C.CY}{'═'*50}")
    print(f"  📊 Результат:")
    print(f"    {C.G}✅ Живые:     {len(alive)}{C.RST}")
    print(f"    {C.R}💀 Баны:      {len(banned)}{C.RST}")
    print(f"    {C.Y}⚠️ Мёртвые:   {len(dead)}{C.RST}")
    print(f"{C.CY}{'═'*50}{C.RST}")

    if banned or dead:
        move = ask("Переместить мёртвые/баны в dead_sessions/? (y/n): ", "n")
        if move == "y":
            dead_dir = BASE_DIR / "dead_sessions"
            dead_dir.mkdir(exist_ok=True)
            for s in banned + dead:
                src = SESSIONS_DIR / f"{s}.session"
                dst = dead_dir / f"{s}.session"
                if src.exists():
                    src.rename(dst)
                    print(f"  {C.DIM}  ↳ {s} → dead_sessions/{C.RST}")

# ─────────────────────────────────────────────────────────────
# 39. АКТИВНЫЕ СЕССИИ
# ─────────────────────────────────────────────────────────────

async def action_active_sessions():
    sessions = select_sessions("Выбери аккаунты")
    if not sessions:
        return

    proxies = load_proxies()

    for i, session_name in enumerate(sessions):
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)
        if not await safe_connect(client, session_name):
            continue

        try:
            result = await client(GetAuthorizationsRequest())
            print(f"\n{C.CY}  📱 Сессии для {session_name}:{C.RST}")
            for j, auth in enumerate(result.authorizations):
                current = " 👈 ТЕКУЩАЯ" if auth.current else ""
                print(f"    {j+1}. {auth.device_model} | {auth.platform} | "
                      f"{auth.app_name} v{auth.app_version}")
                print(f"       IP: {auth.ip} | Регион: {auth.country}")
                print(f"       Создана: {auth.date_created} | "
                      f"Активна: {auth.date_active}{C.G}{current}{C.RST}")
                print(f"       Hash: {auth.hash}")
                print()
        finally:
            await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 40. СБРОС ВСЕХ СЕССИЙ
# ─────────────────────────────────────────────────────────────

async def task_reset_all_sessions(client, session_name, **kw):
    result = await client(GetAuthorizationsRequest())
    count = 0
    for auth in result.authorizations:
        if not auth.current:
            try:
                await client(ResetAuthorizationRequest(hash=auth.hash))
                count += 1
                await human_delay(0.3, 0.8)
            except Exception:
                pass
    print(f"  {C.DIM}  ↳ {session_name}: сброшено {count} сессий{C.RST}")

async def action_reset_all_sessions():
    confirm = ask("⚠️ Сбросить ВСЕ сессии (кроме текущей)? (yes/no): ")
    if confirm.lower() != "yes":
        return
    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_reset_all_sessions,
        task_name="💀 Сброс всех сессий"
    )

# ─────────────────────────────────────────────────────────────
# 41. ВЫБОРОЧНЫЙ СБРОС
# ─────────────────────────────────────────────────────────────

async def action_selective_reset():
    sessions = select_sessions("Выбери аккаунт")
    if not sessions:
        return

    proxies = load_proxies()
    proxy = proxies[0] if proxies else None
    client = await create_client(sessions[0], proxy)
    if not await safe_connect(client, sessions[0]):
        return

    try:
        result = await client(GetAuthorizationsRequest())
        auths = []
        print(f"\n{C.CY}  Сессии:{C.RST}")
        for j, auth in enumerate(result.authorizations):
            if auth.current:
                print(f"  {C.G}{j+1}. [ТЕКУЩАЯ] {auth.device_model} | {auth.app_name}{C.RST}")
            else:
                print(f"  {C.W}{j+1}. {auth.device_model} | {auth.app_name} | "
                      f"IP: {auth.ip} | {auth.date_active}{C.RST}")
            auths.append(auth)

        indices = ask("Номера для сброса (через запятую): ")
        if not indices:
            return

        for idx_str in indices.split(","):
            try:
                idx = int(idx_str.strip()) - 1
                if 0 <= idx < len(auths) and not auths[idx].current:
                    await client(ResetAuthorizationRequest(hash=auths[idx].hash))
                    print(f"  {C.G}✅ Сессия {idx+1} сброшена{C.RST}")
                elif auths[idx].current:
                    print(f"  {C.Y}⚠️ Нельзя сбросить текущую сессию{C.RST}")
            except Exception as e:
                print(f"  {C.R}❌ {e}{C.RST}")

    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 42. ЗАПРОС КОДА + 2FA (создание новой сессии)
# ─────────────────────────────────────────────────────────────

async def action_new_session():
    api_id, api_hash = get_api_credentials()
    phone = ask("Номер телефона (+79...): ")
    if not phone:
        return

    session_name = phone.replace("+", "").replace(" ", "")
    proxy_str_val = ask("Прокси (пусто = без прокси): ")
    proxy = parse_proxy(proxy_str_val) if proxy_str_val else None

    client = await create_client(session_name, proxy)
    await client.connect()

    try:
        result = await client.send_code_request(phone)
        print(f"{C.G}✅ Код отправлен{C.RST}")
        code = ask("Введи код из Telegram: ")

        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            print(f"{C.Y}🔐 Требуется 2FA пароль{C.RST}")
            password = ask("2FA пароль: ")
            await client.sign_in(password=password)

        me = await client.get_me()
        print(f"{C.G}✅ Авторизован: {me.first_name} (@{me.username or '?'}) +{me.phone}{C.RST}")

        # Перемещаем сессию в sessions/
        src = Path(f"{session_name}.session")
        dst = SESSIONS_DIR / f"{session_name}.session"
        if src.exists() and not dst.exists():
            src.rename(dst)

    except Exception as e:
        print(f"{C.R}❌ Ошибка: {e}{C.RST}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 43. ИНФО ОБ АККАУНТАХ
# ─────────────────────────────────────────────────────────────

async def task_get_info(client, session_name, **kw):
    me = await client.get_me()
    full = await client(GetFullUserRequest(me))

    print(f"\n{C.CY}  ── {session_name} ──{C.RST}")
    print(f"    ID:        {me.id}")
    print(f"    Телефон:   +{me.phone or '?'}")
    print(f"    Имя:       {me.first_name or ''} {me.last_name or ''}")
    print(f"    Username:  @{me.username or 'нет'}")
    print(f"    Бот:       {'Да' if me.bot else 'Нет'}")
    print(f"    Premium:   {'Да' if me.premium else 'Нет'}")
    print(f"    Био:       {full.full_user.about or 'нет'}")
    print(f"    Фото:      {'Есть' if me.photo else 'Нет'}")

    # Кол-во диалогов
    dialogs = await client.get_dialogs(limit=0)
    print(f"    Диалогов:  {dialogs.total if hasattr(dialogs, 'total') else '?'}")

async def action_get_info():
    sessions = select_sessions("Выбери аккаунты")
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_get_info,
        task_name="ℹ️ Информация об аккаунтах",
        max_concurrent=3
    )

# ─────────────────────────────────────────────────────────────
# 44. ИМЯ/БИО
# ─────────────────────────────────────────────────────────────

async def task_update_profile(client, session_name, **kw):
    first_name = kw.get("first_name")
    last_name = kw.get("last_name")
    about = kw.get("about")

    kwargs = {}
    if first_name is not None:
        kwargs["first_name"] = first_name
    if last_name is not None:
        kwargs["last_name"] = last_name
    if about is not None:
        kwargs["about"] = about

    if kwargs:
        await client(UpdateProfileRequest(**kwargs))

async def action_update_profile():
    first = ask("Имя (пусто = не менять): ")
    last = ask("Фамилия (пусто = не менять): ")
    about = ask("Био (пусто = не менять): ")

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_update_profile,
        task_name="✏️ Обновление профиля",
        first_name=first if first else None,
        last_name=last if last else None,
        about=about if about else None
    )

# ─────────────────────────────────────────────────────────────
# 45. ФОТО ПРОФИЛЯ
# ─────────────────────────────────────────────────────────────

async def task_set_photo(client, session_name, **kw):
    photo_path = kw["photo_path"]
    delete_old = kw.get("delete_old", False)

    if delete_old:
        photos = await client.get_profile_photos("me")
        if photos:
            await client(DeletePhotosRequest(id=[
                types.InputPhoto(
                    id=p.id,
                    access_hash=p.access_hash,
                    file_reference=p.file_reference
                ) for p in photos
            ]))

    if photo_path and os.path.exists(photo_path):
        file = await client.upload_file(photo_path)
        await client(UploadProfilePhotoRequest(file=file))

async def action_set_photo():
    photo_path = ask("Путь к фото: ")
    if not photo_path or not os.path.exists(photo_path):
        print(f"{C.R}❌ Файл не найден{C.RST}")
        return
    delete_old = ask("Удалить старые фото? (y/n): ", "n") == "y"

    sessions = select_sessions()
    if not sessions:
        return
    await execute_on_sessions(
        sessions, task_set_photo,
        task_name="🖼 Установка фото",
        photo_path=photo_path,
        delete_old=delete_old
    )

# ─────────────────────────────────────────────────────────────
# 46. 2FA (установка/смена пароля)
# ─────────────────────────────────────────────────────────────

async def action_set_2fa():
    sessions = select_sessions("Выбери аккаунт")
    if not sessions:
        return

    proxies = load_proxies()

    for i, session_name in enumerate(sessions):
        proxy = proxies[i % len(proxies)] if proxies else None
        client = await create_client(session_name, proxy)
        if not await safe_connect(client, session_name):
            continue

        try:
            # Проверяем текущий статус 2FA
            pwd = await client(GetPasswordRequest())
            has_2fa = pwd.has_password

            if has_2fa:
                print(f"  {C.Y}🔐 {session_name}: 2FA уже установлен{C.RST}")
                print(f"  1. Сменить пароль  2. Удалить 2FA  3. Пропустить")
                ch = ask_int("Выбор: ", 3)

                if ch == 1:
                    old_pwd = ask("Текущий пароль: ")
                    new_pwd = ask("Новый пароль: ")
                    hint = ask("Подсказка: ", "")
                    try:
                        await client.edit_2fa(
                            current_password=old_pwd,
                            new_password=new_pwd,
                            hint=hint
                        )
                        print(f"  {C.G}✅ Пароль изменён{C.RST}")
                    except Exception as e:
                        print(f"  {C.R}❌ {e}{C.RST}")
                elif ch == 2:
                    old_pwd = ask("Текущий пароль: ")
                    try:
                        await client.edit_2fa(
                            current_password=old_pwd,
                            new_password=None
                        )
                        print(f"  {C.G}✅ 2FA удалён{C.RST}")
                    except Exception as e:
                        print(f"  {C.R}❌ {e}{C.RST}")
            else:
                print(f"  {C.Y}🔓 {session_name}: 2FA не установлен{C.RST}")
                new_pwd = ask("Установить пароль (пусто = пропустить): ")
                if new_pwd:
                    hint = ask("Подсказка: ", "")
                    email = ask("Email для восстановления (пусто = без): ")
                    try:
                        await client.edit_2fa(
                            new_password=new_pwd,
                            hint=hint,
                            email=email if email else None
                        )
                        print(f"  {C.G}✅ 2FA установлен{C.RST}")
                    except Exception as e:
                        print(f"  {C.R}❌ {e}{C.RST}")

        finally:
            await client.disconnect()

# ─────────────────────────────────────────────────────────────
# 47. ОТПИСКА ОТ КАНАЛОВ
# ─────────────────────────────────────────────────────────────

async def task_unsubscribe_all(client, session_name, **kw):
    leave_groups = kw.get("leave_groups", False)
    whitelist = kw.get("whitelist", [])

    count = 0
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, Channel):
            # Пропускаем whitelist
            if entity.username and entity.username.lower() in [w.lower().lstrip("@") for w in whitelist]:
                continue
            if str(entity.id) in whitelist:
                continue

            if entity.broadcast:  # Канал
                try:
                    await client(LeaveChannelRequest(entity))
                    count += 1
                    await human_delay(0.5, 1.5)
                except Exception:
                    pass
            elif entity.megagroup and leave_groups:  # Группа
                try:
                    await client(LeaveChannelRequest(entity))
                    count += 1
                    await human_delay(0.5, 1.5)
                except Exception:
                    pass

    print(f"  {C.DIM}  ↳ {session_name}: отписано от {count}{C.RST}")

async def action_unsubscribe():
    print(f"\n{C.Y}  Режим:{C.RST}")
    print(f"  1. Только каналы")
    print(f"  2. Каналы + группы")
    mode = ask_int("Выбор: ", 1)

    print(f"{C.Y}  Whitelist (не отписываться):{C.RST}")
    print(f"  Введи @username каналов, пустая = конец")
    whitelist = []
    while True:
        w = ask("@")
        if not w:
            break
        whitelist.append(w)

    sessions = select_sessions()
    if not sessions:
        return

    confirm = ask(f"⚠️ Отписаться от {'каналов+групп' if mode==2 else 'каналов'}? (yes/no): ")
    if confirm.lower() != "yes":
        return

    await execute_on_sessions(
        sessions, task_unsubscribe_all,
        task_name="🚪 Отписка от каналов",
        leave_groups=(mode == 2),
        whitelist=whitelist
    )

# ─────────────────────────────────────────────────────────────
# 48. УДАЛИТЬ АККАУНТ
# ─────────────────────────────────────────────────────────────

async def task_delete_account(client, session_name, **kw):
    reason = kw.get("reason", "I want to delete my account")
    await client(DeleteAccountRequest(reason=reason))

async def action_delete_account():
    print(f"\n{C.R}{'═'*50}")
    print(f"  ☠️  ВНИМАНИЕ! УДАЛЕНИЕ АККАУНТА НЕОБРАТИМО!")
    print(f"{'═'*50}{C.RST}")

    confirm1 = ask("Ты уверен? (yes/no): ")
    if confirm1.lower() != "yes":
        return
    confirm2 = ask("Точно уверен? Напиши DELETE: ")
    if confirm2 != "DELETE":
        return

    reason = ask("Причина удаления: ", "I want to delete my account")
    sessions = select_sessions()
    if not sessions:
        return

    await execute_on_sessions(
        sessions, task_delete_account,
        task_name="☠️ УДАЛЕНИЕ АККАУНТОВ",
        reason=reason
    )

# ─────────────────────────────────────────────────────────────
# 49. СПИСОК СЕССИЙ
# ─────────────────────────────────────────────────────────────

async def action_list_sessions():
    sessions = list_sessions()
    if not sessions:
        return
    print(f"\n  Всего: {len(sessions)} сессий")
    print(f"  Папка: {SESSIONS_DIR}")

# ─────────────────────────────────────────────────────────────
# 50. СПИСОК ПРОКСИ
# ─────────────────────────────────────────────────────────────

async def action_list_proxies():
    proxies = load_proxies()
    if not proxies:
        print(f"\n{C.Y}  Прокси не найдены{C.RST}")
        print(f"  Создай файл {C.W}proxies.txt{C.RST} с прокси по одному на строку:")
        print(f"  {C.DIM}socks5://user:pass@ip:port")
        print(f"  socks5://ip:port")
        print(f"  http://ip:port{C.RST}")
        return

    print(f"\n{C.CY}{'─'*50}")
    print(f"  🌐 Прокси: {len(proxies)}")
    print(f"{'─'*50}{C.RST}")
    for i, p in enumerate(proxies, 1):
        print(f"  {C.W}{i:3}. {C.G}{proxy_str(p)}{C.RST}")
    print(f"{C.CY}{'─'*50}{C.RST}")

    # Тест прокси
    test = ask("Протестировать? (y/n): ", "n")
    if test == "y":
        print(f"\n{C.CY}  Тестирование...{C.RST}")
        api_id, api_hash = get_api_credentials()

        for i, p in enumerate(proxies):
            try:
                import socks
                import socket

                ptype_map = {
                    "socks5": socks.SOCKS5,
                    "socks4": socks.SOCKS4,
                    "http": socks.HTTP,
                    "https": socks.HTTP,
                }

                s = socks.socksocket()
                s.set_proxy(
                    ptype_map.get(p["proxy_type"], socks.SOCKS5),
                    p["addr"], p["port"],
                    username=p.get("username"),
                    password=p.get("password")
                )
                s.settimeout(10)

                start_t = time.time()
                s.connect(("149.154.167.50", 443))  # Telegram DC
                latency = int((time.time() - start_t) * 1000)
                s.close()

                print(f"  {C.G}✅ {proxy_str(p)} — {latency}ms{C.RST}")
            except Exception as e:
                print(f"  {C.R}❌ {proxy_str(p)} — {e}{C.RST}")

# ═══════════════════════════════════════════════════════════════
# ГЛАВНЫЙ ЦИКЛ
# ═══════════════════════════════════════════════════════════════

ACTION_MAP = {
    1:  action_view_post,
    2:  action_send_reaction,
    3:  action_subscribe,
    4:  action_all_in_one,
    5:  action_comment,
    6:  action_forward,
    7:  action_vote,
    8:  action_click_button,
    9:  action_mass_reaction,
    10: action_start_bot,
    11: action_bot_scenario,
    12: action_webapp,
    13: action_send_dm,
    14: action_invite,
    15: action_send_message,
    16: action_scheduled_send,
    17: action_edit_message,
    18: action_pin_unpin,
    19: action_delete_own,
    20: action_create_channel,
    21: action_setup_channel,
    22: action_promote_admin,
    23: action_ban_kick,
    24: action_clear_channel,
    25: action_copy_channel,
    26: action_report_channel,
    27: action_report_message,
    28: action_block_users,
    29: action_parse_members,
    30: action_channel_stats,
    31: action_download_media,
    32: action_monitor,
    33: action_auto_responder,
    34: action_auto_posting,
    35: action_tasks_from_json,
    36: action_warmup,
    37: action_online_imitation,
    38: action_checker,
    39: action_active_sessions,
    40: action_reset_all_sessions,
    41: action_selective_reset,
    42: action_new_session,
    43: action_get_info,
    44: action_update_profile,
    45: action_set_photo,
    46: action_set_2fa,
    47: action_unsubscribe,
    48: action_delete_account,
    49: action_list_sessions,
    50: action_list_proxies,
}

async def main():
    # Проверяем API credentials при первом запуске
    get_api_credentials()

    while True:
        print_menu()
        try:
            choice_str = input(f"\n{C.CY}  ▶ Выбери пункт: {C.RST}").strip()
            if not choice_str:
                continue
            choice = int(choice_str)
        except (ValueError, EOFError):
            continue
        except KeyboardInterrupt:
            print(f"\n{C.Y}👋 Выход{C.RST}")
            break

        if choice == 0:
            print(f"\n{C.Y}👋 До встречи!{C.RST}")
            break

        action = ACTION_MAP.get(choice)
        if not action:
            print(f"{C.R}❌ Неверный пункт{C.RST}")
            pause()
            continue

        try:
            # Некоторые функции уже async, вызываем
            result = action()
            if asyncio.iscoroutine(result):
                await result
        except KeyboardInterrupt:
            print(f"\n{C.Y}⏹ Прервано{C.RST}")
        except Exception as e:
            print(f"\n{C.R}❌ Ошибка: {e}{C.RST}")
            import traceback
            traceback.print_exc()

        pause()

# ═══════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        # Для Windows
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.Y}👋 Выход{C.RST}")
    except Exception as e:
        print(f"\n{C.R}Критическая ошибка: {e}{C.RST}")
        import traceback
        traceback.print_exc()

# ═══════════════════════════════════════════════════════════════
# КОНЕЦ ФАЙЛА tg_tool.py
# ═══════════════════════════════════════════════════════════════
