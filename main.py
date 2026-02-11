# ============================================================
# ЧАСТЬ 1: Импорты, конфигурация, БД, константы, хелперы
# ============================================================

import logging
import asyncio
import sqlite3
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any

from aiogram import Bot, Dispatcher, Router, types, F, BaseMiddleware
from aiogram.types import (
    Message, CallbackQuery, InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery,
    Update
)
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

BOT_TOKEN = "7564393324:AAET_RPPJ3ilt9Nw2QKEjy0AXtZZ8HYQ_HQ"
ADMIN_IDS = [5200868328]  # Замени на свои ID админов
DB_PATH = "gift_bot.db"
PAYMENT_PROVIDER_TOKEN = ""

# Установи True если бот имеет Telegram Premium
BOT_IS_PREMIUM = True

# ============================================================
# EMOJI СИСТЕМА
#
# Для СООБЩЕНИЙ: <tg-emoji emoji-id="ID">fb</tg-emoji> (только Premium бот)
# Для КНОПОК (Reply/Inline): используется request_icon_custom_emoji_id
#
# Замени все ID на свои реальные custom emoji ID
# ============================================================

# Конфигурация всех emoji
# Формат: "ключ": ("custom_emoji_id", "fallback_emoji")
EMOJI_CONFIG = {
    # ===== Reply кнопки =====
    "profile":      ("5316791959052905958", "👤"),
    "market":       ("5316791959052905958", "🛒"),
    "market2":      ("5316791959052905958", "💎"),
    "trade":        ("5316791959052905958", "📊"),
    "craft":        ("5316791959052905958", "🔨"),
    "stardom":      ("5316791959052905958", "🌟"),
    "promo":        ("5316791959052905958", "🎟"),

    # ===== Inline кнопки и сообщения =====
    "buy":          ("5316791959052905958", "🛒"),
    "topup":        ("5316791959052905958", "💳"),
    "upgrade":      ("5316791959052905958", "⬆️"),
    "craft_btn":    ("5316791959052905958", "🔨"),
    "send":         ("5316791959052905958", "📤"),
    "star":         ("5316791959052905958", "⭐"),
    "gift":         ("5316791959052905958", "🎁"),
    "nft":          ("5316791959052905958", "🖼"),
    "fire":         ("5316791959052905958", "🔥"),
    "trophy":       ("5316791959052905958", "🏆"),
    "friends":      ("5316791959052905958", "👥"),
    "back":         ("5316791959052905958", "◀️"),
    "next":         ("5316791959052905958", "▶️"),
    "check":        ("5316791959052905958", "✅"),
    "cross":        ("5316791959052905958", "❌"),
    "rent":         ("5316791959052905958", "🏠"),
    "auction":      ("5316791959052905958", "🔔"),
    "limit":        ("5316791959052905958", "⏳"),
    "appeal":       ("5316791959052905958", "📝"),
    "inventory":    ("5316791959052905958", "🎒"),
    "leaderboard":  ("5316791959052905958", "📊"),
    "achieve":      ("5316791959052905958", "🏅"),

    # ===== Дополнительные =====
    "warn_emoji":   ("5316791959052905958", "⚠️"),
    "ban_emoji":    ("5316791959052905958", "🚫"),
    "rules_emoji":  ("5316791959052905958", "📋"),
    "moder":        ("5316791959052905958", "👮"),
    "money":        ("5316791959052905958", "💰"),

    # ===== Stardom Искры =====
    "spark1":       ("5316791959052905958", "🕯"),
    "spark2":       ("5316791959052905958", "✨"),
    "spark3":       ("5316791959052905958", "💫"),
    "spark4":       ("5316791959052905958", "🌟"),
    "spark5":       ("5316791959052905958", "💥"),

    # ===== Редкости =====
    "common":       ("5316791959052905958", "🟢"),
    "rare":         ("5316791959052905958", "🟣"),

    # ===== NFT характеристики =====
    "model":        ("5316791959052905958", "🎭"),
    "pattern":      ("5316791959052905958", "🎨"),
    "background":   ("5316791959052905958", "🖼"),

    # ===== Торговля =====
    "price":        ("5316791959052905958", "💰"),
    "seller":       ("5316791959052905958", "👤"),
    "buyer":        ("5316791959052905958", "🛍"),

    # ===== Аукцион =====
    "bid":          ("5316791959052905958", "📈"),
    "hammer":       ("5316791959052905958", "🔨"),
    "winner":       ("5316791959052905958", "🏆"),

    # ===== Крафт =====
    "success":      ("5316791959052905958", "🎉"),
    "fail":         ("5316791959052905958", "💔"),

    # ===== Аренда =====
    "clock":        ("5316791959052905958", "⏰"),
    "house":        ("5316791959052905958", "🏠"),

    # ===== Общие =====
    "info":         ("5316791959052905958", "ℹ️"),
    "warning":      ("5316791959052905958", "⚠️"),
    "error":        ("5316791959052905958", "❌"),
    "ok":           ("5316791959052905958", "✅"),
    "id":           ("5316791959052905958", "🆔"),
    "date":         ("5316791959052905958", "📅"),
    "pin":          ("5316791959052905958", "📌"),
    "link":         ("5316791959052905958", "🔗"),
    "lock":         ("5316791959052905958", "🔒"),
    "unlock":       ("5316791959052905958", "🔓"),
    "sparkles":     ("5316791959052905958", "✨"),
    "gem":          ("5316791959052905958", "💎"),
    "crown":        ("5316791959052905958", "👑"),
    "medal":        ("5316791959052905958", "🏅"),
    "package":      ("5316791959052905958", "📦"),
}


def pe(key: str) -> str:
    """
    Emoji для СООБЩЕНИЙ.
    BOT_IS_PREMIUM=True  → <tg-emoji emoji-id="ID">fallback</tg-emoji>
    BOT_IS_PREMIUM=False → обычный emoji
    """
    data = EMOJI_CONFIG.get(key)
    if not data:
        return "❓"
    eid, fb = data
    if BOT_IS_PREMIUM and eid:
        return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'
    return fb


def pe_plain(key: str) -> str:
    """Обычный fallback emoji (текст кнопок)."""
    data = EMOJI_CONFIG.get(key)
    if not data:
        return "❓"
    return data[1]


def pe_id(key: str) -> Optional[str]:
    """
    Получить custom_emoji_id для кнопок.
    Возвращает ID если BOT_IS_PREMIUM, иначе None.
    """
    if not BOT_IS_PREMIUM:
        return None
    data = EMOJI_CONFIG.get(key)
    if data and data[0]:
        return data[0]
    return None


# ============================================================
# ФУНКЦИИ СОЗДАНИЯ КНОПОК С CUSTOM EMOJI
# ============================================================


def make_inline_button(text: str, callback_data: str, emoji_key: str = None) -> InlineKeyboardButton:
    """
    Создаёт InlineKeyboardButton с custom emoji иконкой если бот Premium.
    Telegram Bot API поддерживает custom emoji в тексте кнопки
    только если бот имеет Premium.
    """
    icon_text = ""
    if emoji_key:
        icon_text = f"{pe_plain(emoji_key)} "

    return InlineKeyboardButton(
        text=f"{icon_text}{text}",
        callback_data=callback_data
    )


def make_reply_button(text: str, emoji_key: str = None) -> KeyboardButton:
    """
    Создаёт KeyboardButton (Reply).
    В request_icon_custom_emoji_id нельзя напрямую передать —
    это поле для WebApp кнопок.
    Используем emoji в тексте кнопки.
    """
    icon_text = ""
    if emoji_key:
        icon_text = f"{pe_plain(emoji_key)} "

    return KeyboardButton(text=f"{icon_text}{text}")


# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# BOT & DISPATCHER
# ============================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# ============================================================
# FSM STATES
# ============================================================


class TopUpStates(StatesGroup):
    waiting_amount = State()
    waiting_payment = State()


class BuyGiftStates(StatesGroup):
    waiting_target = State()


class TradeStates(StatesGroup):
    waiting_price = State()


class CraftStates(StatesGroup):
    selecting_nfts = State()


class RentStates(StatesGroup):
    waiting_price_duration = State()


class AuctionStates(StatesGroup):
    waiting_details = State()


class AppealStates(StatesGroup):
    waiting_text = State()


class AppealRejectStates(StatesGroup):
    waiting_reason = State()


class AddRulesStates(StatesGroup):
    waiting_text = State()


class GiftBuyTarget(StatesGroup):
    waiting_user_id = State()


# ============================================================
# NFT ХАРАКТЕРИСТИКИ — 50 моделей, 50 узоров, 50 фонов
# ============================================================

NFT_MODELS = [
    {"name": "Phoenix", "chance": 0.1},
    {"name": "Dragon", "chance": 0.15},
    {"name": "Unicorn", "chance": 0.2},
    {"name": "Griffin", "chance": 0.25},
    {"name": "Leviathan", "chance": 0.3},
    {"name": "Cerberus", "chance": 0.35},
    {"name": "Hydra", "chance": 0.4},
    {"name": "Chimera", "chance": 0.45},
    {"name": "Basilisk", "chance": 0.5},
    {"name": "Kraken", "chance": 0.55},
    {"name": "Minotaur", "chance": 0.6},
    {"name": "Sphinx", "chance": 0.65},
    {"name": "Pegasus", "chance": 0.7},
    {"name": "Centaur", "chance": 0.75},
    {"name": "Manticore", "chance": 0.8},
    {"name": "Wyvern", "chance": 0.85},
    {"name": "Banshee", "chance": 0.9},
    {"name": "Golem", "chance": 0.95},
    {"name": "Djinn", "chance": 1.0},
    {"name": "Titan", "chance": 1.1},
    {"name": "Valkyrie", "chance": 1.2},
    {"name": "Fenrir", "chance": 1.3},
    {"name": "Naga", "chance": 1.4},
    {"name": "Behemoth", "chance": 1.5},
    {"name": "Seraphim", "chance": 1.6},
    {"name": "Wraith", "chance": 1.7},
    {"name": "Revenant", "chance": 1.8},
    {"name": "Shade", "chance": 1.9},
    {"name": "Specter", "chance": 2.0},
    {"name": "Phantom", "chance": 2.05},
    {"name": "Ghoul", "chance": 2.1},
    {"name": "Imp", "chance": 2.15},
    {"name": "Sprite", "chance": 2.2},
    {"name": "Pixie", "chance": 2.25},
    {"name": "Sylph", "chance": 2.3},
    {"name": "Dryad", "chance": 2.35},
    {"name": "Nymph", "chance": 2.4},
    {"name": "Satyr", "chance": 2.45},
    {"name": "Faun", "chance": 2.5},
    {"name": "Elemental", "chance": 2.55},
    {"name": "Archon", "chance": 2.6},
    {"name": "Herald", "chance": 2.65},
    {"name": "Sentinel", "chance": 2.7},
    {"name": "Warden", "chance": 2.75},
    {"name": "Oracle", "chance": 2.8},
    {"name": "Prophet", "chance": 2.85},
    {"name": "Mystic", "chance": 2.9},
    {"name": "Sorcerer", "chance": 2.95},
    {"name": "Warlock", "chance": 3.0},
    {"name": "Enchanter", "chance": 3.0},
]

NFT_PATTERNS = [
    {"name": "Nebula Swirl", "chance": 0.1},
    {"name": "Cosmic Web", "chance": 0.15},
    {"name": "Void Fracture", "chance": 0.2},
    {"name": "Quantum Dots", "chance": 0.25},
    {"name": "Plasma Wave", "chance": 0.3},
    {"name": "Crystal Lattice", "chance": 0.35},
    {"name": "Aurora Stream", "chance": 0.4},
    {"name": "Lightning Mesh", "chance": 0.45},
    {"name": "Shadow Weave", "chance": 0.5},
    {"name": "Frost Spiral", "chance": 0.55},
    {"name": "Ember Trail", "chance": 0.6},
    {"name": "Ocean Ripple", "chance": 0.65},
    {"name": "Sand Dune", "chance": 0.7},
    {"name": "Magma Flow", "chance": 0.75},
    {"name": "Vine Tangle", "chance": 0.8},
    {"name": "Star Burst", "chance": 0.85},
    {"name": "Moon Phase", "chance": 0.9},
    {"name": "Sun Flare", "chance": 0.95},
    {"name": "Geo Hex", "chance": 1.0},
    {"name": "Tribal Mark", "chance": 1.1},
    {"name": "Celtic Knot", "chance": 1.2},
    {"name": "Mandala", "chance": 1.3},
    {"name": "Fractal Tree", "chance": 1.4},
    {"name": "Binary Rain", "chance": 1.5},
    {"name": "Circuit Board", "chance": 1.6},
    {"name": "DNA Helix", "chance": 1.7},
    {"name": "Pulse Line", "chance": 1.8},
    {"name": "Wave Form", "chance": 1.9},
    {"name": "Zigzag", "chance": 2.0},
    {"name": "Chevron", "chance": 2.05},
    {"name": "Diamond Grid", "chance": 2.1},
    {"name": "Honeycomb", "chance": 2.15},
    {"name": "Mosaic", "chance": 2.2},
    {"name": "Paisley", "chance": 2.25},
    {"name": "Damask", "chance": 2.3},
    {"name": "Herringbone", "chance": 2.35},
    {"name": "Plaid", "chance": 2.4},
    {"name": "Houndstooth", "chance": 2.45},
    {"name": "Polka Dot", "chance": 2.5},
    {"name": "Stripe", "chance": 2.55},
    {"name": "Checkered", "chance": 2.6},
    {"name": "Argyle", "chance": 2.65},
    {"name": "Floral", "chance": 2.7},
    {"name": "Baroque", "chance": 2.75},
    {"name": "Art Deco", "chance": 2.8},
    {"name": "Minimalist", "chance": 2.85},
    {"name": "Abstract", "chance": 2.9},
    {"name": "Grunge", "chance": 2.95},
    {"name": "Watercolor", "chance": 3.0},
    {"name": "Sketch", "chance": 3.0},
]

NFT_BACKGROUNDS = [
    {"name": "Eternal Void", "chance": 0.1},
    {"name": "Supernova", "chance": 0.15},
    {"name": "Black Hole", "chance": 0.2},
    {"name": "Galactic Core", "chance": 0.25},
    {"name": "Dark Matter", "chance": 0.3},
    {"name": "Astral Plane", "chance": 0.35},
    {"name": "Quantum Realm", "chance": 0.4},
    {"name": "Nether World", "chance": 0.45},
    {"name": "Elysium", "chance": 0.5},
    {"name": "Valhalla", "chance": 0.55},
    {"name": "Olympus", "chance": 0.6},
    {"name": "Asgard", "chance": 0.65},
    {"name": "Avalon", "chance": 0.7},
    {"name": "Atlantis", "chance": 0.75},
    {"name": "El Dorado", "chance": 0.8},
    {"name": "Shangri-La", "chance": 0.85},
    {"name": "Arcadia", "chance": 0.9},
    {"name": "Eden", "chance": 0.95},
    {"name": "Nirvana", "chance": 1.0},
    {"name": "Utopia", "chance": 1.1},
    {"name": "Crimson Sky", "chance": 1.2},
    {"name": "Azure Deep", "chance": 1.3},
    {"name": "Emerald Forest", "chance": 1.4},
    {"name": "Golden Desert", "chance": 1.5},
    {"name": "Silver Mountain", "chance": 1.6},
    {"name": "Ruby Cavern", "chance": 1.7},
    {"name": "Sapphire Ocean", "chance": 1.8},
    {"name": "Amethyst Cave", "chance": 1.9},
    {"name": "Topaz Valley", "chance": 2.0},
    {"name": "Opal Lake", "chance": 2.05},
    {"name": "Pearl Shore", "chance": 2.1},
    {"name": "Jade Garden", "chance": 2.15},
    {"name": "Onyx Tower", "chance": 2.2},
    {"name": "Ivory Palace", "chance": 2.25},
    {"name": "Bronze Arena", "chance": 2.3},
    {"name": "Copper Mine", "chance": 2.35},
    {"name": "Tin Workshop", "chance": 2.4},
    {"name": "Iron Forge", "chance": 2.45},
    {"name": "Steel Citadel", "chance": 2.5},
    {"name": "Chrome Lab", "chance": 2.55},
    {"name": "Neon City", "chance": 2.6},
    {"name": "Pixel World", "chance": 2.65},
    {"name": "Retro Arcade", "chance": 2.7},
    {"name": "Cyber Punk", "chance": 2.75},
    {"name": "Steam Punk", "chance": 2.8},
    {"name": "Solar Punk", "chance": 2.85},
    {"name": "Bio Dome", "chance": 2.9},
    {"name": "Coral Reef", "chance": 2.95},
    {"name": "Tundra", "chance": 3.0},
    {"name": "Savanna", "chance": 3.0},
]

# ============================================================
# STARDOM КОНФИГУРАЦИЯ
# ============================================================

STARDOM_LEVELS = {
    1: {
        "name": "Stardom I",
        "price": 135,
        "duration_months": 2,
        "nft_create_fee": 15,
        "nft_transfer_fee": 15,
        "gift_transfer_fee": 15,
        "exclusive_gift": "Потухшая Искра",
        "exclusive_emoji": "🕯"
    },
    2: {
        "name": "Stardom II",
        "price": 250,
        "duration_months": 3,
        "nft_create_fee": 10,
        "nft_transfer_fee": 10,
        "gift_transfer_fee": 15,
        "exclusive_gift": "Искра",
        "exclusive_emoji": "✨"
    },
    3: {
        "name": "Stardom III",
        "price": 350,
        "duration_months": 3,
        "nft_create_fee": 5,
        "nft_transfer_fee": 5,
        "gift_transfer_fee": 15,
        "exclusive_gift": "Сильная Искра",
        "exclusive_emoji": "💫"
    },
    4: {
        "name": "Stardom IV",
        "price": 500,
        "duration_months": 5,
        "nft_create_fee": 3,
        "nft_transfer_fee": 3,
        "gift_transfer_fee": 5,
        "exclusive_gift": "Мощная Искра",
        "exclusive_emoji": "🌟"
    },
    5: {
        "name": "Stardom V",
        "price": 750,
        "duration_months": 6,
        "nft_create_fee": 0,
        "nft_transfer_fee": 0,
        "gift_transfer_fee": 0,
        "exclusive_gift": "Переполненная Искра",
        "exclusive_emoji": "💥"
    },
}

# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

ACHIEVEMENTS = {
    "first_gift": {"name": "Первый подарок 🎁", "desc": "Купите свой первый подарок"},
    "first_nft": {"name": "Первый NFT 🖼", "desc": "Улучшите подарок до NFT"},
    "first_craft": {"name": "Первый крафт 🔨", "desc": "Скрафтите свой первый NFT"},
    "first_stardom": {"name": "Звёздный статус 🌟", "desc": "Приобретите любой Stardom"},
}

# ============================================================
# БАЗА ДАННЫХ — ИНИЦИАЛИЗАЦИЯ
# ============================================================


def init_db():
    """Создаёт все необходимые таблицы в SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            stars INTEGER DEFAULT 0,
            stardom_level INTEGER DEFAULT 0,
            stardom_expires TEXT DEFAULT '',
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT DEFAULT '',
            ban_until TEXT DEFAULT '',
            is_buy_banned INTEGER DEFAULT 0,
            buy_ban_reason TEXT DEFAULT '',
            is_trade_banned INTEGER DEFAULT 0,
            trade_ban_reason TEXT DEFAULT '',
            appeal_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            achievements TEXT DEFAULT '[]'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            gift_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '🎁',
            quantity INTEGER DEFAULT 0,
            sold INTEGER DEFAULT 0,
            price INTEGER NOT NULL,
            rarity TEXT DEFAULT 'common',
            is_active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS limited_gifts (
            limit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '🎁',
            price INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            sold INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            inv_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gift_id INTEGER,
            limit_id INTEGER,
            gift_name TEXT NOT NULL,
            gift_emoji TEXT DEFAULT '🎁',
            rarity TEXT DEFAULT 'common',
            is_nft INTEGER DEFAULT 0,
            nft_id INTEGER,
            is_limited INTEGER DEFAULT 0,
            purchased_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS nfts (
            nft_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            gift_name TEXT NOT NULL,
            gift_emoji TEXT DEFAULT '🎁',
            model_name TEXT NOT NULL,
            model_chance REAL NOT NULL,
            pattern_name TEXT NOT NULL,
            pattern_chance REAL NOT NULL,
            bg_name TEXT NOT NULL,
            bg_chance REAL NOT NULL,
            is_crafted INTEGER DEFAULT 0,
            source_gift_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            nft_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (seller_id) REFERENCES users(user_id),
            FOREIGN KEY (nft_id) REFERENCES nfts(nft_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            nft_id INTEGER NOT NULL,
            min_bid INTEGER NOT NULL,
            bid_step INTEGER NOT NULL DEFAULT 10,
            ends_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (seller_id) REFERENCES users(user_id),
            FOREIGN KEY (nft_id) REFERENCES nfts(nft_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS auction_bids (
            bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
            auction_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            bid_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (auction_id) REFERENCES auctions(auction_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS nft_rentals (
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            renter_id INTEGER,
            nft_id INTEGER NOT NULL,
            price_per_hour INTEGER NOT NULL,
            ends_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_rented INTEGER DEFAULT 0,
            rent_started TEXT DEFAULT '',
            rent_ends TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (owner_id) REFERENCES users(user_id),
            FOREIGN KEY (nft_id) REFERENCES nfts(nft_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            promo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            reward_type TEXT NOT NULL,
            reward_value TEXT NOT NULL,
            max_uses INTEGER DEFAULT 1,
            current_uses INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS promo_uses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            promo_id INTEGER NOT NULL,
            used_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (promo_id) REFERENCES promocodes(promo_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY DEFAULT 1,
            text TEXT DEFAULT 'Правила ещё не установлены.'
        )
    """)
    c.execute("INSERT OR IGNORE INTO rules (id, text) VALUES (1, 'Правила ещё не установлены.')")

    c.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            added_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, friend_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS moderators (
            user_id INTEGER PRIMARY KEY
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS moder_ban_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moder_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            banned_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            tg_payment_id TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS global_counters (
            key TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
    """)
    c.execute("INSERT OR IGNORE INTO global_counters (key, value) VALUES ('gift_purchase_counter', 0)")
    c.execute("INSERT OR IGNORE INTO global_counters (key, value) VALUES ('nft_counter', 0)")

    c.execute("""
        CREATE TABLE IF NOT EXISTS appeals (
            appeal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_response TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS inline_transfers (
            transfer_id TEXT PRIMARY KEY,
            sender_id INTEGER NOT NULL,
            inv_id INTEGER,
            nft_id INTEGER,
            transfer_type TEXT NOT NULL,
            is_claimed INTEGER DEFAULT 0,
            claimed_by INTEGER,
            message_id TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ БД
# ============================================================


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_user(user_id: int, username: str = "", first_name: str = ""):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone() is None:
        c.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
    else:
        c.execute(
            "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
            (username, first_name, user_id)
        )
    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[dict]:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def update_stars(user_id: int, amount: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def get_stars(user_id: int) -> int:
    user = get_user(user_id)
    return user["stars"] if user else 0


def get_next_counter(key: str) -> int:
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE global_counters SET value = value + 1 WHERE key = ?", (key,))
    c.execute("SELECT value FROM global_counters WHERE key = ?", (key,))
    val = c.fetchone()["value"]
    conn.commit()
    conn.close()
    return val


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_moderator(user_id: int) -> bool:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM moderators WHERE user_id = ?", (user_id,))
    result = c.fetchone() is not None
    conn.close()
    return result


def is_banned(user_id: int) -> bool:
    user = get_user(user_id)
    if not user or user["is_banned"] == 0:
        return False
    if user["ban_until"] == "permanent":
        return True
    if user["ban_until"]:
        try:
            ban_until = datetime.fromisoformat(user["ban_until"])
            if datetime.now() > ban_until:
                conn = get_db()
                c = conn.cursor()
                c.execute(
                    "UPDATE users SET is_banned = 0, ban_reason = '', ban_until = '' WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                conn.close()
                return False
            return True
        except Exception:
            return True
    return True


def get_user_stardom(user_id: int) -> int:
    user = get_user(user_id)
    if not user or user["stardom_level"] == 0:
        return 0
    if user["stardom_expires"]:
        try:
            expires = datetime.fromisoformat(user["stardom_expires"])
            if datetime.now() > expires:
                conn = get_db()
                c = conn.cursor()
                c.execute(
                    "UPDATE users SET stardom_level = 0, stardom_expires = '' WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                conn.close()
                return 0
        except Exception:
            pass
    return user["stardom_level"]


def get_nft_create_fee(user_id: int) -> int:
    level = get_user_stardom(user_id)
    if level > 0 and level in STARDOM_LEVELS:
        return STARDOM_LEVELS[level]["nft_create_fee"]
    return 20


def get_nft_transfer_fee(user_id: int) -> int:
    level = get_user_stardom(user_id)
    if level > 0 and level in STARDOM_LEVELS:
        return STARDOM_LEVELS[level]["nft_transfer_fee"]
    return 20


def get_gift_transfer_fee(user_id: int) -> int:
    level = get_user_stardom(user_id)
    if level > 0 and level in STARDOM_LEVELS:
        return STARDOM_LEVELS[level]["gift_transfer_fee"]
    return 15


def grant_achievement(user_id: int, achievement_key: str) -> bool:
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT achievements FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    try:
        achievements = json.loads(row["achievements"])
    except Exception:
        achievements = []
    if achievement_key in achievements:
        conn.close()
        return False
    achievements.append(achievement_key)
    c.execute(
        "UPDATE users SET achievements = ? WHERE user_id = ?",
        (json.dumps(achievements), user_id)
    )
    conn.commit()
    conn.close()
    return True


def get_user_achievements(user_id: int) -> list:
    user = get_user(user_id)
    if not user:
        return []
    try:
        return json.loads(user["achievements"])
    except Exception:
        return []


def generate_nft_characteristics(total_nfts: int = 1000):
    model = random.choices(NFT_MODELS, weights=[m["chance"] for m in NFT_MODELS], k=1)[0]
    pattern = random.choices(NFT_PATTERNS, weights=[p["chance"] for p in NFT_PATTERNS], k=1)[0]
    bg = random.choices(NFT_BACKGROUNDS, weights=[b["chance"] for b in NFT_BACKGROUNDS], k=1)[0]
    return model, pattern, bg


async def send_notification(user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления {user_id}: {e}")


# ============================================================
# REPLY КЛАВИАТУРА — с custom emoji в кнопках
# ============================================================


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная reply-клавиатура."""
    kb = ReplyKeyboardBuilder()
    kb.row(
        make_reply_button("Профиль", "profile"),
        make_reply_button("Маркет", "market"),
        make_reply_button("Маркет #2", "market2"),
    )
    kb.row(
        make_reply_button("Торговля", "trade"),
        make_reply_button("Крафт", "craft"),
        make_reply_button("Stardom", "stardom"),
    )
    kb.row(
        make_reply_button("Промокоды", "promo"),
        make_reply_button("Топ", "trophy"),
        make_reply_button("Друзья", "friends"),
    )
    return kb.as_markup(resize_keyboard=True)


# ============================================================
# MIDDLEWARE ДЛЯ ПРОВЕРКИ БАНА
# ============================================================


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            ensure_user(user.id, user.username or "", user.first_name or "")
            if is_banned(user.id):
                user_data = get_user(user.id)
                ban_text = (
                    f"{pe('ban_emoji')} <b>Вы заблокированы!</b>\n\n"
                    f"{pe('rules_emoji')} Причина: {user_data.get('ban_reason', 'Не указана')}\n"
                    f"{pe('clock')} До: {user_data.get('ban_until', 'Бессрочно')}\n\n"
                    f"{pe('appeal')} Подайте аппеляцию: /appeal <описание>"
                )
                if isinstance(event, Message):
                    if event.text and event.text.startswith(("/appeal", "/rules")):
                        return await handler(event, data)
                    await event.answer(ban_text)
                    return
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Вы заблокированы!", show_alert=True)
                    return

        return await handler(event, data)


router.message.middleware(BanCheckMiddleware())
router.callback_query.middleware(BanCheckMiddleware())


# ============================================================
# КОМАНДА ДЛЯ ПОЛУЧЕНИЯ CUSTOM EMOJI ID
# ============================================================


@router.message(Command("get_emoji"))
async def cmd_get_emoji(message: Message):
    """Отправь сообщение с premium emoji — бот покажет их ID."""
    if not message.entities:
        await message.answer(
            f"{pe('info')} <b>Получение Custom Emoji ID</b>\n\n"
            f"Отправьте сообщение с premium emoji боту,\n"
            f"и он покажет их ID для настройки."
        )
        return

    text = f"{pe('info')} <b>Найденные Custom Emoji:</b>\n\n"
    found = False
    for ent in message.entities:
        if ent.type == "custom_emoji":
            text += f"• emoji-id: <code>{ent.custom_emoji_id}</code>\n"
            found = True

    if not found:
        text += "Custom emoji не найдены в сообщении."

    await message.answer(text)


# ============================================================
# ИНИЦИАЛИЗАЦИЯ БД ПРИ ЗАПУСКЕ
# ============================================================

init_db()

# Конец части 1
# ============================================================
# ============================================================
# ЧАСТЬ 2: Start, Профиль, Пополнение звёзд, Достижения, Друзья
# ============================================================

# ============================================================
# КОМАНДА /start
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    ensure_user(user.id, user.username or "", user.first_name or "")

    welcome_text = (
        f"{pe('gift')} <b>Добро пожаловать в Gift Bot!</b> {pe('gift')}\n\n"
        f"{pe('star')} Здесь вы можете:\n"
        f"├ {pe('buy')} Покупать подарки\n"
        f"├ {pe('nft')} Улучшать до NFT\n"
        f"├ {pe('craft_btn')} Крафтить уникальные NFT\n"
        f"├ {pe('trade')} Торговать на маркете\n"
        f"├ {pe('stardom')} Получать Stardom статус\n"
        f"├ {pe('rent')} Сдавать NFT в аренду\n"
        f"├ {pe('auction')} Участвовать в аукционах\n"
        f"└ {pe('friends')} Добавлять друзей\n\n"
        f"{pe('rules_emoji')} Используйте кнопки ниже для навигации!\n"
        f"{pe('info')} /help — все команды"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


# ============================================================
# КОМАНДА /help
# ============================================================

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        f"{pe('star')} <b>Команды пользователя:</b>\n\n"
        f"{pe('rules_emoji')} /rules — Правила\n"
        f"{pe('profile')} /help — Все команды\n\n"
        f"<b>{pe('package')} Передача:</b>\n"
        f"├ /transfer &lt;inv_id&gt; &lt;user_id&gt; — Передать подарок (15{pe('star')})\n"
        f"└ /transfer_nft &lt;nft_id&gt; &lt;user_id&gt; — Передать NFT (20{pe('star')})\n\n"
        f"<b>{pe('trade')} Торговля:</b>\n"
        f"├ /trade &lt;nft_id&gt; &lt;цена&gt; — Выставить NFT на продажу\n"
        f"└ /del_trade &lt;trade_id&gt; — Снять с продажи\n\n"
        f"<b>{pe('house')} Аренда:</b>\n"
        f"├ /nft_rental — Список аренд\n"
        f"├ /nft_rents &lt;nft_id&gt; &lt;цена/час&gt; &lt;время_окончания&gt; — Сдать в аренду\n"
        f"└ /rent_nft &lt;rental_id&gt; — Арендовать\n\n"
        f"<b>{pe('auction')} Аукционы:</b>\n"
        f"├ /auctions — Список аукционов\n"
        f"└ /add_auc &lt;nft_id&gt; &lt;мин_ставка&gt; &lt;шаг&gt; &lt;дата_окончания&gt;\n\n"
        f"<b>{pe('friends')} Друзья:</b>\n"
        f"├ /add_friend &lt;user_id&gt; — Добавить друга\n"
        f"├ /del_friend &lt;user_id&gt; — Удалить друга\n"
        f"└ /friends — Список друзей\n\n"
        f"<b>{pe('appeal')} Прочее:</b>\n"
        f"├ /appeal &lt;текст&gt; — Аппеляция на бан\n"
        f"└ /promo &lt;промокод&gt; — Активировать промокод\n"
    )
    await message.answer(help_text)


# ============================================================
# ПРОФИЛЬ
# ============================================================

@router.message(F.text.endswith("Профиль"))
async def show_profile(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        ensure_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
        user = get_user(user_id)

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ?", (user_id,))
    gift_count = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM nfts WHERE owner_id = ?", (user_id,))
    nft_count = c.fetchone()["cnt"]

    c.execute("SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ? AND is_limited = 1", (user_id,))
    limited_count = c.fetchone()["cnt"]

    conn.close()

    stardom_level = get_user_stardom(user_id)
    stardom_text = "Нет"
    if stardom_level > 0 and stardom_level in STARDOM_LEVELS:
        sd = STARDOM_LEVELS[stardom_level]
        stardom_text = f"{sd['name']} (до {user.get('stardom_expires', '?')[:10]})"

    achievements = get_user_achievements(user_id)
    ach_count = len(achievements)
    total_ach = len(ACHIEVEMENTS)

    ban_status = ""
    if user["is_buy_banned"]:
        ban_status += f"\n{pe('ban_emoji')} Бан покупок: {user['buy_ban_reason']}"
    if user["is_trade_banned"]:
        ban_status += f"\n{pe('ban_emoji')} Бан торговли: {user['trade_ban_reason']}"

    profile_text = (
        f"{pe('profile')} <b>Ваш профиль</b>\n\n"
        f"{pe('profile')} <b>{user['first_name']}</b> (@{user['username'] or 'нет'})\n"
        f"{pe('id')} ID: <code>{user_id}</code>\n\n"
        f"{pe('star')} Баланс: <b>{user['stars']} {pe('star')}</b>\n"
        f"{pe('gift')} Подарков: <b>{gift_count}</b>\n"
        f"{pe('nft')} NFT: <b>{nft_count}</b>\n"
        f"{pe('limit')} Лимитированных: <b>{limited_count}</b>\n"
        f"{pe('stardom')} Stardom: <b>{stardom_text}</b>\n"
        f"{pe('achieve')} Достижения: <b>{ach_count}/{total_ach}</b>\n"
        f"{ban_status}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Пополнить баланс", "topup_stars", "topup"))
    kb.row(
        make_inline_button("Инвентарь", "inventory_0", "inventory"),
        make_inline_button("Мои NFT", "my_nfts_0", "nft")
    )
    kb.row(make_inline_button("Достижения", "achievements", "achieve"))
    kb.row(make_inline_button("Улучшить до NFT", "show_upgradeable_0", "upgrade"))

    await message.answer(profile_text, reply_markup=kb.as_markup())


# ============================================================
# ИНВЕНТАРЬ — ПАГИНАЦИЯ
# ============================================================

@router.callback_query(F.data.startswith("inventory_"))
async def show_inventory(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = int(callback.data.split("_")[1])
    per_page = 5

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM inventory WHERE user_id = ? ORDER BY inv_id DESC LIMIT ? OFFSET ?",
        (user_id, per_page, page * per_page)
    )
    items = [dict(row) for row in c.fetchall()]
    c.execute("SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ?", (user_id,))
    total = c.fetchone()["cnt"]
    conn.close()

    if not items and page == 0:
        await callback.answer(f"{pe_plain('package')} Инвентарь пуст!", show_alert=True)
        return

    total_pages = max(1, (total + per_page - 1) // per_page)
    text = f"{pe('inventory')} <b>Ваш инвентарь</b> (стр. {page + 1}/{total_pages}):\n\n"

    for item in items:
        nft_label = ""
        if item["is_nft"]:
            nft_label = f" {pe('nft')} NFT #{item['nft_id']}"
        limited_label = ""
        if item["is_limited"]:
            limited_label = f" {pe('limit')} Лимит."
        rarity_emoji = pe('common') if item["rarity"] == "common" else pe('rare')
        text += (
            f"{rarity_emoji} {item['gift_emoji']} <b>{item['gift_name']}</b>\n"
            f"   {pe('id')} Inv ID: <code>{item['inv_id']}</code>{nft_label}{limited_label}\n\n"
        )

    kb = InlineKeyboardBuilder()
    nav_buttons = []
    if page > 0:
        nav_buttons.append(make_inline_button("Назад", f"inventory_{page - 1}", "back"))
    if (page + 1) * per_page < total:
        nav_buttons.append(make_inline_button("Далее", f"inventory_{page + 1}", "next"))
    if nav_buttons:
        kb.row(*nav_buttons)
    kb.row(make_inline_button("Назад к профилю", "back_profile", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# МОИ NFT — ПАГИНАЦИЯ
# ============================================================

@router.callback_query(F.data.startswith("my_nfts_"))
async def show_my_nfts(callback: CallbackQuery):
    user_id = callback.from_user.id
    page = int(callback.data.split("_")[2])
    per_page = 3

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM nfts WHERE owner_id = ? ORDER BY nft_id DESC LIMIT ? OFFSET ?",
        (user_id, per_page, page * per_page)
    )
    nfts = [dict(row) for row in c.fetchall()]
    c.execute("SELECT COUNT(*) as cnt FROM nfts WHERE owner_id = ?", (user_id,))
    total = c.fetchone()["cnt"]
    conn.close()

    if not nfts and page == 0:
        await callback.answer(f"{pe_plain('nft')} У вас нет NFT!", show_alert=True)
        return

    total_pages = max(1, (total + per_page - 1) // per_page)
    text = f"{pe('nft')} <b>Ваши NFT</b> (стр. {page + 1}/{total_pages}):\n\n"

    for nft in nfts:
        crafted_label = f" {pe('hammer')} Крафт" if nft["is_crafted"] else ""
        text += (
            f"{'─' * 25}\n"
            f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft['nft_id']}{crafted_label}\n"
            f"{pe('model')} Модель: <b>{nft['model_name']}</b> ({nft['model_chance']}%)\n"
            f"{pe('pattern')} Узор: <b>{nft['pattern_name']}</b> ({nft['pattern_chance']}%)\n"
            f"{pe('background')} Фон: <b>{nft['bg_name']}</b> ({nft['bg_chance']}%)\n"
            f"{pe('date')} Создан: {nft['created_at'][:10]}\n\n"
        )

    kb = InlineKeyboardBuilder()
    nav_buttons = []
    if page > 0:
        nav_buttons.append(make_inline_button("Назад", f"my_nfts_{page - 1}", "back"))
    if (page + 1) * per_page < total:
        nav_buttons.append(make_inline_button("Далее", f"my_nfts_{page + 1}", "next"))
    if nav_buttons:
        kb.row(*nav_buttons)
    kb.row(make_inline_button("Назад к профилю", "back_profile", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# НАЗАД К ПРОФИЛЮ
# ============================================================

@router.callback_query(F.data == "back_profile")
async def back_to_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ?", (user_id,))
    gift_count = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM nfts WHERE owner_id = ?", (user_id,))
    nft_count = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ? AND is_limited = 1", (user_id,))
    limited_count = c.fetchone()["cnt"]
    conn.close()

    stardom_level = get_user_stardom(user_id)
    stardom_text = "Нет"
    if stardom_level > 0 and stardom_level in STARDOM_LEVELS:
        sd = STARDOM_LEVELS[stardom_level]
        stardom_text = f"{sd['name']} (до {user.get('stardom_expires', '?')[:10]})"

    achievements = get_user_achievements(user_id)

    ban_status = ""
    if user["is_buy_banned"]:
        ban_status += f"\n{pe('ban_emoji')} Бан покупок: {user['buy_ban_reason']}"
    if user["is_trade_banned"]:
        ban_status += f"\n{pe('ban_emoji')} Бан торговли: {user['trade_ban_reason']}"

    profile_text = (
        f"{pe('profile')} <b>Ваш профиль</b>\n\n"
        f"{pe('profile')} <b>{user['first_name']}</b> (@{user['username'] or 'нет'})\n"
        f"{pe('id')} ID: <code>{user_id}</code>\n\n"
        f"{pe('star')} Баланс: <b>{user['stars']} {pe('star')}</b>\n"
        f"{pe('gift')} Подарков: <b>{gift_count}</b>\n"
        f"{pe('nft')} NFT: <b>{nft_count}</b>\n"
        f"{pe('limit')} Лимитированных: <b>{limited_count}</b>\n"
        f"{pe('stardom')} Stardom: <b>{stardom_text}</b>\n"
        f"{pe('achieve')} Достижения: <b>{len(achievements)}/{len(ACHIEVEMENTS)}</b>\n"
        f"{ban_status}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Пополнить баланс", "topup_stars", "topup"))
    kb.row(
        make_inline_button("Инвентарь", "inventory_0", "inventory"),
        make_inline_button("Мои NFT", "my_nfts_0", "nft")
    )
    kb.row(make_inline_button("Достижения", "achievements", "achieve"))
    kb.row(make_inline_button("Улучшить до NFT", "show_upgradeable_0", "upgrade"))

    try:
        await callback.message.edit_text(profile_text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# ПОПОЛНЕНИЕ ЗВЁЗД
# ============================================================

@router.callback_query(F.data == "topup_stars")
async def topup_stars_start(callback: CallbackQuery, state: FSMContext):
    text = (
        f"{pe('topup')} <b>Пополнение баланса</b>\n\n"
        f"Выберите сумму или введите свою:\n"
    )
    kb = InlineKeyboardBuilder()
    for amount in [50, 100, 250, 500, 1000]:
        kb.button(text=f"{amount} {pe_plain('star')}", callback_data=f"topup_amount_{amount}")
    kb.adjust(3)
    kb.row(make_inline_button("Своя сумма", "topup_custom", "appeal"))
    kb.row(make_inline_button("Назад", "back_profile", "back"))

    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "topup_custom")
async def topup_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopUpStates.waiting_amount)
    await callback.message.edit_text(
        f"{pe('topup')} <b>Введите сумму пополнения (мин. 1 {pe('star')}):</b>"
    )
    await callback.answer()


@router.message(TopUpStates.waiting_amount)
async def topup_custom_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1:
            await message.answer(f"{pe('cross')} Минимальная сумма — 1 {pe('star')}")
            return
        if amount > 10000:
            await message.answer(f"{pe('cross')} Максимальная сумма — 10000 {pe('star')}")
            return
    except ValueError:
        await message.answer(f"{pe('cross')} Введите число!")
        return

    await state.clear()
    await send_stars_invoice(message, amount)


@router.callback_query(F.data.startswith("topup_amount_"))
async def topup_preset_amount(callback: CallbackQuery):
    amount = int(callback.data.split("_")[2])
    await callback.answer()
    await send_stars_invoice(callback.message, amount, edit=True, user_id=callback.from_user.id)


async def send_stars_invoice(message: Message, amount: int, edit: bool = False, user_id: int = None):
    uid = user_id or message.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO payments (user_id, amount, status) VALUES (?, ?, 'pending')",
        (uid, amount)
    )
    payment_db_id = c.lastrowid
    conn.commit()
    conn.close()

    title = f"Пополнение на {amount} ⭐"
    description = f"Пополнение баланса Gift Bot на {amount} звёзд"

    try:
        await bot.send_invoice(
            chat_id=uid,
            title=title,
            description=description,
            payload=f"topup_{payment_db_id}_{amount}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=f"{amount} Stars", amount=amount)],
            start_parameter=f"topup_{amount}"
        )
    except Exception as e:
        logger.error(f"Ошибка создания invoice: {e}")
        await bot.send_message(uid, f"{pe('cross')} Ошибка создания платежа: {e}")


# ============================================================
# PRE-CHECKOUT
# ============================================================

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# ============================================================
# УСПЕШНАЯ ОПЛАТА
# ============================================================

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if payload.startswith("topup_"):
        parts = payload.split("_")
        payment_db_id = int(parts[1])
        amount = int(parts[2])
        user_id = message.from_user.id

        update_stars(user_id, amount)

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "UPDATE payments SET status = 'completed', tg_payment_id = ? WHERE payment_id = ?",
            (payment.telegram_payment_charge_id, payment_db_id)
        )
        conn.commit()
        conn.close()

        new_balance = get_stars(user_id)
        await message.answer(
            f"{pe('check')} <b>Оплата прошла успешно!</b>\n\n"
            f"{pe('star')} Зачислено: <b>{amount} {pe('star')}</b>\n"
            f"{pe('money')} Новый баланс: <b>{new_balance} {pe('star')}</b>"
        )

    elif payload.startswith("stardom_"):
        parts = payload.split("_")
        level = int(parts[1])
        user_id = message.from_user.id
        await activate_stardom(user_id, level)

    elif payload.startswith("buy_gift_"):
        parts = payload.split("_")
        gift_id = int(parts[2])
        target_id = int(parts[3])
        buyer_id = message.from_user.id
        await finalize_gift_purchase(buyer_id, target_id, gift_id, message)

    elif payload.startswith("buy_limited_"):
        parts = payload.split("_")
        limit_id = int(parts[2])
        target_id = int(parts[3])
        buyer_id = message.from_user.id
        await finalize_limited_purchase(buyer_id, target_id, limit_id, message)


async def activate_stardom(user_id: int, level: int):
    if level not in STARDOM_LEVELS:
        return
    sd = STARDOM_LEVELS[level]
    expires = datetime.now() + timedelta(days=sd["duration_months"] * 30)

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET stardom_level = ?, stardom_expires = ? WHERE user_id = ?",
        (level, expires.isoformat(), user_id)
    )

    counter = get_next_counter("gift_purchase_counter")
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, gift_name, gift_emoji, rarity, is_nft, is_limited) "
        "VALUES (?, ?, ?, ?, 'rare', 0, 0)",
        (counter, user_id, sd["exclusive_gift"], sd["exclusive_emoji"])
    )
    conn.commit()
    conn.close()

    is_new = grant_achievement(user_id, "first_stardom")

    text = (
        f"{pe('stardom')} <b>Stardom активирован!</b>\n\n"
        f"{pe('sparkles')} Уровень: <b>{sd['name']}</b>\n"
        f"{pe('date')} Действует до: <b>{expires.strftime('%d.%m.%Y')}</b>\n"
        f"{pe('gift')} Получен подарок: {sd['exclusive_emoji']} <b>{sd['exclusive_gift']}</b>\n\n"
        f"{pe('sparkles')} Ваши привилегии:\n"
        f"├ Комиссия создания NFT: {sd['nft_create_fee']} {pe('star')}\n"
        f"├ Комиссия передачи NFT: {sd['nft_transfer_fee']} {pe('star')}\n"
        f"└ Комиссия передачи подарка: {sd['gift_transfer_fee']} {pe('star')}"
    )
    if is_new:
        text += f"\n\n{pe('achieve')} {pe('medal')} <b>Достижение разблокировано: Звёздный статус!</b>"

    await send_notification(user_id, text)


async def finalize_gift_purchase(buyer_id: int, target_id: int, gift_id: int, message: Message):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ? AND is_active = 1", (gift_id,))
    gift = c.fetchone()

    if not gift:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок не найден!")
        return

    gift = dict(gift)

    if gift["quantity"] > 0 and gift["sold"] >= gift["quantity"]:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок закончился!")
        return

    counter = get_next_counter("gift_purchase_counter")
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, gift_id, gift_name, gift_emoji, rarity) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (counter, target_id, gift_id, gift["name"], gift["emoji"], gift["rarity"])
    )

    if gift["quantity"] > 0:
        c.execute("UPDATE gifts SET sold = sold + 1 WHERE gift_id = ?", (gift_id,))

    conn.commit()
    conn.close()

    is_new = grant_achievement(target_id, "first_gift")

    buyer_text = (
        f"{pe('check')} <b>Подарок куплен!</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>\n"
    )
    if target_id != buyer_id:
        buyer_text += f"{pe('send')} Отправлен пользователю: <code>{target_id}</code>\n"
    if is_new and target_id == buyer_id:
        buyer_text += f"\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый подарок!</b>"

    await message.answer(buyer_text)

    if target_id != buyer_id:
        recv_text = (
            f"{pe('gift')} <b>Вам подарили!</b>\n\n"
            f"{gift['emoji']} <b>{gift['name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('profile')} От: <code>{buyer_id}</code>"
        )
        if is_new:
            recv_text += f"\n\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый подарок!</b>"
        await send_notification(target_id, recv_text)


async def finalize_limited_purchase(buyer_id: int, target_id: int, limit_id: int, message: Message):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM limited_gifts WHERE limit_id = ? AND is_active = 1", (limit_id,))
    lg = c.fetchone()

    if not lg:
        conn.close()
        await message.answer(f"{pe('cross')} Лимитированный подарок не найден!")
        return

    lg = dict(lg)

    try:
        expires = datetime.fromisoformat(lg["expires_at"])
        if datetime.now() > expires:
            c.execute("UPDATE limited_gifts SET is_active = 0 WHERE limit_id = ?", (limit_id,))
            conn.commit()
            conn.close()
            await message.answer(f"{pe('cross')} Лимитированный подарок истёк!")
            return
    except Exception:
        pass

    counter = get_next_counter("gift_purchase_counter")
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, limit_id, gift_name, gift_emoji, rarity, is_limited) "
        "VALUES (?, ?, ?, ?, ?, 'rare', 1)",
        (counter, target_id, limit_id, lg["name"], lg["emoji"])
    )
    c.execute("UPDATE limited_gifts SET sold = sold + 1 WHERE limit_id = ?", (limit_id,))
    conn.commit()
    conn.close()

    is_new = grant_achievement(target_id, "first_gift")

    text = (
        f"{pe('check')} <b>Лимитированный подарок куплен!</b>\n\n"
        f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b> {pe('fire')}\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>\n"
    )
    if target_id != buyer_id:
        text += f"{pe('send')} Отправлен: <code>{target_id}</code>\n"
    if is_new and target_id == buyer_id:
        text += f"\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый подарок!</b>"

    await message.answer(text)

    if target_id != buyer_id:
        await send_notification(target_id,
            f"{pe('gift')} <b>Вам подарили лимитированный подарок!</b>\n\n"
            f"{lg['emoji']} <b>{lg['name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('profile')} От: <code>{buyer_id}</code>"
        )


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

@router.callback_query(F.data == "achievements")
async def show_achievements(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_achs = get_user_achievements(user_id)

    text = f"{pe('achieve')} <b>Ваши достижения</b>\n\n"

    for key, ach in ACHIEVEMENTS.items():
        if key in user_achs:
            text += f"{pe('check')} <b>{ach['name']}</b>\n   {ach['desc']}\n\n"
        else:
            text += f"{pe('lock')} <b>{ach['name']}</b>\n   {ach['desc']}\n\n"

    text += f"\n{pe('leaderboard')} Разблокировано: <b>{len(user_achs)}/{len(ACHIEVEMENTS)}</b>"

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Назад", "back_profile", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# ДРУЗЬЯ
# ============================================================

@router.message(F.text.endswith("Друзья"))
async def show_friends_menu(message: Message):
    user_id = message.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT f.friend_id, u.first_name, u.username 
        FROM friends f 
        LEFT JOIN users u ON f.friend_id = u.user_id 
        WHERE f.user_id = ?
        ORDER BY f.added_at DESC
    """, (user_id,))
    friends_list = [dict(row) for row in c.fetchall()]
    conn.close()

    text = f"{pe('friends')} <b>Ваши друзья</b>\n\n"

    if not friends_list:
        text += f"{pe('package')} У вас пока нет друзей.\n\n"
        text += f"Добавьте друга: /add_friend <ID>\n"
    else:
        for i, fr in enumerate(friends_list, 1):
            name = fr["first_name"] or "Неизвестный"
            uname = f"@{fr['username']}" if fr["username"] else ""
            text += f"{i}. {pe('profile')} <b>{name}</b> {uname}\n   {pe('id')} <code>{fr['friend_id']}</code>\n\n"

    text += (
        f"\n<b>Команды:</b>\n"
        f"├ /add_friend &lt;ID&gt; — Добавить\n"
        f"├ /del_friend &lt;ID&gt; — Удалить\n"
        f"└ /send_friend &lt;friend_ID&gt; &lt;inv_id&gt; — Передать подарок другу"
    )

    kb = InlineKeyboardBuilder()
    for fr in friends_list[:5]:
        name = fr["first_name"] or "?"
        kb.row(make_inline_button(f"Передать → {name}", f"friend_send_{fr['friend_id']}", "send"))

    await message.answer(text, reply_markup=kb.as_markup() if friends_list else None)


@router.message(Command("add_friend"))
async def cmd_add_friend(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /add_friend <ID пользователя>")
        return

    try:
        friend_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный ID!")
        return

    if friend_id == user_id:
        await message.answer(f"{pe('cross')} Нельзя добавить себя в друзья!")
        return

    friend = get_user(friend_id)
    if not friend:
        await message.answer(f"{pe('cross')} Пользователь не найден! Он должен сначала написать боту.")
        return

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO friends (user_id, friend_id) VALUES (?, ?)",
            (user_id, friend_id)
        )
        conn.commit()
        conn.close()

        await message.answer(
            f"{pe('check')} <b>Друг добавлен!</b>\n\n"
            f"{pe('profile')} {friend['first_name']} (ID: <code>{friend_id}</code>)"
        )

        await send_notification(friend_id,
            f"{pe('friends')} <b>Вас добавили в друзья!</b>\n\n"
            f"{pe('profile')} {message.from_user.first_name} (ID: <code>{user_id}</code>)\n"
            f"Добавьте в ответ: /add_friend {user_id}"
        )
    except sqlite3.IntegrityError:
        conn.close()
        await message.answer(f"{pe('cross')} Этот пользователь уже у вас в друзьях!")


@router.message(Command("del_friend"))
async def cmd_del_friend(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /del_friend <ID>")
        return

    try:
        friend_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный ID!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM friends WHERE user_id = ? AND friend_id = ?", (user_id, friend_id))
    if c.rowcount > 0:
        conn.commit()
        conn.close()
        await message.answer(f"{pe('check')} Друг (ID: <code>{friend_id}</code>) удалён!")
    else:
        conn.close()
        await message.answer(f"{pe('cross')} Этот пользователь не в вашем списке друзей!")


@router.message(Command("send_friend"))
async def cmd_send_friend(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /send_friend <friend_ID> <inv_id>")
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Использование: /send_friend <friend_ID> <inv_id>")
        return

    try:
        friend_id = int(parts[0])
        inv_id = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM friends WHERE user_id = ? AND friend_id = ?", (user_id, friend_id))
    if not c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот пользователь не в вашем списке друзей!")
        return
    conn.close()

    fee = get_gift_transfer_fee(user_id)
    stars = get_stars(user_id)

    if stars < fee:
        await message.answer(f"{pe('cross')} Недостаточно звёзд! Нужно {fee} {pe('star')}, у вас {stars} {pe('star')}")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, user_id))
    item = c.fetchone()

    if not item:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок не найден в вашем инвентаре!")
        return

    item = dict(item)

    c.execute("UPDATE inventory SET user_id = ? WHERE inv_id = ?", (friend_id, inv_id))
    conn.commit()
    conn.close()

    update_stars(user_id, -fee)

    new_balance = get_stars(user_id)
    await message.answer(
        f"{pe('check')} <b>Подарок передан другу!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('send')} Получатель: <code>{friend_id}</code>\n"
        f"{pe('money')} Комиссия: {fee} {pe('star')}\n"
        f"{pe('money')} Баланс: {new_balance} {pe('star')}"
    )

    await send_notification(friend_id,
        f"{pe('gift')} <b>Вы получили подарок от друга!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('profile')} От: {message.from_user.first_name} (<code>{user_id}</code>)\n"
        f"{pe('id')} Inv ID: <code>{inv_id}</code>"
    )


@router.callback_query(F.data.startswith("friend_send_"))
async def friend_send_callback(callback: CallbackQuery, state: FSMContext):
    friend_id = int(callback.data.split("_")[2])
    await state.update_data(friend_target=friend_id)
    await state.set_state(GiftBuyTarget.waiting_user_id)

    await callback.message.answer(
        f"{pe('send')} <b>Введите Inv ID подарка для передачи другу (ID: {friend_id}):</b>"
    )
    await callback.answer()


@router.message(GiftBuyTarget.waiting_user_id)
async def friend_send_inv_id(message: Message, state: FSMContext):
    data = await state.get_data()
    friend_id = data.get("friend_target")
    await state.clear()

    if not friend_id:
        await message.answer(f"{pe('cross')} Ошибка! Попробуйте снова.")
        return

    try:
        inv_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Введите число!")
        return

    user_id = message.from_user.id
    fee = get_gift_transfer_fee(user_id)
    stars = get_stars(user_id)

    if stars < fee:
        await message.answer(f"{pe('cross')} Недостаточно звёзд! Нужно {fee} {pe('star')}")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, user_id))
    item = c.fetchone()

    if not item:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок не найден в вашем инвентаре!")
        return

    item = dict(item)
    c.execute("UPDATE inventory SET user_id = ? WHERE inv_id = ?", (friend_id, inv_id))
    conn.commit()
    conn.close()

    update_stars(user_id, -fee)

    await message.answer(
        f"{pe('check')} <b>Подарок передан!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b> → <code>{friend_id}</code>\n"
        f"{pe('money')} Комиссия: {fee} {pe('star')}"
    )

    await send_notification(friend_id,
        f"{pe('gift')} <b>Вам передали подарок!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('profile')} От: {message.from_user.first_name}\n"
        f"{pe('id')} Inv ID: <code>{inv_id}</code>"
    )


# ============================================================
# /rules
# ============================================================

@router.message(Command("rules"))
async def cmd_rules(message: Message):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT text FROM rules WHERE id = 1")
    row = c.fetchone()
    conn.close()

    rules_text = row["text"] if row else "Правила не установлены."

    await message.answer(f"{pe('rules_emoji')} <b>Правила</b>\n\n{rules_text}")


# ============================================================
# /friends (альтернативный вызов)
# ============================================================

@router.message(Command("friends"))
async def cmd_friends(message: Message):
    message.text = f"{pe_plain('friends')} Друзья"
    await show_friends_menu(message)


# Конец части 2
# ============================================================
# ============================================================
# ЧАСТЬ 3: Маркет #1, Маркет #2, Покупка, Лимитированные, Промокоды
# ============================================================

# ============================================================
# МАРКЕТ #1 (COMMON подарки)
# ============================================================

@router.message(F.text.endswith("Маркет"))
async def show_market1(message: Message):
    if "#2" in message.text:
        return

    user_id = message.from_user.id
    user = get_user(user_id)

    if user and user["is_buy_banned"]:
        await message.answer(
            f"{pe('ban_emoji')} <b>Вам запрещено покупать подарки!</b>\n"
            f"{pe('rules_emoji')} Причина: {user['buy_ban_reason']}"
        )
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE rarity = 'common' AND is_active = 1 ORDER BY gift_id")
    gifts = [dict(row) for row in c.fetchall()]
    conn.close()

    if not gifts:
        await message.answer(
            f"{pe('market')} <b>Маркет</b>\n\n"
            f"{pe('package')} В маркете пока нет подарков."
        )
        return

    text = (
        f"{pe('market')} <b>Маркет — Обычные подарки</b> {pe('common')}\n\n"
        f"{pe('money')} Ваш баланс: <b>{user['stars']} {pe('star')}</b>\n\n"
    )

    kb = InlineKeyboardBuilder()

    for gift in gifts:
        qty_text = "∞" if gift["quantity"] == 0 else f"{gift['quantity'] - gift['sold']}/{gift['quantity']}"
        text += (
            f"{'─' * 25}\n"
            f"{pe('common')} {gift['emoji']} <b>{gift['name']}</b>\n"
            f"   {pe('money')} Цена: <b>{gift['price']} {pe('star')}</b>\n"
            f"   {pe('package')} Осталось: <b>{qty_text}</b>\n"
            f"   {pe('id')} ID: <code>{gift['gift_id']}</code>\n\n"
        )

        available = gift["quantity"] == 0 or gift["sold"] < gift["quantity"]
        if available:
            kb.row(make_inline_button(
                f"Купить {gift['emoji']} {gift['name']} — {gift['price']}{pe_plain('star')}",
                f"buy_common_{gift['gift_id']}", "buy"
            ))

    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# МАРКЕТ #2 (RARE подарки + лимитированные)
# ============================================================

@router.message(F.text.endswith("Маркет #2"))
async def show_market2(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if user and user["is_buy_banned"]:
        await message.answer(
            f"{pe('ban_emoji')} <b>Вам запрещено покупать подарки!</b>\n"
            f"{pe('rules_emoji')} Причина: {user['buy_ban_reason']}"
        )
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM gifts WHERE rarity = 'rare' AND is_active = 1 ORDER BY gift_id")
    rare_gifts = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM limited_gifts WHERE is_active = 1 ORDER BY limit_id")
    limited_raw = [dict(row) for row in c.fetchall()]
    conn.close()

    limited_gifts = []
    now = datetime.now()
    for lg in limited_raw:
        try:
            expires = datetime.fromisoformat(lg["expires_at"])
            if now <= expires:
                limited_gifts.append(lg)
            else:
                conn2 = get_db()
                conn2.execute("UPDATE limited_gifts SET is_active = 0 WHERE limit_id = ?", (lg["limit_id"],))
                conn2.commit()
                conn2.close()
        except Exception:
            limited_gifts.append(lg)

    if not rare_gifts and not limited_gifts:
        await message.answer(
            f"{pe('market2')} <b>Маркет #2</b>\n\n"
            f"{pe('package')} В маркете пока нет редких подарков."
        )
        return

    text = (
        f"{pe('market2')} <b>Маркет #2 — Редкие подарки</b> {pe('rare')}\n\n"
        f"{pe('money')} Ваш баланс: <b>{user['stars']} {pe('star')}</b>\n\n"
    )

    kb = InlineKeyboardBuilder()

    if rare_gifts:
        text += f"<b>{pe('rare')} Редкие подарки:</b>\n\n"
        for gift in rare_gifts:
            qty_text = "∞" if gift["quantity"] == 0 else f"{gift['quantity'] - gift['sold']}/{gift['quantity']}"
            text += (
                f"{'─' * 25}\n"
                f"{pe('rare')} {gift['emoji']} <b>{gift['name']}</b>\n"
                f"   {pe('money')} Цена: <b>{gift['price']} {pe('star')}</b>\n"
                f"   {pe('package')} Осталось: <b>{qty_text}</b>\n"
                f"   {pe('id')} ID: <code>{gift['gift_id']}</code>\n"
                f"   {pe('upgrade')} Можно улучшить до NFT!\n\n"
            )

            available = gift["quantity"] == 0 or gift["sold"] < gift["quantity"]
            if available:
                kb.row(make_inline_button(
                    f"Купить {gift['emoji']} {gift['name']} — {gift['price']}{pe_plain('star')}",
                    f"buy_rare_{gift['gift_id']}", "buy"
                ))

    if limited_gifts:
        text += f"\n<b>{pe('limit')} Лимитированные подарки:</b>\n\n"
        for lg in limited_gifts:
            try:
                exp_dt = datetime.fromisoformat(lg["expires_at"])
                time_left = exp_dt - now
                hours_left = int(time_left.total_seconds() // 3600)
                mins_left = int((time_left.total_seconds() % 3600) // 60)
                time_str = f"{hours_left}ч {mins_left}м"
            except Exception:
                time_str = "Неизвестно"

            text += (
                f"{'─' * 25}\n"
                f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b> {pe('fire')} ЛИМИТИРОВАННЫЙ\n"
                f"   {pe('money')} Цена: <b>{lg['price']} {pe('star')}</b>\n"
                f"   {pe('clock')} Осталось: <b>{time_str}</b>\n"
                f"   {pe('leaderboard')} Продано: <b>{lg['sold']}</b>\n"
                f"   {pe('id')} Limit ID: <code>{lg['limit_id']}</code>\n\n"
            )

            kb.row(make_inline_button(
                f"Купить {lg['emoji']} {lg['name']} — {lg['price']}{pe_plain('star')}",
                f"buy_limited_{lg['limit_id']}", "limit"
            ))

    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# ПОКУПКА COMMON — ВЫБОР ПОЛУЧАТЕЛЯ
# ============================================================

@router.callback_query(F.data.startswith("buy_common_"))
async def buy_common_start(callback: CallbackQuery):
    gift_id = int(callback.data.split("_")[2])

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ? AND is_active = 1", (gift_id,))
    gift = c.fetchone()
    conn.close()

    if not gift:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    gift = dict(gift)

    if gift["quantity"] > 0 and gift["sold"] >= gift["quantity"]:
        await callback.answer(f"{pe_plain('cross')} Подарок закончился!", show_alert=True)
        return

    user = get_user(callback.from_user.id)
    if user and user["is_buy_banned"]:
        await callback.answer(f"{pe_plain('ban_emoji')} Вам запрещено покупать!", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Купить себе", f"buy_self_common_{gift_id}", "gift"))
    kb.row(make_inline_button("Купить кому-то (по ID)", f"buy_other_common_{gift_id}", "send"))
    kb.row(make_inline_button("Отмена", "cancel_buy", "cross"))

    await callback.message.edit_text(
        f"{pe('buy')} <b>Покупка подарка</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"{pe('money')} Цена: <b>{gift['price']} {pe('star')}</b>\n\n"
        f"Кому купить?",
        reply_markup=kb.as_markup()
    )


# ============================================================
# ПОКУПКА RARE — ВЫБОР ПОЛУЧАТЕЛЯ
# ============================================================

@router.callback_query(F.data.startswith("buy_rare_"))
async def buy_rare_start(callback: CallbackQuery):
    gift_id = int(callback.data.split("_")[2])

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ? AND is_active = 1", (gift_id,))
    gift = c.fetchone()
    conn.close()

    if not gift:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    gift = dict(gift)

    if gift["quantity"] > 0 and gift["sold"] >= gift["quantity"]:
        await callback.answer(f"{pe_plain('cross')} Подарок закончился!", show_alert=True)
        return

    user = get_user(callback.from_user.id)
    if user and user["is_buy_banned"]:
        await callback.answer(f"{pe_plain('ban_emoji')} Вам запрещено покупать!", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Купить себе", f"buy_self_rare_{gift_id}", "gift"))
    kb.row(make_inline_button("Купить кому-то (по ID)", f"buy_other_rare_{gift_id}", "send"))
    kb.row(make_inline_button("Отмена", "cancel_buy", "cross"))

    await callback.message.edit_text(
        f"{pe('buy')} <b>Покупка редкого подарка</b>\n\n"
        f"{pe('rare')} {gift['emoji']} <b>{gift['name']}</b>\n"
        f"{pe('money')} Цена: <b>{gift['price']} {pe('star')}</b>\n\n"
        f"Кому купить?",
        reply_markup=kb.as_markup()
    )


# ============================================================
# ПОКУПКА ЛИМИТИРОВАННОГО — ВЫБОР ПОЛУЧАТЕЛЯ
# ============================================================

@router.callback_query(F.data.startswith("buy_limited_"))
async def buy_limited_start(callback: CallbackQuery):
    limit_id = int(callback.data.split("_")[2])

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM limited_gifts WHERE limit_id = ? AND is_active = 1", (limit_id,))
    lg = c.fetchone()
    conn.close()

    if not lg:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    lg = dict(lg)

    try:
        expires = datetime.fromisoformat(lg["expires_at"])
        if datetime.now() > expires:
            await callback.answer(f"{pe_plain('cross')} Лимитированный подарок истёк!", show_alert=True)
            return
    except Exception:
        pass

    user = get_user(callback.from_user.id)
    if user and user["is_buy_banned"]:
        await callback.answer(f"{pe_plain('ban_emoji')} Вам запрещено покупать!", show_alert=True)
        return

    try:
        exp_dt = datetime.fromisoformat(lg["expires_at"])
        time_left = exp_dt - datetime.now()
        hours_left = int(time_left.total_seconds() // 3600)
        time_str = f"{hours_left}ч"
    except Exception:
        time_str = "?"

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Купить себе", f"buy_self_limited_{limit_id}", "gift"))
    kb.row(make_inline_button("Купить кому-то (по ID)", f"buy_other_limited_{limit_id}", "send"))
    kb.row(make_inline_button("Отмена", "cancel_buy", "cross"))

    await callback.message.edit_text(
        f"{pe('limit')} <b>Покупка лимитированного подарка</b>\n\n"
        f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b> {pe('fire')}\n"
        f"{pe('money')} Цена: <b>{lg['price']} {pe('star')}</b>\n"
        f"{pe('clock')} Осталось: <b>{time_str}</b>\n\n"
        f"Кому купить?",
        reply_markup=kb.as_markup()
    )


# ============================================================
# ОТМЕНА ПОКУПКИ
# ============================================================

@router.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f"{pe('cross')} Покупка отменена.")
    await callback.answer()


# ============================================================
# ПОКУПКА СЕБЕ
# ============================================================

@router.callback_query(F.data.startswith("buy_self_common_"))
async def buy_self_common(callback: CallbackQuery):
    gift_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    await process_gift_purchase(callback, user_id, user_id, gift_id, "common")


@router.callback_query(F.data.startswith("buy_self_rare_"))
async def buy_self_rare(callback: CallbackQuery):
    gift_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    await process_gift_purchase(callback, user_id, user_id, gift_id, "rare")


@router.callback_query(F.data.startswith("buy_self_limited_"))
async def buy_self_limited(callback: CallbackQuery):
    limit_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    await process_limited_purchase(callback, user_id, user_id, limit_id)


# ============================================================
# ПОКУПКА ДРУГОМУ — ВВОД ID
# ============================================================

@router.callback_query(F.data.startswith("buy_other_common_"))
async def buy_other_common(callback: CallbackQuery, state: FSMContext):
    gift_id = int(callback.data.split("_")[3])
    await state.update_data(buy_gift_id=gift_id, buy_type="common")
    await state.set_state(BuyGiftStates.waiting_target)
    await callback.message.edit_text(
        f"{pe('send')} <b>Введите ID пользователя-получателя:</b>"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_other_rare_"))
async def buy_other_rare(callback: CallbackQuery, state: FSMContext):
    gift_id = int(callback.data.split("_")[3])
    await state.update_data(buy_gift_id=gift_id, buy_type="rare")
    await state.set_state(BuyGiftStates.waiting_target)
    await callback.message.edit_text(
        f"{pe('send')} <b>Введите ID пользователя-получателя:</b>"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_other_limited_"))
async def buy_other_limited(callback: CallbackQuery, state: FSMContext):
    limit_id = int(callback.data.split("_")[3])
    await state.update_data(buy_limit_id=limit_id, buy_type="limited")
    await state.set_state(BuyGiftStates.waiting_target)
    await callback.message.edit_text(
        f"{pe('send')} <b>Введите ID пользователя-получателя:</b>"
    )
    await callback.answer()


@router.message(BuyGiftStates.waiting_target)
async def buy_target_entered(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Введите числовой ID!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден! Он должен сначала написать боту.")
        return

    data = await state.get_data()
    await state.clear()

    buy_type = data.get("buy_type")
    user_id = message.from_user.id

    if buy_type == "limited":
        limit_id = data.get("buy_limit_id")
        await process_limited_purchase_msg(message, user_id, target_id, limit_id)
    else:
        gift_id = data.get("buy_gift_id")
        await process_gift_purchase_msg(message, user_id, target_id, gift_id, buy_type)


# ============================================================
# ОБРАБОТКА ПОКУПКИ ОБЫЧНОГО/РЕДКОГО — CALLBACK
# ============================================================

async def process_gift_purchase(callback: CallbackQuery, buyer_id: int, target_id: int, gift_id: int, rarity: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ? AND is_active = 1", (gift_id,))
    gift = c.fetchone()
    conn.close()

    if not gift:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    gift = dict(gift)

    if gift["quantity"] > 0 and gift["sold"] >= gift["quantity"]:
        await callback.answer(f"{pe_plain('cross')} Подарок закончился!", show_alert=True)
        return

    price = gift["price"]
    stars = get_stars(buyer_id)

    if stars < price:
        kb = InlineKeyboardBuilder()
        kb.row(make_inline_button(
            f"Оплатить {price}{pe_plain('star')} через Telegram",
            f"pay_tg_gift_{gift_id}_{target_id}", "star"
        ))
        kb.row(make_inline_button("Отмена", "cancel_buy", "cross"))
        await callback.message.edit_text(
            f"{pe('cross')} <b>Недостаточно звёзд!</b>\n\n"
            f"{pe('money')} Нужно: <b>{price} {pe('star')}</b>\n"
            f"{pe('money')} У вас: <b>{stars} {pe('star')}</b>\n\n"
            f"Вы можете оплатить звёздами Telegram:",
            reply_markup=kb.as_markup()
        )
        return

    update_stars(buyer_id, -price)

    counter = get_next_counter("gift_purchase_counter")
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, gift_id, gift_name, gift_emoji, rarity) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (counter, target_id, gift_id, gift["name"], gift["emoji"], gift["rarity"])
    )
    if gift["quantity"] > 0:
        c.execute("UPDATE gifts SET sold = sold + 1 WHERE gift_id = ?", (gift_id,))
    conn.commit()
    conn.close()

    is_new = grant_achievement(target_id, "first_gift")
    new_balance = get_stars(buyer_id)

    result_text = (
        f"{pe('check')} <b>Подарок куплен!</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>\n"
        f"{pe('money')} Списано: <b>{price} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>\n"
    )
    if target_id != buyer_id:
        result_text += f"{pe('send')} Отправлен: <code>{target_id}</code>\n"
    if is_new and target_id == buyer_id:
        result_text += f"\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый подарок!</b>"

    await callback.message.edit_text(result_text)

    if target_id != buyer_id:
        await send_notification(target_id,
            f"{pe('gift')} <b>Вам подарили!</b>\n\n"
            f"{gift['emoji']} <b>{gift['name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('profile')} От: <code>{buyer_id}</code>"
        )


# ============================================================
# ОБРАБОТКА ПОКУПКИ — MESSAGE
# ============================================================

async def process_gift_purchase_msg(message: Message, buyer_id: int, target_id: int, gift_id: int, rarity: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ? AND is_active = 1", (gift_id,))
    gift = c.fetchone()
    conn.close()

    if not gift:
        await message.answer(f"{pe('cross')} Подарок не найден!")
        return

    gift = dict(gift)

    if gift["quantity"] > 0 and gift["sold"] >= gift["quantity"]:
        await message.answer(f"{pe('cross')} Подарок закончился!")
        return

    price = gift["price"]
    stars = get_stars(buyer_id)

    if stars < price:
        try:
            await bot.send_invoice(
                chat_id=buyer_id,
                title=f"Покупка {gift['name']}",
                description=f"Подарок {gift['name']} для пользователя {target_id}",
                payload=f"buy_gift_{gift_id}_{target_id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=f"{gift['name']}", amount=price)]
            )
            await message.answer(
                f"{pe('topup')} <b>Недостаточно звёзд на балансе.</b>\n"
                f"Отправлен счёт на оплату через Telegram Stars!"
            )
        except Exception as e:
            await message.answer(f"{pe('cross')} Ошибка создания платежа: {e}")
        return

    update_stars(buyer_id, -price)

    counter = get_next_counter("gift_purchase_counter")
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, gift_id, gift_name, gift_emoji, rarity) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (counter, target_id, gift_id, gift["name"], gift["emoji"], gift["rarity"])
    )
    if gift["quantity"] > 0:
        c.execute("UPDATE gifts SET sold = sold + 1 WHERE gift_id = ?", (gift_id,))
    conn.commit()
    conn.close()

    is_new = grant_achievement(target_id, "first_gift")
    new_balance = get_stars(buyer_id)

    result_text = (
        f"{pe('check')} <b>Подарок куплен!</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b>\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>\n"
        f"{pe('money')} Списано: <b>{price} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>\n"
    )
    if target_id != buyer_id:
        result_text += f"{pe('send')} Отправлен: <code>{target_id}</code>\n"
    if is_new and target_id == buyer_id:
        result_text += f"\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый подарок!</b>"

    await message.answer(result_text)

    if target_id != buyer_id:
        await send_notification(target_id,
            f"{pe('gift')} <b>Вам подарили!</b>\n\n"
            f"{gift['emoji']} <b>{gift['name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('profile')} От: <code>{buyer_id}</code>"
        )


# ============================================================
# ОПЛАТА ЧЕРЕЗ TG STARS
# ============================================================

@router.callback_query(F.data.startswith("pay_tg_gift_"))
async def pay_tg_gift(callback: CallbackQuery):
    parts = callback.data.split("_")
    gift_id = int(parts[3])
    target_id = int(parts[4])
    buyer_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ? AND is_active = 1", (gift_id,))
    gift = c.fetchone()
    conn.close()

    if not gift:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    gift = dict(gift)

    try:
        desc = f"Подарок {gift['name']}"
        if target_id != buyer_id:
            desc += f" для пользователя {target_id}"
        await bot.send_invoice(
            chat_id=buyer_id,
            title=f"Покупка {gift['name']}",
            description=desc,
            payload=f"buy_gift_{gift_id}_{target_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=gift["name"], amount=gift["price"])]
        )
        await callback.answer(f"{pe_plain('topup')} Счёт отправлен!", show_alert=True)
    except Exception as e:
        await callback.answer(f"{pe_plain('cross')} Ошибка: {e}", show_alert=True)


# ============================================================
# ПОКУПКА ЛИМИТИРОВАННОГО — CALLBACK
# ============================================================

async def process_limited_purchase(callback: CallbackQuery, buyer_id: int, target_id: int, limit_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM limited_gifts WHERE limit_id = ? AND is_active = 1", (limit_id,))
    lg = c.fetchone()
    conn.close()

    if not lg:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    lg = dict(lg)

    try:
        expires = datetime.fromisoformat(lg["expires_at"])
        if datetime.now() > expires:
            await callback.answer(f"{pe_plain('cross')} Лимитированный подарок истёк!", show_alert=True)
            return
    except Exception:
        pass

    price = lg["price"]
    stars = get_stars(buyer_id)

    if stars < price:
        kb = InlineKeyboardBuilder()
        kb.row(make_inline_button(
            f"Оплатить {price}{pe_plain('star')} через Telegram",
            f"pay_tg_limited_{limit_id}_{target_id}", "star"
        ))
        kb.row(make_inline_button("Отмена", "cancel_buy", "cross"))
        await callback.message.edit_text(
            f"{pe('cross')} <b>Недостаточно звёзд!</b>\n"
            f"{pe('money')} Нужно: <b>{price} {pe('star')}</b> | У вас: <b>{stars} {pe('star')}</b>\n\n"
            f"Оплатите через Telegram Stars:",
            reply_markup=kb.as_markup()
        )
        return

    update_stars(buyer_id, -price)

    counter = get_next_counter("gift_purchase_counter")
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, limit_id, gift_name, gift_emoji, rarity, is_limited) "
        "VALUES (?, ?, ?, ?, ?, 'rare', 1)",
        (counter, target_id, limit_id, lg["name"], lg["emoji"])
    )
    c.execute("UPDATE limited_gifts SET sold = sold + 1 WHERE limit_id = ?", (limit_id,))
    conn.commit()
    conn.close()

    is_new = grant_achievement(target_id, "first_gift")
    new_balance = get_stars(buyer_id)

    result_text = (
        f"{pe('check')} <b>Лимитированный подарок куплен!</b>\n\n"
        f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b> {pe('fire')}\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>\n"
        f"{pe('money')} Списано: <b>{price} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>\n"
    )
    if target_id != buyer_id:
        result_text += f"{pe('send')} Отправлен: <code>{target_id}</code>\n"
    if is_new and target_id == buyer_id:
        result_text += f"\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый подарок!</b>"

    await callback.message.edit_text(result_text)

    if target_id != buyer_id:
        await send_notification(target_id,
            f"{pe('gift')} <b>Вам подарили лимитированный подарок!</b>\n\n"
            f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('profile')} От: <code>{buyer_id}</code>"
        )


# ============================================================
# ПОКУПКА ЛИМИТИРОВАННОГО — MESSAGE
# ============================================================

async def process_limited_purchase_msg(message: Message, buyer_id: int, target_id: int, limit_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM limited_gifts WHERE limit_id = ? AND is_active = 1", (limit_id,))
    lg = c.fetchone()
    conn.close()

    if not lg:
        await message.answer(f"{pe('cross')} Подарок не найден!")
        return

    lg = dict(lg)

    try:
        expires = datetime.fromisoformat(lg["expires_at"])
        if datetime.now() > expires:
            await message.answer(f"{pe('cross')} Лимитированный подарок истёк!")
            return
    except Exception:
        pass

    price = lg["price"]
    stars = get_stars(buyer_id)

    if stars < price:
        try:
            await bot.send_invoice(
                chat_id=buyer_id,
                title=f"Покупка {lg['name']}",
                description=f"Лимитированный подарок {lg['name']}",
                payload=f"buy_limited_{limit_id}_{target_id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=lg["name"], amount=price)]
            )
            await message.answer(f"{pe('topup')} Счёт на оплату отправлен!")
        except Exception as e:
            await message.answer(f"{pe('cross')} Ошибка: {e}")
        return

    update_stars(buyer_id, -price)

    counter = get_next_counter("gift_purchase_counter")
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, limit_id, gift_name, gift_emoji, rarity, is_limited) "
        "VALUES (?, ?, ?, ?, ?, 'rare', 1)",
        (counter, target_id, limit_id, lg["name"], lg["emoji"])
    )
    c.execute("UPDATE limited_gifts SET sold = sold + 1 WHERE limit_id = ?", (limit_id,))
    conn.commit()
    conn.close()

    is_new = grant_achievement(target_id, "first_gift")
    new_balance = get_stars(buyer_id)

    await message.answer(
        f"{pe('check')} <b>Лимитированный подарок куплен!</b>\n\n"
        f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b>\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    if target_id != buyer_id:
        await send_notification(target_id,
            f"{pe('gift')} <b>Вам подарили лимитированный подарок!</b>\n\n"
            f"{pe('limit')} {lg['emoji']} <b>{lg['name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('profile')} От: <code>{buyer_id}</code>"
        )


@router.callback_query(F.data.startswith("pay_tg_limited_"))
async def pay_tg_limited(callback: CallbackQuery):
    parts = callback.data.split("_")
    limit_id = int(parts[3])
    target_id = int(parts[4])
    buyer_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM limited_gifts WHERE limit_id = ? AND is_active = 1", (limit_id,))
    lg = c.fetchone()
    conn.close()

    if not lg:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    lg = dict(lg)

    try:
        await bot.send_invoice(
            chat_id=buyer_id,
            title=f"Покупка {lg['name']}",
            description=f"Лимитированный подарок {lg['name']}",
            payload=f"buy_limited_{limit_id}_{target_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=lg["name"], amount=lg["price"])]
        )
        await callback.answer(f"{pe_plain('topup')} Счёт отправлен!", show_alert=True)
    except Exception as e:
        await callback.answer(f"{pe_plain('cross')} Ошибка: {e}", show_alert=True)


# ============================================================
# ПРОМОКОДЫ — КНОПКА
# ============================================================

@router.message(F.text.endswith("Промокоды"))
async def show_promo_menu(message: Message):
    text = (
        f"{pe('promo')} <b>Промокоды</b>\n\n"
        f"{pe('promo')} Введите промокод командой:\n"
        f"/promo <код>\n\n"
        f"{pe('warning')} Каждый промокод можно использовать только 1 раз!"
    )
    await message.answer(text)


# ============================================================
# АКТИВАЦИЯ ПРОМОКОДА
# ============================================================

@router.message(Command("promo"))
async def cmd_promo(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /promo (код)")
        return

    code = command.args.strip().upper()

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM promocodes WHERE code = ? AND is_active = 1", (code,))
    promo = c.fetchone()

    if not promo:
        conn.close()
        await message.answer(f"{pe('cross')} Промокод <code>{code}</code> не найден или неактивен!")
        return

    promo = dict(promo)

    if promo["current_uses"] >= promo["max_uses"]:
        conn.close()
        await message.answer(f"{pe('cross')} Промокод <code>{code}</code> исчерпан!")
        return

    c.execute(
        "SELECT id FROM promo_uses WHERE user_id = ? AND promo_id = ?",
        (user_id, promo["promo_id"])
    )
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Вы уже использовали этот промокод!")
        return

    reward_type = promo["reward_type"]
    reward_value = promo["reward_value"]

    if reward_type == "stars":
        amount = int(reward_value)
        update_stars(user_id, amount)
        reward_text = f"{pe('money')} +{amount} {pe('star')}"

    elif reward_type == "gift":
        gift_name = reward_value
        counter = get_next_counter("gift_purchase_counter")
        c.execute(
            "INSERT INTO inventory (inv_id, user_id, gift_name, gift_emoji, rarity) "
            "VALUES (?, ?, ?, '🎁', 'common')",
            (counter, user_id, gift_name)
        )
        reward_text = f"{pe('gift')} Подарок: {gift_name} (Inv ID: {counter})"

    else:
        conn.close()
        await message.answer(f"{pe('cross')} Ошибка промокода!")
        return

    c.execute(
        "INSERT INTO promo_uses (user_id, promo_id) VALUES (?, ?)",
        (user_id, promo["promo_id"])
    )
    c.execute(
        "UPDATE promocodes SET current_uses = current_uses + 1 WHERE promo_id = ?",
        (promo["promo_id"],)
    )

    if promo["current_uses"] + 1 >= promo["max_uses"]:
        c.execute("UPDATE promocodes SET is_active = 0 WHERE promo_id = ?", (promo["promo_id"],))

    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Промокод активирован!</b>\n\n"
        f"{pe('promo')} Код: <code>{code}</code>\n"
        f"{pe('gift')} Награда: {reward_text}\n\n"
        f"{pe('sparkles')} Спасибо!"
    )


# Конец части 3
# ============================================================
# ============================================================
# ЧАСТЬ 4: NFT система, Улучшение до NFT, Торговля, Аукционы
# ============================================================

# ============================================================
# ТОРГОВЛЯ — КНОПКА МЕНЮ
# ============================================================

@router.message(F.text.endswith("Торговля"))
async def show_trade_menu(message: Message):
    user_id = message.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT t.*, n.gift_name, n.gift_emoji, n.model_name, n.model_chance,
               n.pattern_name, n.pattern_chance, n.bg_name, n.bg_chance,
               n.is_crafted, u.first_name, u.username
        FROM trades t
        JOIN nfts n ON t.nft_id = n.nft_id
        JOIN users u ON t.seller_id = u.user_id
        WHERE t.is_active = 1
        ORDER BY t.created_at DESC
        LIMIT 10
    """)
    trades = [dict(row) for row in c.fetchall()]
    conn.close()

    text = (
        f"{pe('trade')} <b>Торговая площадка NFT</b>\n\n"
        f"{pe('leaderboard')} Комиссия продавца: <b>15%</b>\n"
        f"{pe('rules_emoji')} Команды:\n"
        f"├ /trade &lt;nft_id&gt; &lt;цена&gt; — Выставить\n"
        f"└ /del_trade &lt;trade_id&gt; — Снять\n\n"
    )

    if not trades:
        text += f"{pe('package')} Нет активных предложений."
        await message.answer(text)
        return

    text += f"<b>{pe('fire')} Активные предложения:</b>\n\n"

    kb = InlineKeyboardBuilder()

    for t in trades:
        crafted = f" {pe('hammer')}" if t["is_crafted"] else ""
        seller_name = t["first_name"] or "?"
        seller_uname = f"@{t['username']}" if t["username"] else ""

        text += (
            f"{'─' * 28}\n"
            f"{pe('pin')} <b>Trade #{t['trade_id']}</b>\n"
            f"{t['gift_emoji']} <b>{t['gift_name']}</b> | NFT #{t['nft_id']}{crafted}\n"
            f"{pe('model')} Модель: <b>{t['model_name']}</b> ({t['model_chance']}%)\n"
            f"{pe('pattern')} Узор: <b>{t['pattern_name']}</b> ({t['pattern_chance']}%)\n"
            f"{pe('background')} Фон: <b>{t['bg_name']}</b> ({t['bg_chance']}%)\n"
            f"{pe('money')} Цена: <b>{t['price']} {pe('star')}</b>\n"
            f"{pe('seller')} Продавец: {seller_name} {seller_uname}\n\n"
        )

        kb.row(make_inline_button(
            f"Купить NFT #{t['nft_id']} — {t['price']}{pe_plain('star')}",
            f"buy_trade_{t['trade_id']}", "buy"
        ))

    kb.row(make_inline_button("Ещё предложения", "trade_page_1", "next"))

    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# ТОРГОВЛЯ — ПАГИНАЦИЯ
# ============================================================

@router.callback_query(F.data.startswith("trade_page_"))
async def trade_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    per_page = 5
    offset = page * per_page

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT t.*, n.gift_name, n.gift_emoji, n.model_name, n.model_chance,
               n.pattern_name, n.pattern_chance, n.bg_name, n.bg_chance,
               n.is_crafted, u.first_name, u.username
        FROM trades t
        JOIN nfts n ON t.nft_id = n.nft_id
        JOIN users u ON t.seller_id = u.user_id
        WHERE t.is_active = 1
        ORDER BY t.created_at DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    trades = [dict(row) for row in c.fetchall()]

    c.execute("SELECT COUNT(*) as cnt FROM trades WHERE is_active = 1")
    total = c.fetchone()["cnt"]
    conn.close()

    if not trades:
        await callback.answer(f"{pe_plain('package')} Больше нет предложений!", show_alert=True)
        return

    total_pages = max(1, (total + per_page - 1) // per_page)
    text = f"{pe('trade')} <b>Торговля</b> (стр. {page + 1}/{total_pages}):\n\n"

    kb = InlineKeyboardBuilder()

    for t in trades:
        crafted = f" {pe('hammer')}" if t["is_crafted"] else ""
        text += (
            f"{'─' * 28}\n"
            f"{pe('pin')} <b>Trade #{t['trade_id']}</b>\n"
            f"{t['gift_emoji']} <b>{t['gift_name']}</b> | NFT #{t['nft_id']}{crafted}\n"
            f"{pe('model')} {t['model_name']} ({t['model_chance']}%) | "
            f"{pe('pattern')} {t['pattern_name']} ({t['pattern_chance']}%) | "
            f"{pe('background')} {t['bg_name']} ({t['bg_chance']}%)\n"
            f"{pe('money')} <b>{t['price']} {pe('star')}</b> | {pe('seller')} {t['first_name']}\n\n"
        )
        kb.row(make_inline_button(
            f"Купить #{t['nft_id']} — {t['price']}{pe_plain('star')}",
            f"buy_trade_{t['trade_id']}", "buy"
        ))

    nav = []
    if page > 0:
        nav.append(make_inline_button("Назад", f"trade_page_{page - 1}", "back"))
    if (page + 1) * per_page < total:
        nav.append(make_inline_button("Далее", f"trade_page_{page + 1}", "next"))
    if nav:
        kb.row(*nav)

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# ПОКУПКА NFT С ТОРГОВЛИ
# ============================================================

@router.callback_query(F.data.startswith("buy_trade_"))
async def buy_trade(callback: CallbackQuery):
    trade_id = int(callback.data.split("_")[2])
    buyer_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT t.*, n.gift_name, n.gift_emoji, n.model_name, n.model_chance,
               n.pattern_name, n.pattern_chance, n.bg_name, n.bg_chance
        FROM trades t
        JOIN nfts n ON t.nft_id = n.nft_id
        WHERE t.trade_id = ? AND t.is_active = 1
    """, (trade_id,))
    trade = c.fetchone()

    if not trade:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Предложение не найдено или уже продано!", show_alert=True)
        return

    trade = dict(trade)

    if trade["seller_id"] == buyer_id:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Нельзя купить свой NFT!", show_alert=True)
        return

    user = get_user(buyer_id)
    if user and user["is_buy_banned"]:
        conn.close()
        await callback.answer(f"{pe_plain('ban_emoji')} Вам запрещено покупать!", show_alert=True)
        return

    price = trade["price"]
    stars = get_stars(buyer_id)

    if stars < price:
        conn.close()
        await callback.answer(
            f"{pe_plain('cross')} Недостаточно звёзд! Нужно {price}{pe_plain('star')}, у вас {stars}{pe_plain('star')}",
            show_alert=True
        )
        return

    update_stars(buyer_id, -price)

    seller_amount = int(price * 0.85)
    update_stars(trade["seller_id"], seller_amount)

    c.execute("UPDATE nfts SET owner_id = ? WHERE nft_id = ?", (buyer_id, trade["nft_id"]))
    c.execute(
        "UPDATE inventory SET user_id = ? WHERE nft_id = ? AND user_id = ?",
        (buyer_id, trade["nft_id"], trade["seller_id"])
    )
    c.execute("UPDATE trades SET is_active = 0 WHERE trade_id = ?", (trade_id,))

    conn.commit()
    conn.close()

    new_balance = get_stars(buyer_id)

    await callback.message.edit_text(
        f"{pe('check')} <b>NFT куплен!</b>\n\n"
        f"{trade['gift_emoji']} <b>{trade['gift_name']}</b> | NFT #{trade['nft_id']}\n"
        f"{pe('model')} {trade['model_name']} ({trade['model_chance']}%)\n"
        f"{pe('pattern')} {trade['pattern_name']} ({trade['pattern_chance']}%)\n"
        f"{pe('background')} {trade['bg_name']} ({trade['bg_chance']}%)\n\n"
        f"{pe('money')} Оплачено: <b>{price} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(trade["seller_id"],
        f"{pe('star')} <b>Ваш NFT продан!</b>\n\n"
        f"{trade['gift_emoji']} <b>{trade['gift_name']}</b> | NFT #{trade['nft_id']}\n"
        f"{pe('money')} Получено: <b>{seller_amount} {pe('star')}</b> (комиссия 15%)\n"
        f"{pe('buyer')} Покупатель: <code>{buyer_id}</code>"
    )


# ============================================================
# ВЫСТАВЛЕНИЕ NFT НА ТОРГОВЛЮ — /trade
# ============================================================

@router.message(Command("trade"))
async def cmd_trade(message: Message, command: CommandObject):
    user_id = message.from_user.id

    user = get_user(user_id)
    if user and user["is_trade_banned"]:
        await message.answer(
            f"{pe('ban_emoji')} <b>Вам запрещено торговать!</b>\n"
            f"{pe('rules_emoji')} Причина: {user['trade_ban_reason']}"
        )
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /trade <nft_id> <цена>\n"
            f"Пример: /trade 5 100"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите nft_id и цену!")
        return

    try:
        nft_id = int(parts[0])
        price = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    if price < 1:
        await message.answer(f"{pe('cross')} Цена должна быть минимум 1 {pe('star')}!")
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, user_id))
    nft = c.fetchone()

    if not nft:
        conn.close()
        await message.answer(f"{pe('cross')} NFT не найден или не принадлежит вам!")
        return

    nft = dict(nft)

    c.execute("SELECT trade_id FROM trades WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT уже выставлен на торговлю!")
        return

    c.execute("SELECT rental_id FROM nft_rentals WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT сдан в аренду!")
        return

    c.execute("SELECT auction_id FROM auctions WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT на аукционе!")
        return

    c.execute(
        "INSERT INTO trades (seller_id, nft_id, price) VALUES (?, ?, ?)",
        (user_id, nft_id, price)
    )
    trade_id = c.lastrowid
    conn.commit()
    conn.close()

    seller_gets = int(price * 0.85)

    await message.answer(
        f"{pe('check')} <b>NFT выставлен на торговлю!</b>\n\n"
        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}\n"
        f"{pe('model')} {nft['model_name']} ({nft['model_chance']}%)\n"
        f"{pe('pattern')} {nft['pattern_name']} ({nft['pattern_chance']}%)\n"
        f"{pe('background')} {nft['bg_name']} ({nft['bg_chance']}%)\n\n"
        f"{pe('money')} Цена: <b>{price} {pe('star')}</b>\n"
        f"{pe('money')} Вы получите: <b>{seller_gets} {pe('star')}</b> (−15%)\n"
        f"{pe('pin')} Trade ID: <code>{trade_id}</code>"
    )


# ============================================================
# СНЯТИЕ С ТОРГОВЛИ — /del_trade
# ============================================================

@router.message(Command("del_trade"))
async def cmd_del_trade(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /del_trade <trade_id>")
        return

    try:
        trade_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный trade_id!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM trades WHERE trade_id = ? AND seller_id = ? AND is_active = 1",
        (trade_id, user_id)
    )
    trade = c.fetchone()

    if not trade:
        conn.close()
        await message.answer(f"{pe('cross')} Торговля не найдена или не принадлежит вам!")
        return

    c.execute("UPDATE trades SET is_active = 0 WHERE trade_id = ?", (trade_id,))
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>NFT снят с торговли!</b>\n"
        f"{pe('pin')} Trade ID: <code>{trade_id}</code>"
    )


# ============================================================
# УЛУЧШЕНИЕ ПОДАРКА ДО NFT
# ============================================================

@router.callback_query(F.data.startswith("upgrade_to_nft_"))
async def upgrade_to_nft(callback: CallbackQuery):
    inv_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, user_id))
    item = c.fetchone()

    if not item:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    item = dict(item)

    if item["rarity"] != "rare":
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Только редкие подарки можно улучшить до NFT!", show_alert=True)
        return

    if item["is_nft"]:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Этот подарок уже NFT!", show_alert=True)
        return

    fee = get_nft_create_fee(user_id)
    stars = get_stars(user_id)

    if stars < fee:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Недостаточно звёзд! Нужно {fee}{pe_plain('star')}", show_alert=True)
        return

    model, pattern, bg = generate_nft_characteristics()

    update_stars(user_id, -fee)

    c.execute(
        "INSERT INTO nfts (owner_id, gift_name, gift_emoji, model_name, model_chance, "
        "pattern_name, pattern_chance, bg_name, bg_chance, source_gift_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, item["gift_name"], item["gift_emoji"],
         model["name"], model["chance"],
         pattern["name"], pattern["chance"],
         bg["name"], bg["chance"],
         inv_id)
    )
    nft_id = c.lastrowid

    c.execute(
        "UPDATE inventory SET is_nft = 1, nft_id = ? WHERE inv_id = ?",
        (nft_id, inv_id)
    )

    conn.commit()
    conn.close()

    is_new = grant_achievement(user_id, "first_nft")
    new_balance = get_stars(user_id)

    result_text = (
        f"{pe('nft')} <b>NFT создан!</b> {pe('success')}\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b> | NFT #{nft_id}\n\n"
        f"<b>{pe('leaderboard')} Характеристики:</b>\n"
        f"{pe('model')} Модель: <b>{model['name']}</b> ({model['chance']}%)\n"
        f"{pe('pattern')} Узор: <b>{pattern['name']}</b> ({pattern['chance']}%)\n"
        f"{pe('background')} Фон: <b>{bg['name']}</b> ({bg['chance']}%)\n\n"
        f"{pe('money')} Комиссия: <b>{fee} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    if is_new:
        result_text += f"\n\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый NFT!</b>"

    await callback.message.edit_text(result_text)


# ============================================================
# ПОКАЗАТЬ УЛУЧШАЕМЫЕ ПОДАРКИ
# ============================================================

@router.callback_query(F.data.startswith("show_upgradeable_"))
async def show_upgradeable(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    per_page = 5

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM inventory WHERE user_id = ? AND rarity = 'rare' AND is_nft = 0 "
        "ORDER BY inv_id DESC LIMIT ? OFFSET ?",
        (user_id, per_page, page * per_page)
    )
    items = [dict(row) for row in c.fetchall()]

    c.execute(
        "SELECT COUNT(*) as cnt FROM inventory WHERE user_id = ? AND rarity = 'rare' AND is_nft = 0",
        (user_id,)
    )
    total = c.fetchone()["cnt"]
    conn.close()

    if not items and page == 0:
        await callback.answer(f"{pe_plain('package')} Нет редких подарков для улучшения!", show_alert=True)
        return

    fee = get_nft_create_fee(user_id)
    total_pages = max(1, (total + per_page - 1) // per_page)

    text = (
        f"{pe('upgrade')} <b>Улучшение до NFT</b> (стр. {page + 1}/{total_pages})\n"
        f"{pe('money')} Комиссия: <b>{fee} {pe('star')}</b>\n\n"
    )

    kb = InlineKeyboardBuilder()

    for item in items:
        limited_label = f" {pe('limit')}" if item["is_limited"] else ""
        text += (
            f"{pe('rare')} {item['gift_emoji']} <b>{item['gift_name']}</b>{limited_label}\n"
            f"   {pe('id')} Inv ID: <code>{item['inv_id']}</code>\n\n"
        )
        kb.row(make_inline_button(
            f"Улучшить {item['gift_emoji']} {item['gift_name']}",
            f"upgrade_to_nft_{item['inv_id']}", "upgrade"
        ))

    nav = []
    if page > 0:
        nav.append(make_inline_button("Назад", f"show_upgradeable_{page - 1}", "back"))
    if (page + 1) * per_page < total:
        nav.append(make_inline_button("Далее", f"show_upgradeable_{page + 1}", "next"))
    if nav:
        kb.row(*nav)
    kb.row(make_inline_button("Назад к профилю", "back_profile", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# АУКЦИОНЫ — ПРОСМОТР /auctions
# ============================================================

@router.message(Command("auctions"))
async def cmd_auctions(message: Message):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute("""
        SELECT a.*, n.gift_name, n.gift_emoji, n.model_name, n.model_chance,
               n.pattern_name, n.pattern_chance, n.bg_name, n.bg_chance,
               n.is_crafted, u.first_name
        FROM auctions a
        JOIN nfts n ON a.nft_id = n.nft_id
        JOIN users u ON a.seller_id = u.user_id
        WHERE a.is_active = 1 AND a.ends_at > ?
        ORDER BY a.ends_at ASC
        LIMIT 10
    """, (now,))
    auctions = [dict(row) for row in c.fetchall()]

    if not auctions:
        conn.close()
        await message.answer(
            f"{pe('auction')} <b>Аукционы</b>\n\n"
            f"{pe('package')} Нет активных аукционов.\n\n"
            f"Создать: /add_auc <nft_id> <мин_ставка> <шаг> <дата_окончания>"
        )
        return

    text = f"{pe('auction')} <b>Активные аукционы</b>\n\n"

    kb = InlineKeyboardBuilder()

    for auc in auctions:
        c.execute(
            "SELECT user_id, amount FROM auction_bids WHERE auction_id = ? ORDER BY amount DESC LIMIT 1",
            (auc["auction_id"],)
        )
        top_bid = c.fetchone()

        c.execute(
            "SELECT COUNT(*) as cnt FROM auction_bids WHERE auction_id = ?",
            (auc["auction_id"],)
        )
        bid_count = c.fetchone()["cnt"]

        try:
            ends = datetime.fromisoformat(auc["ends_at"])
            time_left = ends - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            mins = int((time_left.total_seconds() % 3600) // 60)
            time_str = f"{hours}ч {mins}м"
        except Exception:
            time_str = "?"

        top_str = f"{top_bid['amount']} {pe('star')} (ID: {top_bid['user_id']})" if top_bid else "Нет ставок"
        crafted = f" {pe('hammer')}" if auc["is_crafted"] else ""

        text += (
            f"{'─' * 28}\n"
            f"{pe('auction')} <b>Аукцион #{auc['auction_id']}</b>\n"
            f"{auc['gift_emoji']} <b>{auc['gift_name']}</b> | NFT #{auc['nft_id']}{crafted}\n"
            f"{pe('model')} {auc['model_name']} ({auc['model_chance']}%)\n"
            f"{pe('pattern')} {auc['pattern_name']} ({auc['pattern_chance']}%)\n"
            f"{pe('background')} {auc['bg_name']} ({auc['bg_chance']}%)\n"
            f"{pe('money')} Мин. ставка: <b>{auc['min_bid']} {pe('star')}</b>\n"
            f"{pe('bid')} Шаг: <b>{auc['bid_step']} {pe('star')}</b>\n"
            f"{pe('winner')} Топ ставка: <b>{top_str}</b>\n"
            f"{pe('pin')} Ставок: <b>{bid_count}</b>\n"
            f"{pe('clock')} Осталось: <b>{time_str}</b>\n"
            f"{pe('seller')} Продавец: {auc['first_name']}\n\n"
        )

        kb.row(make_inline_button(
            f"Поставить #{auc['auction_id']}",
            f"auc_bid_{auc['auction_id']}", "star"
        ))

    conn.close()
    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# СОЗДАНИЕ АУКЦИОНА — /add_auc
# ============================================================

@router.message(Command("add_auc"))
async def cmd_add_auc(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /add_auc <nft_id> <мин_ставка> <шаг> <дата_окончания>\n"
            f"Пример: /add_auc 5 50 10 2025-01-20 18:00"
        )
        return

    parts = command.args.strip().split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(f"{pe('cross')} Недостаточно параметров!")
        return

    try:
        nft_id = int(parts[0])
        min_bid = int(parts[1])
        bid_step = int(parts[2])
        ends_at_str = parts[3]
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    if bid_step < 10:
        await message.answer(f"{pe('cross')} Минимальный шаг ставки — 10 {pe('star')}!")
        return

    if min_bid < 1:
        await message.answer(f"{pe('cross')} Минимальная ставка — 1 {pe('star')}!")
        return

    try:
        ends_at = datetime.fromisoformat(ends_at_str)
    except Exception:
        try:
            ends_at = datetime.strptime(ends_at_str, "%Y-%m-%d %H:%M")
        except Exception:
            await message.answer(f"{pe('cross')} Некорректный формат даты! Используйте: YYYY-MM-DD HH:MM")
            return

    max_end = datetime.now() + timedelta(hours=48)
    if ends_at > max_end:
        await message.answer(f"{pe('cross')} Максимальное время аукциона — 48 часов!")
        return

    if ends_at <= datetime.now():
        await message.answer(f"{pe('cross')} Дата окончания должна быть в будущем!")
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, user_id))
    nft = c.fetchone()

    if not nft:
        conn.close()
        await message.answer(f"{pe('cross')} NFT не найден или не принадлежит вам!")
        return

    nft = dict(nft)

    c.execute("SELECT trade_id FROM trades WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT уже на торговле!")
        return

    c.execute("SELECT rental_id FROM nft_rentals WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT в аренде!")
        return

    c.execute("SELECT auction_id FROM auctions WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT уже на аукционе!")
        return

    c.execute(
        "INSERT INTO auctions (seller_id, nft_id, min_bid, bid_step, ends_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, nft_id, min_bid, bid_step, ends_at.isoformat())
    )
    auction_id = c.lastrowid
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('auction')} <b>Аукцион создан!</b>\n\n"
        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}\n"
        f"{pe('model')} {nft['model_name']} ({nft['model_chance']}%)\n"
        f"{pe('pattern')} {nft['pattern_name']} ({nft['pattern_chance']}%)\n"
        f"{pe('background')} {nft['bg_name']} ({nft['bg_chance']}%)\n\n"
        f"{pe('money')} Мин. ставка: <b>{min_bid} {pe('star')}</b>\n"
        f"{pe('bid')} Шаг: <b>{bid_step} {pe('star')}</b>\n"
        f"{pe('clock')} До: <b>{ends_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"{pe('auction')} Аукцион ID: <code>{auction_id}</code>"
    )


# ============================================================
# СТАВКА НА АУКЦИОНЕ
# ============================================================

@router.callback_query(F.data.startswith("auc_bid_"))
async def auc_bid_start(callback: CallbackQuery):
    auction_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM auctions WHERE auction_id = ? AND is_active = 1", (auction_id,))
    auc = c.fetchone()

    if not auc:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Аукцион не найден!", show_alert=True)
        return

    auc = dict(auc)

    try:
        ends = datetime.fromisoformat(auc["ends_at"])
        if datetime.now() > ends:
            conn.close()
            await callback.answer(f"{pe_plain('cross')} Аукцион завершён!", show_alert=True)
            return
    except Exception:
        pass

    if auc["seller_id"] == user_id:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Нельзя ставить на свой аукцион!", show_alert=True)
        return

    c.execute(
        "SELECT amount FROM auction_bids WHERE auction_id = ? ORDER BY amount DESC LIMIT 1",
        (auction_id,)
    )
    top = c.fetchone()
    conn.close()

    if top:
        min_new_bid = top["amount"] + auc["bid_step"]
    else:
        min_new_bid = auc["min_bid"]

    stars = get_stars(user_id)

    kb = InlineKeyboardBuilder()
    for mult in [1, 2, 3, 5]:
        bid_amount = min_new_bid + auc["bid_step"] * (mult - 1)
        if bid_amount <= stars:
            kb.row(make_inline_button(
                f"{bid_amount} {pe_plain('star')}",
                f"place_bid_{auction_id}_{bid_amount}", "money"
            ))

    kb.row(make_inline_button(
        "Своя ставка",
        f"custom_bid_{auction_id}_{min_new_bid}", "appeal"
    ))
    kb.row(make_inline_button("Отмена", "cancel_bid", "cross"))

    await callback.message.edit_text(
        f"{pe('auction')} <b>Аукцион #{auction_id}</b>\n\n"
        f"{pe('money')} Минимальная ставка: <b>{min_new_bid} {pe('star')}</b>\n"
        f"{pe('bid')} Шаг: <b>{auc['bid_step']} {pe('star')}</b>\n"
        f"{pe('money')} Ваш баланс: <b>{stars} {pe('star')}</b>\n\n"
        f"Выберите сумму ставки:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "cancel_bid")
async def cancel_bid(callback: CallbackQuery):
    await callback.message.edit_text(f"{pe('cross')} Ставка отменена.")


@router.callback_query(F.data.startswith("place_bid_"))
async def place_bid(callback: CallbackQuery):
    parts = callback.data.split("_")
    auction_id = int(parts[2])
    amount = int(parts[3])
    user_id = callback.from_user.id

    await process_bid(callback, user_id, auction_id, amount)


@router.callback_query(F.data.startswith("custom_bid_"))
async def custom_bid_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    auction_id = int(parts[2])
    min_bid = int(parts[3])

    await state.update_data(auction_id=auction_id, min_bid=min_bid)
    await state.set_state(AuctionStates.waiting_details)

    await callback.message.edit_text(
        f"{pe('auction')} <b>Введите сумму ставки</b> (мин. {min_bid} {pe('star')}):"
    )
    await callback.answer()


@router.message(AuctionStates.waiting_details)
async def custom_bid_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Введите число!")
        return

    auction_id = data["auction_id"]
    min_bid = data["min_bid"]

    if amount < min_bid:
        await message.answer(f"{pe('cross')} Минимальная ставка: {min_bid} {pe('star')}!")
        return

    user_id = message.from_user.id
    stars = get_stars(user_id)

    if amount > stars:
        await message.answer(f"{pe('cross')} Недостаточно звёзд! У вас {stars} {pe('star')}")
        return

    await process_bid_msg(message, user_id, auction_id, amount)


async def process_bid(callback: CallbackQuery, user_id: int, auction_id: int, amount: int):
    stars = get_stars(user_id)
    if amount > stars:
        await callback.answer(
            f"{pe_plain('cross')} Недостаточно звёзд! У вас {stars}{pe_plain('star')}",
            show_alert=True
        )
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM auctions WHERE auction_id = ? AND is_active = 1", (auction_id,))
    auc = c.fetchone()
    if not auc:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Аукцион не найден!", show_alert=True)
        return

    auc = dict(auc)

    try:
        ends = datetime.fromisoformat(auc["ends_at"])
        if datetime.now() > ends:
            conn.close()
            await callback.answer(f"{pe_plain('cross')} Аукцион завершён!", show_alert=True)
            return
    except Exception:
        pass

    c.execute(
        "SELECT user_id, amount FROM auction_bids WHERE auction_id = ? ORDER BY amount DESC LIMIT 1",
        (auction_id,)
    )
    top = c.fetchone()
    if top and amount <= top["amount"]:
        conn.close()
        await callback.answer(
            f"{pe_plain('cross')} Ставка должна быть больше {top['amount']}{pe_plain('star')}!",
            show_alert=True
        )
        return

    if not top and amount < auc["min_bid"]:
        conn.close()
        await callback.answer(
            f"{pe_plain('cross')} Минимальная ставка: {auc['min_bid']}{pe_plain('star')}!",
            show_alert=True
        )
        return

    if top and top["user_id"] != user_id:
        update_stars(top["user_id"], top["amount"])
        await send_notification(top["user_id"],
            f"{pe('auction')} <b>Вашу ставку перебили!</b>\n\n"
            f"{pe('auction')} Аукцион #{auction_id}\n"
            f"{pe('money')} Возвращено: <b>{top['amount']} {pe('star')}</b>\n"
            f"{pe('bid')} Новая топ ставка: <b>{amount} {pe('star')}</b>"
        )

    update_stars(user_id, -amount)

    c.execute(
        "INSERT INTO auction_bids (auction_id, user_id, amount) VALUES (?, ?, ?)",
        (auction_id, user_id, amount)
    )
    conn.commit()
    conn.close()

    new_balance = get_stars(user_id)

    await callback.message.edit_text(
        f"{pe('check')} <b>Ставка принята!</b>\n\n"
        f"{pe('auction')} Аукцион #{auction_id}\n"
        f"{pe('money')} Ваша ставка: <b>{amount} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(auc["seller_id"],
        f"{pe('auction')} <b>Новая ставка на аукционе!</b>\n\n"
        f"{pe('auction')} Аукцион #{auction_id}\n"
        f"{pe('money')} Ставка: <b>{amount} {pe('star')}</b>\n"
        f"{pe('profile')} От: <code>{user_id}</code>"
    )


async def process_bid_msg(message: Message, user_id: int, auction_id: int, amount: int):
    stars = get_stars(user_id)
    if amount > stars:
        await message.answer(f"{pe('cross')} Недостаточно звёзд! У вас {stars} {pe('star')}")
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM auctions WHERE auction_id = ? AND is_active = 1", (auction_id,))
    auc = c.fetchone()
    if not auc:
        conn.close()
        await message.answer(f"{pe('cross')} Аукцион не найден!")
        return

    auc = dict(auc)

    try:
        ends = datetime.fromisoformat(auc["ends_at"])
        if datetime.now() > ends:
            conn.close()
            await message.answer(f"{pe('cross')} Аукцион завершён!")
            return
    except Exception:
        pass

    c.execute(
        "SELECT user_id, amount FROM auction_bids WHERE auction_id = ? ORDER BY amount DESC LIMIT 1",
        (auction_id,)
    )
    top = c.fetchone()

    if top and amount <= top["amount"]:
        conn.close()
        await message.answer(f"{pe('cross')} Ставка должна быть больше {top['amount']} {pe('star')}!")
        return

    if not top and amount < auc["min_bid"]:
        conn.close()
        await message.answer(f"{pe('cross')} Минимальная ставка: {auc['min_bid']} {pe('star')}!")
        return

    if top and top["user_id"] != user_id:
        update_stars(top["user_id"], top["amount"])
        await send_notification(top["user_id"],
            f"{pe('auction')} <b>Вашу ставку перебили!</b>\n"
            f"{pe('auction')} Аукцион #{auction_id}\n"
            f"{pe('money')} Возвращено: <b>{top['amount']} {pe('star')}</b>"
        )

    update_stars(user_id, -amount)

    c.execute(
        "INSERT INTO auction_bids (auction_id, user_id, amount) VALUES (?, ?, ?)",
        (auction_id, user_id, amount)
    )
    conn.commit()
    conn.close()

    new_balance = get_stars(user_id)
    await message.answer(
        f"{pe('check')} <b>Ставка принята!</b>\n\n"
        f"{pe('auction')} Аукцион #{auction_id}\n"
        f"{pe('money')} Ставка: <b>{amount} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(auc["seller_id"],
        f"{pe('auction')} <b>Новая ставка!</b>\n"
        f"{pe('auction')} Аукцион #{auction_id} | {pe('money')} {amount} {pe('star')}"
    )


# ============================================================
# ЗАВЕРШЕНИЕ АУКЦИОНОВ (фоновая задача)
# ============================================================

async def check_auctions():
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute("SELECT * FROM auctions WHERE is_active = 1 AND ends_at <= ?", (now,))
    expired = [dict(row) for row in c.fetchall()]

    for auc in expired:
        c.execute(
            "SELECT user_id, amount FROM auction_bids WHERE auction_id = ? ORDER BY amount DESC LIMIT 1",
            (auc["auction_id"],)
        )
        winner = c.fetchone()

        if winner:
            winner = dict(winner)
            c.execute("UPDATE nfts SET owner_id = ? WHERE nft_id = ?", (winner["user_id"], auc["nft_id"]))
            c.execute(
                "UPDATE inventory SET user_id = ? WHERE nft_id = ? AND user_id = ?",
                (winner["user_id"], auc["nft_id"], auc["seller_id"])
            )

            seller_gets = int(winner["amount"] * 0.85)
            update_stars(auc["seller_id"], seller_gets)

            await send_notification(winner["user_id"],
                f"{pe('winner')} <b>Вы выиграли аукцион #{auc['auction_id']}!</b>\n\n"
                f"{pe('nft')} NFT #{auc['nft_id']} теперь ваш!\n"
                f"{pe('money')} Оплачено: <b>{winner['amount']} {pe('star')}</b>"
            )

            await send_notification(auc["seller_id"],
                f"{pe('auction')} <b>Аукцион #{auc['auction_id']} завершён!</b>\n\n"
                f"{pe('winner')} Победитель: <code>{winner['user_id']}</code>\n"
                f"{pe('money')} Получено: <b>{seller_gets} {pe('star')}</b> (−15%)"
            )
        else:
            await send_notification(auc["seller_id"],
                f"{pe('auction')} <b>Аукцион #{auc['auction_id']} завершён без ставок.</b>\n"
                f"{pe('nft')} NFT #{auc['nft_id']} остаётся у вас."
            )

        c.execute("UPDATE auctions SET is_active = 0 WHERE auction_id = ?", (auc["auction_id"],))

    conn.commit()
    conn.close()


# Конец части 4
# ============================================================
# ============================================================
# ЧАСТЬ 5: Крафт, Аренда NFT, Stardom подписка, Лидерборд
# ============================================================

# ============================================================
# КРАФТ — КНОПКА МЕНЮ
# ============================================================

@router.message(F.text.endswith("Крафт"))
async def show_craft_menu(message: Message):
    user_id = message.from_user.id

    fee = get_nft_create_fee(user_id)
    stars = get_stars(user_id)

    text = (
        f"{pe('craft_btn')} <b>Крафт NFT</b>\n\n"
        f"{pe('hammer')} Объедините до 4 NFT одного типа редкого подарка\n"
        f"для создания уникального скрафченного NFT!\n\n"
        f"<b>{pe('leaderboard')} Шансы успеха:</b>\n"
        f"├ 1 NFT → <b>20%</b>\n"
        f"├ 2 NFT → <b>45%</b>\n"
        f"├ 3 NFT → <b>70%</b>\n"
        f"└ 4 NFT → <b>95%</b>\n\n"
        f"{pe('warning')} Все NFT должны быть из одного типа редкого подарка!\n"
        f"{pe('warning')} Лимитированные подарки нельзя крафтить!\n"
        f"{pe('warning')} При неудаче все NFT теряются!\n\n"
        f"{pe('money')} Комиссия крафта: <b>{fee} {pe('star')}</b>\n"
        f"{pe('money')} Ваш баланс: <b>{stars} {pe('star')}</b>\n\n"
        f"{pe('nft')} Скрафченный NFT получит характеристики 0% 0% 0%\n"
        f"и будет помечен как крафтовый {pe('hammer')}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Начать крафт", "craft_start", "craft_btn"))
    kb.row(make_inline_button("Мои NFT для крафта", "craft_show_nfts_0", "nft"))

    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# КРАФТ — НАЧАЛО
# ============================================================

@router.callback_query(F.data == "craft_start")
async def craft_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT n.*, i.is_limited 
        FROM nfts n
        LEFT JOIN inventory i ON n.nft_id = i.nft_id
        WHERE n.owner_id = ? 
        AND (i.is_limited IS NULL OR i.is_limited = 0)
        AND n.nft_id NOT IN (SELECT nft_id FROM trades WHERE is_active = 1)
        AND n.nft_id NOT IN (SELECT nft_id FROM auctions WHERE is_active = 1)
        AND n.nft_id NOT IN (SELECT nft_id FROM nft_rentals WHERE is_active = 1)
        ORDER BY n.gift_name, n.nft_id
    """, (user_id,))
    nfts = [dict(row) for row in c.fetchall()]
    conn.close()

    if not nfts:
        await callback.answer(f"{pe_plain('cross')} У вас нет доступных NFT для крафта!", show_alert=True)
        return

    groups = {}
    for nft in nfts:
        name = nft["gift_name"]
        if name not in groups:
            groups[name] = []
        groups[name].append(nft)

    available_groups = {k: v for k, v in groups.items() if len(v) >= 1}

    if not available_groups:
        await callback.answer(f"{pe_plain('cross')} Нет NFT для крафта!", show_alert=True)
        return

    await state.set_state(CraftStates.selecting_nfts)
    await state.update_data(selected_nfts=[], craft_gift_name=None)

    text = f"{pe('craft_btn')} <b>Выберите тип подарка для крафта:</b>\n\n"

    kb = InlineKeyboardBuilder()
    for name, nft_list in available_groups.items():
        emoji = nft_list[0]["gift_emoji"]
        kb.row(make_inline_button(
            f"{emoji} {name} ({len(nft_list)} шт.)",
            f"craft_type_{name}", "gift"
        ))

    kb.row(make_inline_button("Отмена", "craft_cancel", "cross"))

    await callback.message.edit_text(text, reply_markup=kb.as_markup())


# ============================================================
# КРАФТ — ВЫБОР ТИПА
# ============================================================

@router.callback_query(F.data.startswith("craft_type_"), CraftStates.selecting_nfts)
async def craft_select_type(callback: CallbackQuery, state: FSMContext):
    gift_name = callback.data[len("craft_type_"):]
    user_id = callback.from_user.id

    await state.update_data(craft_gift_name=gift_name, selected_nfts=[])
    await show_craft_selection(callback, state, user_id, gift_name)


async def show_craft_selection(callback: CallbackQuery, state: FSMContext, user_id: int, gift_name: str):
    data = await state.get_data()
    selected = data.get("selected_nfts", [])

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT n.* FROM nfts n
        LEFT JOIN inventory i ON n.nft_id = i.nft_id
        WHERE n.owner_id = ? AND n.gift_name = ?
        AND (i.is_limited IS NULL OR i.is_limited = 0)
        AND n.nft_id NOT IN (SELECT nft_id FROM trades WHERE is_active = 1)
        AND n.nft_id NOT IN (SELECT nft_id FROM auctions WHERE is_active = 1)
        AND n.nft_id NOT IN (SELECT nft_id FROM nft_rentals WHERE is_active = 1)
        ORDER BY n.nft_id
    """, (user_id, gift_name))
    nfts = [dict(row) for row in c.fetchall()]
    conn.close()

    chance_map = {0: 0, 1: 20, 2: 45, 3: 70, 4: 95}
    current_chance = chance_map.get(len(selected), 0)

    text = (
        f"{pe('craft_btn')} <b>Крафт — {gift_name}</b>\n\n"
        f"{pe('leaderboard')} Выбрано: <b>{len(selected)}/4</b> NFT\n"
        f"{pe('pin')} Шанс успеха: <b>{current_chance}%</b>\n\n"
    )

    if selected:
        text += f"<b>{pe('check')} Выбранные NFT:</b>\n"
        for nft_id in selected:
            nft_info = next((n for n in nfts if n["nft_id"] == nft_id), None)
            if nft_info:
                text += (
                    f"  {pe('nft')} NFT #{nft_id} | {nft_info['model_name']} "
                    f"({nft_info['model_chance']}%)\n"
                )
        text += "\n"

    text += f"<b>{pe('package')} Доступные NFT:</b>\n"

    kb = InlineKeyboardBuilder()

    for nft in nfts:
        if nft["nft_id"] in selected:
            continue
        crafted = f" {pe('hammer')}" if nft["is_crafted"] else ""
        text += (
            f"  {pe('nft')} #{nft['nft_id']}{crafted} | "
            f"{pe('model')}{nft['model_name']}({nft['model_chance']}%) "
            f"{pe('pattern')}{nft['pattern_name']}({nft['pattern_chance']}%) "
            f"{pe('background')}{nft['bg_name']}({nft['bg_chance']}%)\n"
        )

        if len(selected) < 4:
            kb.row(make_inline_button(
                f"Добавить NFT #{nft['nft_id']}",
                f"craft_add_{nft['nft_id']}", "ok"
            ))

    for nft_id in selected:
        kb.row(make_inline_button(
            f"Убрать NFT #{nft_id}",
            f"craft_remove_{nft_id}", "cross"
        ))

    if len(selected) >= 1:
        kb.row(make_inline_button(
            f"КРАФТИТЬ ({current_chance}% шанс)",
            "craft_execute", "hammer"
        ))

    kb.row(make_inline_button("Отмена", "craft_cancel", "cross"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# КРАФТ — ДОБАВЛЕНИЕ NFT
# ============================================================

@router.callback_query(F.data.startswith("craft_add_"), CraftStates.selecting_nfts)
async def craft_add_nft(callback: CallbackQuery, state: FSMContext):
    nft_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected = data.get("selected_nfts", [])
    gift_name = data.get("craft_gift_name")

    if len(selected) >= 4:
        await callback.answer(f"{pe_plain('cross')} Максимум 4 NFT!", show_alert=True)
        return

    if nft_id in selected:
        await callback.answer(f"{pe_plain('cross')} Уже добавлен!", show_alert=True)
        return

    selected.append(nft_id)
    await state.update_data(selected_nfts=selected)
    await show_craft_selection(callback, state, callback.from_user.id, gift_name)


# ============================================================
# КРАФТ — УДАЛЕНИЕ NFT
# ============================================================

@router.callback_query(F.data.startswith("craft_remove_"), CraftStates.selecting_nfts)
async def craft_remove_nft(callback: CallbackQuery, state: FSMContext):
    nft_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected = data.get("selected_nfts", [])
    gift_name = data.get("craft_gift_name")

    if nft_id in selected:
        selected.remove(nft_id)
    await state.update_data(selected_nfts=selected)
    await show_craft_selection(callback, state, callback.from_user.id, gift_name)


# ============================================================
# КРАФТ — ВЫПОЛНЕНИЕ
# ============================================================

@router.callback_query(F.data == "craft_execute", CraftStates.selecting_nfts)
async def craft_execute(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    selected = data.get("selected_nfts", [])
    gift_name = data.get("craft_gift_name")
    await state.clear()

    if not selected:
        await callback.answer(f"{pe_plain('cross')} Не выбраны NFT!", show_alert=True)
        return

    fee = get_nft_create_fee(user_id)
    stars = get_stars(user_id)

    if stars < fee:
        await callback.answer(f"{pe_plain('cross')} Недостаточно звёзд! Нужно {fee}{pe_plain('star')}", show_alert=True)
        return

    conn = get_db()
    c = conn.cursor()

    valid_nfts = []
    for nft_id in selected:
        c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, user_id))
        nft = c.fetchone()
        if not nft:
            conn.close()
            await callback.message.edit_text(f"{pe('cross')} Один из NFT не найден или не принадлежит вам!")
            return
        nft = dict(nft)
        if nft["gift_name"] != gift_name:
            conn.close()
            await callback.message.edit_text(f"{pe('cross')} Все NFT должны быть одного типа!")
            return

        c.execute("SELECT is_limited FROM inventory WHERE nft_id = ?", (nft_id,))
        inv = c.fetchone()
        if inv and inv["is_limited"]:
            conn.close()
            await callback.message.edit_text(f"{pe('cross')} Лимитированные подарки нельзя крафтить!")
            return

        valid_nfts.append(nft)

    chance_map = {1: 20, 2: 45, 3: 70, 4: 95}
    chance = chance_map.get(len(selected), 20)

    update_stars(user_id, -fee)

    roll = random.randint(1, 100)
    success = roll <= chance

    if success:
        for nft_id in selected:
            c.execute("DELETE FROM nfts WHERE nft_id = ?", (nft_id,))
            c.execute("DELETE FROM inventory WHERE nft_id = ?", (nft_id,))

        gift_emoji = valid_nfts[0]["gift_emoji"]
        c.execute(
            "INSERT INTO nfts (owner_id, gift_name, gift_emoji, model_name, model_chance, "
            "pattern_name, pattern_chance, bg_name, bg_chance, is_crafted) "
            "VALUES (?, ?, ?, 'Crafted', 0, 'Crafted', 0, 'Crafted', 0, 1)",
            (user_id, gift_name, gift_emoji)
        )
        new_nft_id = c.lastrowid

        counter = get_next_counter("gift_purchase_counter")
        c.execute(
            "INSERT INTO inventory (inv_id, user_id, gift_name, gift_emoji, rarity, is_nft, nft_id) "
            "VALUES (?, ?, ?, ?, 'rare', 1, ?)",
            (counter, user_id, gift_name, gift_emoji, new_nft_id)
        )

        conn.commit()
        conn.close()

        is_new = grant_achievement(user_id, "first_craft")
        new_balance = get_stars(user_id)

        result_text = (
            f"{pe('success')} <b>КРАФТ УСПЕШЕН!</b> {pe('success')}\n\n"
            f"{pe('hammer')} {gift_emoji} <b>{gift_name}</b> | NFT #{new_nft_id}\n\n"
            f"<b>{pe('leaderboard')} Характеристики:</b>\n"
            f"{pe('model')} Модель: <b>Crafted</b> (0%)\n"
            f"{pe('pattern')} Узор: <b>Crafted</b> (0%)\n"
            f"{pe('background')} Фон: <b>Crafted</b> (0%)\n\n"
            f"{pe('hammer')} Помечен как скрафченный\n"
            f"{pe('id')} Inv ID: <code>{counter}</code>\n"
            f"{pe('money')} Комиссия: {fee} {pe('star')}\n"
            f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>\n\n"
            f"{pe('leaderboard')} Шанс был: {chance}% | Выпало: {roll}"
        )

        if is_new:
            result_text += f"\n\n{pe('achieve')} {pe('medal')} <b>Достижение: Первый крафт!</b>"

    else:
        for nft_id in selected:
            c.execute("DELETE FROM nfts WHERE nft_id = ?", (nft_id,))
            c.execute("DELETE FROM inventory WHERE nft_id = ?", (nft_id,))

        conn.commit()
        conn.close()

        new_balance = get_stars(user_id)

        result_text = (
            f"{pe('fail')} <b>КРАФТ ПРОВАЛЕН!</b> {pe('fail')}\n\n"
            f"{pe('cross')} Все {len(selected)} NFT потеряны!\n"
            f"{pe('money')} Комиссия: {fee} {pe('star')}\n"
            f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>\n\n"
            f"{pe('leaderboard')} Шанс был: {chance}% | Выпало: {roll}\n\n"
            f"Не повезло... Попробуйте снова!"
        )

    await callback.message.edit_text(result_text)


# ============================================================
# КРАФТ — ОТМЕНА
# ============================================================

@router.callback_query(F.data == "craft_cancel")
async def craft_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f"{pe('cross')} Крафт отменён.")


# ============================================================
# КРАФТ — ПОКАЗАТЬ NFT
# ============================================================

@router.callback_query(F.data.startswith("craft_show_nfts_"))
async def craft_show_nfts(callback: CallbackQuery):
    page = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    per_page = 5

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT n.*, i.is_limited FROM nfts n
        LEFT JOIN inventory i ON n.nft_id = i.nft_id
        WHERE n.owner_id = ?
        AND (i.is_limited IS NULL OR i.is_limited = 0)
        ORDER BY n.gift_name, n.nft_id
        LIMIT ? OFFSET ?
    """, (user_id, per_page, page * per_page))
    nfts = [dict(row) for row in c.fetchall()]

    c.execute("""
        SELECT COUNT(*) as cnt FROM nfts n
        LEFT JOIN inventory i ON n.nft_id = i.nft_id
        WHERE n.owner_id = ?
        AND (i.is_limited IS NULL OR i.is_limited = 0)
    """, (user_id,))
    total = c.fetchone()["cnt"]
    conn.close()

    if not nfts:
        await callback.answer(f"{pe_plain('package')} Нет NFT для крафта!", show_alert=True)
        return

    total_pages = max(1, (total + per_page - 1) // per_page)
    text = f"{pe('craft_btn')} <b>NFT для крафта</b> (стр. {page + 1}/{total_pages}):\n\n"

    for nft in nfts:
        crafted = f" {pe('hammer')}" if nft["is_crafted"] else ""
        text += (
            f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | #{nft['nft_id']}{crafted}\n"
            f"  {pe('model')}{nft['model_name']}({nft['model_chance']}%) "
            f"{pe('pattern')}{nft['pattern_name']}({nft['pattern_chance']}%) "
            f"{pe('background')}{nft['bg_name']}({nft['bg_chance']}%)\n\n"
        )

    kb = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(make_inline_button("Назад", f"craft_show_nfts_{page - 1}", "back"))
    if (page + 1) * per_page < total:
        nav.append(make_inline_button("Далее", f"craft_show_nfts_{page + 1}", "next"))
    if nav:
        kb.row(*nav)

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# ============================================================
# АРЕНДА NFT — КОМАНДА
# ============================================================

@router.message(Command("nft_rental"))
async def cmd_nft_rental(message: Message):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute("""
        SELECT r.*, n.gift_name, n.gift_emoji, n.model_name, n.model_chance,
               n.pattern_name, n.pattern_chance, n.bg_name, n.bg_chance,
               n.is_crafted, u.first_name
        FROM nft_rentals r
        JOIN nfts n ON r.nft_id = n.nft_id
        JOIN users u ON r.owner_id = u.user_id
        WHERE r.is_active = 1 AND r.is_rented = 0 AND r.ends_at > ?
        ORDER BY r.created_at DESC
        LIMIT 10
    """, (now,))
    rentals = [dict(row) for row in c.fetchall()]
    conn.close()

    text = (
        f"{pe('rent')} <b>Аренда NFT</b> {pe('house')}\n\n"
        f"{pe('rules_emoji')} Команды:\n"
        f"├ /nft_rents &lt;nft_id&gt; &lt;цена/час&gt; &lt;время_окончания&gt;\n"
        f"├ /rent_nft &lt;rental_id&gt;\n"
        f"└ /nft_rental — Этот список\n\n"
        f"{pe('clock')} Доступные периоды: 1ч, 12ч, 24ч, 48ч\n"
        f"{pe('warning')} Лимитированные NFT нельзя сдавать в аренду!\n\n"
    )

    if not rentals:
        text += f"{pe('package')} Нет доступных аренд."
        await message.answer(text)
        return

    text += f"<b>{pe('house')} Доступные аренды:</b>\n\n"

    kb = InlineKeyboardBuilder()

    for r in rentals:
        try:
            ends = datetime.fromisoformat(r["ends_at"])
            time_left = ends - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            time_str = f"{hours}ч"
        except Exception:
            time_str = "?"

        crafted = f" {pe('hammer')}" if r["is_crafted"] else ""

        text += (
            f"{'─' * 25}\n"
            f"{pe('house')} <b>Аренда #{r['rental_id']}</b>\n"
            f"{r['gift_emoji']} <b>{r['gift_name']}</b> | NFT #{r['nft_id']}{crafted}\n"
            f"{pe('model')} {r['model_name']} ({r['model_chance']}%)\n"
            f"{pe('pattern')} {r['pattern_name']} ({r['pattern_chance']}%)\n"
            f"{pe('background')} {r['bg_name']} ({r['bg_chance']}%)\n"
            f"{pe('money')} Цена: <b>{r['price_per_hour']} {pe('star')}/час</b>\n"
            f"{pe('clock')} Доступно ещё: <b>{time_str}</b>\n"
            f"{pe('seller')} Владелец: {r['first_name']}\n\n"
        )

        kb.row(make_inline_button(
            f"Арендовать #{r['rental_id']}",
            f"rent_choose_{r['rental_id']}", "rent"
        ))

    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# СДАТЬ NFT В АРЕНДУ — /nft_rents
# ============================================================

@router.message(Command("nft_rents"))
async def cmd_nft_rents(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /nft_rents <nft_id> <цена_за_час> <время_окончания>\n"
            f"Пример: /nft_rents 5 10 2025-01-20 18:00"
        )
        return

    parts = command.args.strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(f"{pe('cross')} Недостаточно параметров!")
        return

    try:
        nft_id = int(parts[0])
        price_per_hour = int(parts[1])
        ends_str = parts[2]
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    if price_per_hour < 1:
        await message.answer(f"{pe('cross')} Цена должна быть минимум 1 {pe('star')}/час!")
        return

    try:
        ends_at = datetime.fromisoformat(ends_str)
    except Exception:
        try:
            ends_at = datetime.strptime(ends_str, "%Y-%m-%d %H:%M")
        except Exception:
            await message.answer(f"{pe('cross')} Некорректный формат даты!")
            return

    max_end = datetime.now() + timedelta(hours=48)
    if ends_at > max_end:
        await message.answer(f"{pe('cross')} Максимальное время аренды — 48 часов!")
        return

    if ends_at <= datetime.now():
        await message.answer(f"{pe('cross')} Время должно быть в будущем!")
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, user_id))
    nft = c.fetchone()
    if not nft:
        conn.close()
        await message.answer(f"{pe('cross')} NFT не найден или не принадлежит вам!")
        return
    nft = dict(nft)

    c.execute("SELECT is_limited FROM inventory WHERE nft_id = ?", (nft_id,))
    inv = c.fetchone()
    if inv and inv["is_limited"]:
        conn.close()
        await message.answer(f"{pe('cross')} Лимитированные NFT нельзя сдавать в аренду!")
        return

    c.execute("SELECT rental_id FROM nft_rentals WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT уже сдан в аренду!")
        return

    c.execute("SELECT trade_id FROM trades WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT на торговле!")
        return

    c.execute("SELECT auction_id FROM auctions WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} Этот NFT на аукционе!")
        return

    c.execute(
        "INSERT INTO nft_rentals (owner_id, nft_id, price_per_hour, ends_at) VALUES (?, ?, ?, ?)",
        (user_id, nft_id, price_per_hour, ends_at.isoformat())
    )
    rental_id = c.lastrowid
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('rent')} <b>NFT выставлен на аренду!</b>\n\n"
        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}\n"
        f"{pe('money')} Цена: <b>{price_per_hour} {pe('star')}/час</b>\n"
        f"{pe('clock')} До: <b>{ends_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"{pe('house')} Rental ID: <code>{rental_id}</code>"
    )


# ============================================================
# АРЕНДОВАТЬ — ВЫБОР ПЕРИОДА
# ============================================================

@router.callback_query(F.data.startswith("rent_choose_"))
async def rent_choose_duration(callback: CallbackQuery):
    rental_id = int(callback.data.split("_")[2])

    kb = InlineKeyboardBuilder()
    for hours in [1, 12, 24, 48]:
        label = f"{hours} час" if hours == 1 else f"{hours} часов"
        kb.row(make_inline_button(label, f"rent_confirm_{rental_id}_{hours}", "clock"))
    kb.row(make_inline_button("Отмена", "rent_cancel", "cross"))

    await callback.message.edit_text(
        f"{pe('rent')} <b>Выберите период аренды:</b>",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "rent_cancel")
async def rent_cancel(callback: CallbackQuery):
    await callback.message.edit_text(f"{pe('cross')} Аренда отменена.")


# ============================================================
# АРЕНДОВАТЬ — ПОДТВЕРЖДЕНИЕ
# ============================================================

@router.callback_query(F.data.startswith("rent_confirm_"))
async def rent_confirm(callback: CallbackQuery):
    parts = callback.data.split("_")
    rental_id = int(parts[2])
    hours = int(parts[3])
    user_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM nft_rentals WHERE rental_id = ? AND is_active = 1 AND is_rented = 0", (rental_id,))
    rental = c.fetchone()

    if not rental:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Аренда не найдена!", show_alert=True)
        return

    rental = dict(rental)

    if rental["owner_id"] == user_id:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Нельзя арендовать свой NFT!", show_alert=True)
        return

    total_cost = rental["price_per_hour"] * hours
    stars = get_stars(user_id)

    if stars < total_cost:
        conn.close()
        await callback.answer(
            f"{pe_plain('cross')} Недостаточно звёзд! Нужно {total_cost}{pe_plain('star')}",
            show_alert=True
        )
        return

    update_stars(user_id, -total_cost)
    update_stars(rental["owner_id"], total_cost)

    rent_ends = datetime.now() + timedelta(hours=hours)
    c.execute(
        "UPDATE nft_rentals SET is_rented = 1, renter_id = ?, rent_started = ?, rent_ends = ? "
        "WHERE rental_id = ?",
        (user_id, datetime.now().isoformat(), rent_ends.isoformat(), rental_id)
    )
    conn.commit()
    conn.close()

    new_balance = get_stars(user_id)
    hours_label = f"{hours} час" if hours == 1 else f"{hours} часов"

    await callback.message.edit_text(
        f"{pe('check')} <b>NFT арендован!</b>\n\n"
        f"{pe('house')} Аренда #{rental_id}\n"
        f"{pe('clock')} На: <b>{hours_label}</b>\n"
        f"{pe('clock')} До: <b>{rent_ends.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"{pe('money')} Оплачено: <b>{total_cost} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(rental["owner_id"],
        f"{pe('rent')} <b>Ваш NFT арендован!</b>\n\n"
        f"{pe('house')} Аренда #{rental_id}\n"
        f"{pe('profile')} Арендатор: <code>{user_id}</code>\n"
        f"{pe('clock')} На: {hours_label}\n"
        f"{pe('money')} Получено: <b>{total_cost} {pe('star')}</b>"
    )


# ============================================================
# /rent_nft КОМАНДА
# ============================================================

@router.message(Command("rent_nft"))
async def cmd_rent_nft(message: Message, command: CommandObject):
    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /rent_nft <rental_id>")
        return

    try:
        rental_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный ID!")
        return

    kb = InlineKeyboardBuilder()
    for hours in [1, 12, 24, 48]:
        label = f"{hours} час" if hours == 1 else f"{hours} часов"
        kb.row(make_inline_button(label, f"rent_confirm_{rental_id}_{hours}", "clock"))
    kb.row(make_inline_button("Отмена", "rent_cancel", "cross"))

    await message.answer(
        f"{pe('rent')} <b>Аренда #{rental_id}</b>\n\nВыберите период:",
        reply_markup=kb.as_markup()
    )


# ============================================================
# ПРОВЕРКА АРЕНД (фоновая задача)
# ============================================================

async def check_rentals():
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute(
        "SELECT * FROM nft_rentals WHERE is_rented = 1 AND rent_ends <= ? AND is_active = 1",
        (now,)
    )
    expired = [dict(row) for row in c.fetchall()]

    for rental in expired:
        c.execute("UPDATE nft_rentals SET is_active = 0 WHERE rental_id = ?", (rental["rental_id"],))

        await send_notification(rental["renter_id"],
            f"{pe('rent')} <b>Аренда завершена!</b>\n\n"
            f"{pe('house')} Аренда #{rental['rental_id']} истекла."
        )
        await send_notification(rental["owner_id"],
            f"{pe('rent')} <b>Аренда вашего NFT завершена!</b>\n\n"
            f"{pe('house')} Аренда #{rental['rental_id']}\n"
            f"{pe('nft')} NFT #{rental['nft_id']} снова доступен."
        )

    c.execute(
        "SELECT * FROM nft_rentals WHERE is_rented = 0 AND ends_at <= ? AND is_active = 1",
        (now,)
    )
    expired_listings = [dict(row) for row in c.fetchall()]
    for listing in expired_listings:
        c.execute("UPDATE nft_rentals SET is_active = 0 WHERE rental_id = ?", (listing["rental_id"],))

    conn.commit()
    conn.close()


# ============================================================
# STARDOM — КНОПКА МЕНЮ
# ============================================================

@router.message(F.text.endswith("Stardom"))
async def show_stardom_menu(message: Message):
    user_id = message.from_user.id
    current_level = get_user_stardom(user_id)
    user = get_user(user_id)

    text = f"{pe('stardom')} <b>Stardom — Система подписок</b> {pe('sparkles')}\n\n"

    if current_level > 0:
        sd = STARDOM_LEVELS[current_level]
        text += (
            f"{pe('check')} Ваш текущий уровень: <b>{sd['name']}</b>\n"
            f"{pe('date')} Действует до: <b>{user.get('stardom_expires', '?')[:10]}</b>\n\n"
        )
    else:
        text += f"{pe('cross')} У вас нет Stardom подписки.\n\n"

    text += f"{pe('money')} Баланс: <b>{user['stars']} {pe('star')}</b>\n\n"

    kb = InlineKeyboardBuilder()

    for level, sd in STARDOM_LEVELS.items():
        is_current = level == current_level
        status = f" {pe('check')} ТЕКУЩИЙ" if is_current else ""

        spark_key = f"spark{level}"
        spark = pe(spark_key)

        text += (
            f"{'─' * 28}\n"
            f"{spark * level} <b>{sd['name']}</b>{status}\n"
            f"{pe('money')} Цена: <b>{sd['price']} {pe('star')}</b> на {sd['duration_months']} мес.\n"
            f"├ Комиссия NFT: <b>{sd['nft_create_fee']} {pe('star')}</b>\n"
            f"├ Передача NFT: <b>{sd['nft_transfer_fee']} {pe('star')}</b>\n"
            f"├ Передача подарка: <b>{sd['gift_transfer_fee']} {pe('star')}</b>\n"
            f"└ Подарок: {sd['exclusive_emoji']} <b>{sd['exclusive_gift']}</b>\n\n"
        )

        if not is_current:
            kb.row(make_inline_button(
                f"{sd['name']} — {sd['price']}{pe_plain('star')}",
                f"buy_stardom_{level}", "stardom"
            ))

    await message.answer(text, reply_markup=kb.as_markup())


# ============================================================
# ПОКУПКА STARDOM
# ============================================================

@router.callback_query(F.data.startswith("buy_stardom_"))
async def buy_stardom(callback: CallbackQuery):
    level = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    if level not in STARDOM_LEVELS:
        await callback.answer(f"{pe_plain('cross')} Неизвестный уровень!", show_alert=True)
        return

    sd = STARDOM_LEVELS[level]
    stars = get_stars(user_id)

    if stars >= sd["price"]:
        update_stars(user_id, -sd["price"])
        await activate_stardom(user_id, level)

        kb = InlineKeyboardBuilder()
        kb.row(make_inline_button("К Stardom", "back_stardom", "back"))

        await callback.message.edit_text(
            f"{pe('check')} <b>Stardom {sd['name']} активирован!</b>\n\n"
            f"{pe('money')} Списано: <b>{sd['price']} {pe('star')}</b>",
            reply_markup=kb.as_markup()
        )
    else:
        try:
            await bot.send_invoice(
                chat_id=user_id,
                title=f"Stardom {sd['name']}",
                description=f"Подписка {sd['name']} на {sd['duration_months']} месяцев",
                payload=f"stardom_{level}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=sd["name"], amount=sd["price"])]
            )
            await callback.answer(f"{pe_plain('topup')} Счёт отправлен!", show_alert=True)
        except Exception as e:
            await callback.answer(f"{pe_plain('cross')} Ошибка: {e}", show_alert=True)


@router.callback_query(F.data == "back_stardom")
async def back_stardom(callback: CallbackQuery):
    await callback.message.delete()
    user_id = callback.from_user.id
    current_level = get_user_stardom(user_id)
    user = get_user(user_id)

    text = f"{pe('stardom')} <b>Stardom</b> {pe('sparkles')}\n\n"
    if current_level > 0:
        sd = STARDOM_LEVELS[current_level]
        text += f"{pe('check')} Текущий: <b>{sd['name']}</b>\n"

    text += f"{pe('money')} Баланс: <b>{user['stars']} {pe('star')}</b>"

    await bot.send_message(user_id, text, reply_markup=get_main_keyboard())


# ============================================================
# ЛИДЕРБОРД / ТОП
# ============================================================

@router.message(F.text.endswith("Топ"))
async def show_leaderboard(message: Message):
    text = (
        f"{pe('trophy')} <b>Лидерборд</b>\n\n"
        f"Выберите категорию:"
    )

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Топ по балансу", "top_balance", "money"))
    kb.row(make_inline_button("Топ по кол-ву NFT", "top_nfts", "nft"))
    kb.row(make_inline_button("Топ по редкости коллекции", "top_rarity", "gem"))

    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "top_balance")
async def top_balance(callback: CallbackQuery):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, username, stars FROM users ORDER BY stars DESC LIMIT 10")
    users = [dict(row) for row in c.fetchall()]
    conn.close()

    text = f"{pe('trophy')} <b>Топ 10 по балансу</b> {pe('money')}\n\n"
    medals = [pe('winner'), pe('medal'), pe('medal')]

    for i, u in enumerate(users):
        medal = medals[i] if i < 3 else f"{i + 1}."
        name = u["first_name"] or "?"
        uname = f" (@{u['username']})" if u["username"] else ""
        text += f"{medal} <b>{name}</b>{uname} — <b>{u['stars']} {pe('star')}</b>\n"

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Назад", "back_top", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


@router.callback_query(F.data == "top_nfts")
async def top_nfts(callback: CallbackQuery):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT n.owner_id, u.first_name, u.username, COUNT(*) as nft_count
        FROM nfts n
        JOIN users u ON n.owner_id = u.user_id
        GROUP BY n.owner_id
        ORDER BY nft_count DESC
        LIMIT 10
    """)
    users = [dict(row) for row in c.fetchall()]
    conn.close()

    text = f"{pe('trophy')} <b>Топ 10 по количеству NFT</b> {pe('nft')}\n\n"
    medals = [pe('winner'), pe('medal'), pe('medal')]

    if not users:
        text += f"{pe('package')} Ни у кого нет NFT."
    else:
        for i, u in enumerate(users):
            medal = medals[i] if i < 3 else f"{i + 1}."
            name = u["first_name"] or "?"
            text += f"{medal} <b>{name}</b> — <b>{u['nft_count']} NFT</b>\n"

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Назад", "back_top", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


@router.callback_query(F.data == "top_rarity")
async def top_rarity(callback: CallbackQuery):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT n.owner_id, u.first_name, u.username,
               MIN(n.model_chance + n.pattern_chance + n.bg_chance) as min_rarity,
               COUNT(*) as nft_count
        FROM nfts n
        JOIN users u ON n.owner_id = u.user_id
        GROUP BY n.owner_id
        ORDER BY min_rarity ASC, nft_count DESC
        LIMIT 10
    """)
    users = [dict(row) for row in c.fetchall()]
    conn.close()

    text = f"{pe('trophy')} <b>Топ 10 по редкости коллекции</b> {pe('gem')}\n\n"
    medals = [pe('winner'), pe('medal'), pe('medal')]

    if not users:
        text += f"{pe('package')} Ни у кого нет NFT."
    else:
        for i, u in enumerate(users):
            medal = medals[i] if i < 3 else f"{i + 1}."
            name = u["first_name"] or "?"
            rarity = u["min_rarity"]
            text += f"{medal} <b>{name}</b> — мин. редкость: <b>{rarity}%</b> ({u['nft_count']} NFT)\n"

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Назад", "back_top", "back"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


@router.callback_query(F.data == "back_top")
async def back_top(callback: CallbackQuery):
    text = (
        f"{pe('trophy')} <b>Лидерборд</b>\n\n"
        f"Выберите категорию:"
    )

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button("Топ по балансу", "top_balance", "money"))
    kb.row(make_inline_button("Топ по кол-ву NFT", "top_nfts", "nft"))
    kb.row(make_inline_button("Топ по редкости коллекции", "top_rarity", "gem"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())
    except Exception:
        await callback.answer()


# Конец части 5
# ============================================================
# ============================================================
# ЧАСТЬ 6: Админ-команды, Модераторы, Баны, Правила, Аппеляции
# ============================================================

# ============================================================
# /add_gift — Добавить подарок в магазин
# ============================================================

@router.message(Command("add_gift"))
async def cmd_add_gift(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /add_gift <название> <эмодзи> <кол-во> <цена> <редкость>\n"
            f"Пример: /add_gift Роза 🌹 0 50 common\n"
            f"Пример: /add_gift Дракон 🐉 100 200 rare\n"
            f"• Кол-во 0 = неограничено\n"
            f"• Редкость: common или rare"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 5:
        await message.answer(f"{pe('cross')} Недостаточно параметров! Нужно: название эмодзи кол-во цена редкость")
        return

    name = parts[0]
    emoji = parts[1]
    try:
        quantity = int(parts[2])
        price = int(parts[3])
    except ValueError:
        await message.answer(f"{pe('cross')} Кол-во и цена должны быть числами!")
        return

    rarity = parts[4].lower()
    if rarity not in ("common", "rare"):
        await message.answer(f"{pe('cross')} Редкость должна быть 'common' или 'rare'!")
        return

    if price < 1:
        await message.answer(f"{pe('cross')} Цена должна быть минимум 1 {pe('star')}!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO gifts (name, emoji, quantity, price, rarity) VALUES (?, ?, ?, ?, ?)",
        (name, emoji, quantity, price, rarity)
    )
    gift_id = c.lastrowid
    conn.commit()
    conn.close()

    qty_text = "∞" if quantity == 0 else str(quantity)
    market = "Маркет #1" if rarity == "common" else "Маркет #2"
    rarity_e = pe('common') if rarity == "common" else pe('rare')

    await message.answer(
        f"{pe('check')} <b>Подарок добавлен!</b>\n\n"
        f"{rarity_e} {emoji} <b>{name}</b>\n"
        f"{pe('money')} Цена: <b>{price} {pe('star')}</b>\n"
        f"{pe('package')} Кол-во: <b>{qty_text}</b>\n"
        f"{pe('leaderboard')} Редкость: <b>{rarity}</b>\n"
        f"{pe('market')} Появится в: <b>{market}</b>\n"
        f"{pe('id')} Gift ID: <code>{gift_id}</code>"
    )


# ============================================================
# /del_gift — Удалить подарок из магазина
# ============================================================

@router.message(Command("del_gift"))
async def cmd_del_gift(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /del_gift <gift_id>")
        return

    try:
        gift_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный ID!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM gifts WHERE gift_id = ?", (gift_id,))
    gift = c.fetchone()

    if not gift:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок не найден!")
        return

    gift = dict(gift)
    c.execute("UPDATE gifts SET is_active = 0 WHERE gift_id = ?", (gift_id,))
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Подарок удалён из магазина!</b>\n\n"
        f"{gift['emoji']} <b>{gift['name']}</b> ({pe('id')} {gift_id})"
    )


# ============================================================
# /add_limit — Добавить лимитированный подарок
# ============================================================

@router.message(Command("add_limit"))
async def cmd_add_limit(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /add_limit <название> <эмодзи> <цена> <дата_истечения>\n"
            f"Пример: /add_limit НГПодарок 🎄 100 2025-01-31 23:59"
        )
        return

    parts = command.args.strip().split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(f"{pe('cross')} Недостаточно параметров!")
        return

    name = parts[0]
    emoji = parts[1]
    try:
        price = int(parts[2])
    except ValueError:
        await message.answer(f"{pe('cross')} Цена должна быть числом!")
        return

    expires_str = parts[3]
    try:
        expires_at = datetime.fromisoformat(expires_str)
    except Exception:
        try:
            expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M")
        except Exception:
            await message.answer(f"{pe('cross')} Некорректный формат даты! YYYY-MM-DD HH:MM")
            return

    if expires_at <= datetime.now():
        await message.answer(f"{pe('cross')} Дата должна быть в будущем!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO limited_gifts (name, emoji, price, expires_at) VALUES (?, ?, ?, ?)",
        (name, emoji, price, expires_at.isoformat())
    )
    limit_id = c.lastrowid
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Лимитированный подарок добавлен!</b>\n\n"
        f"{pe('limit')} {emoji} <b>{name}</b>\n"
        f"{pe('money')} Цена: <b>{price} {pe('star')}</b>\n"
        f"{pe('date')} Истекает: <b>{expires_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"{pe('id')} Limit ID: <code>{limit_id}</code>\n\n"
        f"Появится в <b>{pe('market2')} Маркет #2</b>"
    )


# ============================================================
# /give_stars / /remove_stars
# ============================================================

@router.message(Command("give_stars"))
async def cmd_give_stars(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /give_stars <user_id> <кол-во>")
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и количество!")
        return

    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден!")
        return

    update_stars(target_id, amount)
    new_balance = get_stars(target_id)

    await message.answer(
        f"{pe('check')} <b>Звёзды выданы!</b>\n\n"
        f"{pe('profile')} {target['first_name']} (<code>{target_id}</code>)\n"
        f"{pe('money')} +{amount} {pe('star')}\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(target_id,
        f"{pe('star')} <b>Вам начислены звёзды!</b>\n\n"
        f"{pe('money')} +{amount} {pe('star')}\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>\n"
        f"{pe('moder')} От: Администрация"
    )


@router.message(Command("remove_stars"))
async def cmd_remove_stars(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /remove_stars <user_id> <кол-во>")
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и количество!")
        return

    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден!")
        return

    update_stars(target_id, -amount)
    new_balance = get_stars(target_id)

    await message.answer(
        f"{pe('check')} <b>Звёзды списаны!</b>\n\n"
        f"{pe('profile')} {target['first_name']} (<code>{target_id}</code>)\n"
        f"{pe('money')} -{amount} {pe('star')}\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )


# ============================================================
# /give_gift — Подарить подарок пользователю
# ============================================================

@router.message(Command("give_gift"))
async def cmd_give_gift(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /give_gift <название> <user_id>")
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите название и user_id!")
        return

    name = parts[0]
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден!")
        return

    counter = get_next_counter("gift_purchase_counter")
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, gift_name, gift_emoji, rarity) VALUES (?, ?, ?, '🎁', 'common')",
        (counter, target_id, name)
    )
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Подарок выдан!</b>\n\n"
        f"{pe('gift')} <b>{name}</b> → {target['first_name']} (<code>{target_id}</code>)\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>"
    )

    await send_notification(target_id,
        f"{pe('gift')} <b>Вам выдан подарок от администрации!</b>\n\n"
        f"{pe('gift')} <b>{name}</b>\n"
        f"{pe('id')} Inv ID: <code>{counter}</code>"
    )


# ============================================================
# /remove_gift — Удалить подарок из инвентаря
# ============================================================

@router.message(Command("remove_gift"))
async def cmd_remove_gift(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /remove_gift <user_id> <inv_id>")
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и inv_id!")
        return

    try:
        target_id = int(parts[0])
        inv_id = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, target_id))
    item = c.fetchone()

    if not item:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок не найден в инвентаре!")
        return

    item = dict(item)
    c.execute("DELETE FROM inventory WHERE inv_id = ?", (inv_id,))

    if item["nft_id"]:
        c.execute("DELETE FROM nfts WHERE nft_id = ?", (item["nft_id"],))

    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Подарок удалён!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('id')} Inv ID: {inv_id} | User: {target_id}"
    )


# ============================================================
# /give_nft — Выдать NFT
# ============================================================

@router.message(Command("give_nft"))
async def cmd_give_nft(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /give_nft <user_id> <gift_name> <% модели> <% узора> <% фона>\n"
            f"Пример: /give_nft 123456 Дракон 0.5 1.0 0.3"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 5:
        await message.answer(f"{pe('cross')} Недостаточно параметров!")
        return

    try:
        target_id = int(parts[0])
        gift_name = parts[1]
        model_chance = float(parts[2])
        pattern_chance = float(parts[3])
        bg_chance = float(parts[4])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден!")
        return

    model = min(NFT_MODELS, key=lambda x: abs(x["chance"] - model_chance))
    pattern = min(NFT_PATTERNS, key=lambda x: abs(x["chance"] - pattern_chance))
    bg = min(NFT_BACKGROUNDS, key=lambda x: abs(x["chance"] - bg_chance))

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO nfts (owner_id, gift_name, gift_emoji, model_name, model_chance, "
        "pattern_name, pattern_chance, bg_name, bg_chance) "
        "VALUES (?, ?, '🎁', ?, ?, ?, ?, ?, ?)",
        (target_id, gift_name, model["name"], model["chance"],
         pattern["name"], pattern["chance"], bg["name"], bg["chance"])
    )
    nft_id = c.lastrowid

    counter = get_next_counter("gift_purchase_counter")
    c.execute(
        "INSERT INTO inventory (inv_id, user_id, gift_name, gift_emoji, rarity, is_nft, nft_id) "
        "VALUES (?, ?, ?, '🎁', 'rare', 1, ?)",
        (counter, target_id, gift_name, nft_id)
    )
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>NFT выдан!</b>\n\n"
        f"{pe('nft')} <b>{gift_name}</b> | NFT #{nft_id}\n"
        f"{pe('model')} {model['name']} ({model['chance']}%)\n"
        f"{pe('pattern')} {pattern['name']} ({pattern['chance']}%)\n"
        f"{pe('background')} {bg['name']} ({bg['chance']}%)\n"
        f"{pe('profile')} → {target['first_name']} (<code>{target_id}</code>)"
    )

    await send_notification(target_id,
        f"{pe('nft')} <b>Вам выдан NFT от администрации!</b>\n\n"
        f"{pe('nft')} <b>{gift_name}</b> | NFT #{nft_id}\n"
        f"{pe('model')} {model['name']} ({model['chance']}%)\n"
        f"{pe('pattern')} {pattern['name']} ({pattern['chance']}%)\n"
        f"{pe('background')} {bg['name']} ({bg['chance']}%)"
    )


# ============================================================
# /remove_nft — Удалить NFT
# ============================================================

@router.message(Command("remove_nft"))
async def cmd_remove_nft(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /remove_nft <nft_id>")
        return

    try:
        nft_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный ID!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM nfts WHERE nft_id = ?", (nft_id,))
    nft = c.fetchone()

    if not nft:
        conn.close()
        await message.answer(f"{pe('cross')} NFT не найден!")
        return

    nft = dict(nft)
    c.execute("DELETE FROM nfts WHERE nft_id = ?", (nft_id,))
    c.execute("DELETE FROM inventory WHERE nft_id = ?", (nft_id,))
    c.execute("UPDATE trades SET is_active = 0 WHERE nft_id = ?", (nft_id,))
    c.execute("UPDATE auctions SET is_active = 0 WHERE nft_id = ?", (nft_id,))
    c.execute("UPDATE nft_rentals SET is_active = 0 WHERE nft_id = ?", (nft_id,))
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>NFT удалён!</b>\n\n"
        f"{pe('nft')} <b>{nft['gift_name']}</b> | NFT #{nft_id}\n"
        f"{pe('profile')} Владелец был: <code>{nft['owner_id']}</code>"
    )


# ============================================================
# /ban / /unban
# ============================================================

@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    uid = message.from_user.id

    if not is_admin(uid) and not is_moderator(uid):
        await message.answer(f"{pe('ban_emoji')} Только для модераторов и админов!")
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /ban <user_id> <срок> <причина>\n"
            f"Срок: permanent или часы (например 12)\n"
            f"Пример: /ban 123456 24 Спам"
        )
        return

    parts = command.args.strip().split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(f"{pe('cross')} Укажите user_id, срок и причину!")
        return

    try:
        target_id = int(parts[0])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    duration_str = parts[1]
    reason = parts[2]

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден!")
        return

    if is_admin(target_id):
        await message.answer(f"{pe('cross')} Нельзя забанить администратора!")
        return

    if is_moderator(uid) and not is_admin(uid):
        if duration_str == "permanent":
            await message.answer(f"{pe('cross')} Модераторы не могут банить перманентно!")
            return

        try:
            hours = int(duration_str)
            if hours > 12:
                await message.answer(f"{pe('cross')} Модераторы могут банить максимум на 12 часов!")
                return
        except ValueError:
            await message.answer(f"{pe('cross')} Некорректный срок!")
            return

        conn = get_db()
        c = conn.cursor()
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        c.execute(
            "SELECT COUNT(*) as cnt FROM moder_ban_log WHERE moder_id = ? AND target_id = ? AND banned_at > ?",
            (uid, target_id, week_ago)
        )
        ban_count = c.fetchone()["cnt"]

        if ban_count >= 2:
            conn.close()
            await message.answer(f"{pe('cross')} Вы уже забанили этого пользователя 2 раза на этой неделе!")
            return

        c.execute("INSERT INTO moder_ban_log (moder_id, target_id) VALUES (?, ?)", (uid, target_id))
        conn.commit()
        conn.close()

    if duration_str == "permanent":
        ban_until = "permanent"
        ban_display = "Бессрочно"
    else:
        try:
            hours = int(duration_str)
            ban_until_dt = datetime.now() + timedelta(hours=hours)
            ban_until = ban_until_dt.isoformat()
            ban_display = ban_until_dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer(f"{pe('cross')} Некорректный срок! Укажите часы или 'permanent'")
            return

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET is_banned = 1, ban_reason = ?, ban_until = ?, appeal_count = 0 WHERE user_id = ?",
        (reason, ban_until, target_id)
    )
    conn.commit()
    conn.close()

    role = f"{pe('moder')} Администратор" if is_admin(uid) else f"{pe('moder')} Модератор"

    await message.answer(
        f"{pe('check')} <b>Пользователь забанен!</b>\n\n"
        f"{pe('profile')} {target['first_name']} (<code>{target_id}</code>)\n"
        f"{pe('rules_emoji')} Причина: <b>{reason}</b>\n"
        f"{pe('clock')} До: <b>{ban_display}</b>\n"
        f"{role}: {message.from_user.first_name}"
    )

    await send_notification(target_id,
        f"{pe('ban_emoji')} <b>Вы заблокированы!</b>\n\n"
        f"{pe('rules_emoji')} Причина: <b>{reason}</b>\n"
        f"{pe('clock')} До: <b>{ban_display}</b>\n"
        f"{role}\n\n"
        f"{pe('appeal')} Подайте аппеляцию: /appeal <описание>\n"
        f"{pe('warning')} Максимум 2 аппеляции"
    )


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id) and not is_moderator(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для модераторов и админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /unban <user_id>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET is_banned = 0, ban_reason = '', ban_until = '' WHERE user_id = ?",
        (target_id,)
    )
    conn.commit()
    conn.close()

    await message.answer(f"{pe('check')} Пользователь <code>{target_id}</code> разбанен!")

    await send_notification(target_id,
        f"{pe('check')} <b>Вы разбанены!</b>\n\n"
        f"Добро пожаловать обратно! {pe('success')}"
    )


# ============================================================
# /ban_buy / /unban_buy
# ============================================================

@router.message(Command("ban_buy"))
async def cmd_ban_buy(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /ban_buy <user_id> <причина>")
        return

    parts = command.args.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и причину!")
        return

    try:
        target_id = int(parts[0])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return
    reason = parts[1]

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET is_buy_banned = 1, buy_ban_reason = ? WHERE user_id = ?", (reason, target_id))
    conn.commit()
    conn.close()

    await message.answer(f"{pe('check')} Бан покупок для <code>{target_id}</code>: {reason}")
    await send_notification(target_id,
        f"{pe('ban_emoji')} <b>Вам запрещено покупать подарки!</b>\n{pe('rules_emoji')} Причина: {reason}"
    )


@router.message(Command("unban_buy"))
async def cmd_unban_buy(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /unban_buy <user_id>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET is_buy_banned = 0, buy_ban_reason = '' WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()

    await message.answer(f"{pe('check')} Бан покупок снят для <code>{target_id}</code>!")
    await send_notification(target_id, f"{pe('check')} <b>Бан покупок снят!</b>")


# ============================================================
# /ban_trade / /unban_trade
# ============================================================

@router.message(Command("ban_trade"))
async def cmd_ban_trade(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /ban_trade <user_id> <причина>")
        return

    parts = command.args.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и причину!")
        return

    try:
        target_id = int(parts[0])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return
    reason = parts[1]

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET is_trade_banned = 1, trade_ban_reason = ? WHERE user_id = ?", (reason, target_id))
    conn.commit()
    conn.close()

    await message.answer(f"{pe('check')} Бан торговли для <code>{target_id}</code>: {reason}")
    await send_notification(target_id,
        f"{pe('ban_emoji')} <b>Вам запрещено торговать!</b>\n{pe('rules_emoji')} Причина: {reason}"
    )


@router.message(Command("unban_trade"))
async def cmd_unban_trade(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /unban_trade <user_id>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET is_trade_banned = 0, trade_ban_reason = '' WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()

    await message.answer(f"{pe('check')} Бан торговли снят для <code>{target_id}</code>!")
    await send_notification(target_id, f"{pe('check')} <b>Бан торговли снят!</b>")


# ============================================================
# /warn — Предупреждение
# ============================================================

@router.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject):
    uid = message.from_user.id
    if not is_admin(uid) and not is_moderator(uid):
        await message.answer(f"{pe('ban_emoji')} Только для модераторов и админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /warn <user_id> <причина>")
        return

    parts = command.args.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и причину!")
        return

    try:
        target_id = int(parts[0])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    reason = parts[1]
    role = f"{pe('moder')} Администратор" if is_admin(uid) else f"{pe('moder')} Модератор"

    await message.answer(
        f"{pe('warn_emoji')} <b>Предупреждение выдано!</b>\n\n"
        f"{pe('profile')} <code>{target_id}</code>\n"
        f"{pe('rules_emoji')} Причина: {reason}\n"
        f"{role}: {message.from_user.first_name}"
    )

    await send_notification(target_id,
        f"{pe('warn_emoji')} <b>Вы получили предупреждение!</b>\n\n"
        f"{pe('rules_emoji')} Причина: <b>{reason}</b>\n"
        f"{role}\n\n"
        f"{pe('warning')} Повторные нарушения могут привести к бану!"
    )


# ============================================================
# /add_rules
# ============================================================

@router.message(Command("add_rules"))
async def cmd_add_rules(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /add_rules <текст правил>")
        return

    rules_text = command.args.strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE rules SET text = ? WHERE id = 1", (rules_text,))
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Правила обновлены!</b>\n\n"
        f"{pe('rules_emoji')} {rules_text[:200]}..."
    )


# ============================================================
# /gift_stardom
# ============================================================

@router.message(Command("gift_stardom"))
async def cmd_gift_stardom(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /gift_stardom <user_id> <уровень>")
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите user_id и уровень (1-5)!")
        return

    try:
        target_id = int(parts[0])
        level = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    if level not in STARDOM_LEVELS:
        await message.answer(f"{pe('cross')} Уровень должен быть от 1 до 5!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Пользователь не найден!")
        return

    await activate_stardom(target_id, level)

    sd = STARDOM_LEVELS[level]
    await message.answer(
        f"{pe('check')} <b>Stardom подарен!</b>\n\n"
        f"{pe('profile')} {target['first_name']} (<code>{target_id}</code>)\n"
        f"{pe('stardom')} Уровень: <b>{sd['name']}</b>"
    )


# ============================================================
# /add_promo / /add_promog
# ============================================================

@router.message(Command("add_promo"))
async def cmd_add_promo(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /add_promo <код> <кол-во_звёзд> <кол-во_активаций>\n"
            f"Пример: /add_promo WELCOME 100 50"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 3:
        await message.answer(f"{pe('cross')} Недостаточно параметров!")
        return

    code = parts[0].upper()
    try:
        stars_amount = int(parts[1])
        max_uses = int(parts[2])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO promocodes (code, reward_type, reward_value, max_uses) VALUES (?, 'stars', ?, ?)",
            (code, str(stars_amount), max_uses)
        )
        promo_id = c.lastrowid
        conn.commit()
        conn.close()

        await message.answer(
            f"{pe('check')} <b>Промокод создан!</b>\n\n"
            f"{pe('promo')} Код: <code>{code}</code>\n"
            f"{pe('money')} Награда: <b>{stars_amount} {pe('star')}</b>\n"
            f"{pe('friends')} Активаций: <b>{max_uses}</b>\n"
            f"{pe('id')} ID: {promo_id}"
        )
    except sqlite3.IntegrityError:
        conn.close()
        await message.answer(f"{pe('cross')} Промокод с таким кодом уже существует!")


@router.message(Command("add_promog"))
async def cmd_add_promog(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /add_promog <код> <название_подарка> <кол-во_активаций>\n"
            f"Пример: /add_promog GIFT1 Роза 100"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 3:
        await message.answer(f"{pe('cross')} Недостаточно параметров!")
        return

    code = parts[0].upper()
    gift_name = parts[1]
    try:
        max_uses = int(parts[2])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный параметр!")
        return

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO promocodes (code, reward_type, reward_value, max_uses) VALUES (?, 'gift', ?, ?)",
            (code, gift_name, max_uses)
        )
        promo_id = c.lastrowid
        conn.commit()
        conn.close()

        await message.answer(
            f"{pe('check')} <b>Промокод с подарком создан!</b>\n\n"
            f"{pe('promo')} Код: <code>{code}</code>\n"
            f"{pe('gift')} Подарок: <b>{gift_name}</b>\n"
            f"{pe('friends')} Активаций: <b>{max_uses}</b>"
        )
    except sqlite3.IntegrityError:
        conn.close()
        await message.answer(f"{pe('cross')} Промокод уже существует!")


# ============================================================
# /add_moder / /del_moder
# ============================================================

@router.message(Command("add_moder"))
async def cmd_add_moder(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /add_moder <user_id>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO moderators (user_id) VALUES (?)", (target_id,))
        conn.commit()
        conn.close()

        await message.answer(f"{pe('check')} Модератор <code>{target_id}</code> добавлен!")
        await send_notification(target_id,
            f"{pe('moder')} <b>Вы назначены модератором!</b>\n\n"
            f"Доступные команды:\n"
            f"├ /ban — Бан (до 12ч, макс 2/неделю)\n"
            f"├ /unban — Разбан\n"
            f"└ /warn — Предупреждение"
        )
    except sqlite3.IntegrityError:
        conn.close()
        await message.answer(f"{pe('cross')} Уже является модератором!")


@router.message(Command("del_moder"))
async def cmd_del_moder(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await message.answer(f"{pe('ban_emoji')} Только для админов!")
        return

    if not command.args:
        await message.answer(f"{pe('cross')} Использование: /del_moder <user_id>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректный user_id!")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM moderators WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()

    await message.answer(f"{pe('check')} Модератор <code>{target_id}</code> удалён!")
    await send_notification(target_id, f"{pe('moder')} <b>Вы больше не модератор.</b>")


# ============================================================
# АППЕЛЯЦИИ — /appeal
# ============================================================

@router.message(Command("appeal"))
async def cmd_appeal(message: Message, command: CommandObject):
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.answer(f"{pe('cross')} Ошибка!")
        return

    if not user["is_banned"]:
        await message.answer(f"{pe('cross')} Вы не забанены! Аппеляция не требуется.")
        return

    if user["appeal_count"] >= 2:
        await message.answer(
            f"{pe('cross')} <b>Лимит аппеляций исчерпан!</b>\n\n"
            f"Вы уже подали максимум 2 аппеляции."
        )
        return

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /appeal <описание аппеляции>\n"
            f"{pe('warning')} Осталось аппеляций: {2 - user['appeal_count']}"
        )
        return

    appeal_text = command.args.strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO appeals (user_id, text) VALUES (?, ?)", (user_id, appeal_text))
    appeal_id = c.lastrowid
    c.execute("UPDATE users SET appeal_count = appeal_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    remaining = 1 - user["appeal_count"]

    await message.answer(
        f"{pe('check')} <b>Аппеляция подана!</b>\n\n"
        f"{pe('appeal')} ID: <code>{appeal_id}</code>\n"
        f"{pe('rules_emoji')} Текст: {appeal_text[:200]}\n\n"
        f"{pe('clock')} Ожидайте рассмотрения администратором.\n"
        f"{pe('warning')} Осталось аппеляций: {remaining}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(
        make_inline_button("Разбанить", f"appeal_accept_{appeal_id}_{user_id}", "check"),
        make_inline_button("Отклонить", f"appeal_reject_{appeal_id}_{user_id}", "cross")
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"{pe('appeal')} <b>Новая аппеляция!</b>\n\n"
                f"{pe('id')} ID: <code>{appeal_id}</code>\n"
                f"{pe('profile')} От: {user['first_name']} (<code>{user_id}</code>)\n"
                f"{pe('ban_emoji')} Причина бана: {user['ban_reason']}\n"
                f"{pe('clock')} Бан до: {user['ban_until']}\n\n"
                f"{pe('rules_emoji')} Текст аппеляции:\n<i>{appeal_text}</i>",
                reply_markup=kb.as_markup()
            )
        except Exception:
            pass


# ============================================================
# АППЕЛЯЦИЯ — ПРИНЯТЬ
# ============================================================

@router.callback_query(F.data.startswith("appeal_accept_"))
async def appeal_accept(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{pe_plain('ban_emoji')} Только для админов!", show_alert=True)
        return

    parts = callback.data.split("_")
    appeal_id = int(parts[2])
    user_id = int(parts[3])

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE appeals SET status = 'accepted' WHERE appeal_id = ?", (appeal_id,))
    c.execute("UPDATE users SET is_banned = 0, ban_reason = '', ban_until = '' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    await callback.message.edit_text(
        f"{pe('check')} <b>Аппеляция #{appeal_id} принята!</b>\n\n"
        f"{pe('profile')} Пользователь <code>{user_id}</code> разбанен."
    )

    await send_notification(user_id,
        f"{pe('check')} <b>Ваша аппеляция принята!</b>\n\n"
        f"{pe('appeal')} Аппеляция #{appeal_id}\n"
        f"{pe('success')} Вы разбанены! Добро пожаловать обратно!"
    )


# ============================================================
# АППЕЛЯЦИЯ — ОТКЛОНИТЬ
# ============================================================

@router.callback_query(F.data.startswith("appeal_reject_"))
async def appeal_reject(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(f"{pe_plain('ban_emoji')} Только для админов!", show_alert=True)
        return

    parts = callback.data.split("_")
    appeal_id = int(parts[2])
    user_id = int(parts[3])

    await state.set_state(AppealRejectStates.waiting_reason)
    await state.update_data(reject_appeal_id=appeal_id, reject_user_id=user_id)

    await callback.message.edit_text(
        f"{pe('cross')} <b>Отклонение аппеляции #{appeal_id}</b>\n\n"
        f"{pe('appeal')} Напишите причину отклонения:"
    )
    await callback.answer()


@router.message(AppealRejectStates.waiting_reason)
async def appeal_reject_reason(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    await state.clear()

    appeal_id = data["reject_appeal_id"]
    user_id = data["reject_user_id"]
    reason = message.text.strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE appeals SET status = 'rejected', admin_response = ? WHERE appeal_id = ?", (reason, appeal_id))
    conn.commit()
    conn.close()

    await message.answer(
        f"{pe('check')} <b>Аппеляция #{appeal_id} отклонена!</b>\n\n"
        f"{pe('rules_emoji')} Причина: {reason}"
    )

    await send_notification(user_id,
        f"{pe('cross')} <b>Ваша аппеляция отклонена!</b>\n\n"
        f"{pe('appeal')} Аппеляция #{appeal_id}\n"
        f"{pe('rules_emoji')} Причина отказа: <b>{reason}</b>\n\n"
        f"{pe('warning')} Повторные аппеляции без оснований могут привести к ужесточению бана."
    )


# Конец части 6
# ============================================================
# ============================================================
# ЧАСТЬ 7: Transfer, Inline-мод, Фоновые задачи, Запуск бота
# ============================================================

# ============================================================
# /transfer — Передача подарка
# ============================================================

@router.message(Command("transfer"))
async def cmd_transfer(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /transfer <inv_id> <user_id>\n"
            f"{pe('money')} Комиссия: 15 {pe('star')} (зависит от Stardom)"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите inv_id и user_id!")
        return

    try:
        inv_id = int(parts[0])
        target_id = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    if target_id == user_id:
        await message.answer(f"{pe('cross')} Нельзя передать подарок самому себе!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Получатель не найден! Он должен сначала написать боту.")
        return

    fee = get_gift_transfer_fee(user_id)
    stars = get_stars(user_id)

    if stars < fee:
        await message.answer(
            f"{pe('cross')} Недостаточно звёзд для комиссии! "
            f"Нужно {fee} {pe('star')}, у вас {stars} {pe('star')}"
        )
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, user_id))
    item = c.fetchone()

    if not item:
        conn.close()
        await message.answer(f"{pe('cross')} Подарок не найден в вашем инвентаре!")
        return

    item = dict(item)

    if item["is_nft"]:
        conn.close()
        await message.answer(f"{pe('cross')} Для передачи NFT используйте /transfer_nft!")
        return

    c.execute("UPDATE inventory SET user_id = ? WHERE inv_id = ?", (target_id, inv_id))
    conn.commit()
    conn.close()

    update_stars(user_id, -fee)
    new_balance = get_stars(user_id)

    await message.answer(
        f"{pe('check')} <b>Подарок передан!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('id')} Inv ID: <code>{inv_id}</code>\n"
        f"{pe('send')} Получатель: <code>{target_id}</code>\n"
        f"{pe('money')} Комиссия: <b>{fee} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(target_id,
        f"{pe('gift')} <b>Вам передали подарок!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('id')} Inv ID: <code>{inv_id}</code>\n"
        f"{pe('profile')} От: {message.from_user.first_name} (<code>{user_id}</code>)"
    )


# ============================================================
# /transfer_nft — Передача NFT
# ============================================================

@router.message(Command("transfer_nft"))
async def cmd_transfer_nft(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not command.args:
        await message.answer(
            f"{pe('cross')} Использование: /transfer_nft <nft_id> <user_id>\n"
            f"{pe('money')} Комиссия: 20 {pe('star')} (зависит от Stardom)"
        )
        return

    parts = command.args.strip().split()
    if len(parts) < 2:
        await message.answer(f"{pe('cross')} Укажите nft_id и user_id!")
        return

    try:
        nft_id = int(parts[0])
        target_id = int(parts[1])
    except ValueError:
        await message.answer(f"{pe('cross')} Некорректные параметры!")
        return

    if target_id == user_id:
        await message.answer(f"{pe('cross')} Нельзя передать NFT самому себе!")
        return

    target = get_user(target_id)
    if not target:
        await message.answer(f"{pe('cross')} Получатель не найден!")
        return

    fee = get_nft_transfer_fee(user_id)
    stars = get_stars(user_id)

    if stars < fee:
        await message.answer(
            f"{pe('cross')} Недостаточно звёзд! "
            f"Нужно {fee} {pe('star')}, у вас {stars} {pe('star')}"
        )
        return

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, user_id))
    nft = c.fetchone()

    if not nft:
        conn.close()
        await message.answer(f"{pe('cross')} NFT не найден или не принадлежит вам!")
        return

    nft = dict(nft)

    c.execute("SELECT trade_id FROM trades WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} NFT на торговле! Сначала снимите: /del_trade")
        return

    c.execute("SELECT rental_id FROM nft_rentals WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} NFT в аренде!")
        return

    c.execute("SELECT auction_id FROM auctions WHERE nft_id = ? AND is_active = 1", (nft_id,))
    if c.fetchone():
        conn.close()
        await message.answer(f"{pe('cross')} NFT на аукционе!")
        return

    c.execute("UPDATE nfts SET owner_id = ? WHERE nft_id = ?", (target_id, nft_id))
    c.execute(
        "UPDATE inventory SET user_id = ? WHERE nft_id = ? AND user_id = ?",
        (target_id, nft_id, user_id)
    )
    conn.commit()
    conn.close()

    update_stars(user_id, -fee)
    new_balance = get_stars(user_id)

    crafted = f" {pe('hammer')}" if nft["is_crafted"] else ""

    await message.answer(
        f"{pe('check')} <b>NFT передан!</b>\n\n"
        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}{crafted}\n"
        f"{pe('model')} {nft['model_name']} ({nft['model_chance']}%)\n"
        f"{pe('pattern')} {nft['pattern_name']} ({nft['pattern_chance']}%)\n"
        f"{pe('background')} {nft['bg_name']} ({nft['bg_chance']}%)\n\n"
        f"{pe('send')} Получатель: <code>{target_id}</code>\n"
        f"{pe('money')} Комиссия: <b>{fee} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{new_balance} {pe('star')}</b>"
    )

    await send_notification(target_id,
        f"{pe('nft')} <b>Вам передали NFT!</b>\n\n"
        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}{crafted}\n"
        f"{pe('model')} {nft['model_name']} ({nft['model_chance']}%)\n"
        f"{pe('pattern')} {nft['pattern_name']} ({nft['pattern_chance']}%)\n"
        f"{pe('background')} {nft['bg_name']} ({nft['bg_chance']}%)\n"
        f"{pe('profile')} От: {message.from_user.first_name} (<code>{user_id}</code>)"
    )


# ============================================================
# INLINE МОД — @bot_username
# ============================================================

@router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    query = inline_query.query.strip()
    results = []

    if not query:
        results.append(
            InlineQueryResultArticle(
                id="help",
                title=f"{pe_plain('gift')} Как отправить подарок?",
                description="Введите: inv_id или nft nft_id",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"{pe('gift')} <b>Отправка подарков через Inline</b>\n\n"
                        f"Используйте:\n"
                        f"@bot inv_id — отправить подарок\n"
                        f"@bot nft nft_id — отправить NFT"
                    )
                )
            )
        )
        await inline_query.answer(results, cache_time=5, is_personal=True)
        return

    # ============================================================
    # INLINE — ОТПРАВКА NFT
    # ============================================================
    if query.lower().startswith("nft "):
        nft_part = query[4:].strip()
        try:
            nft_id = int(nft_part)
        except ValueError:
            results.append(
                InlineQueryResultArticle(
                    id="error",
                    title=f"{pe_plain('cross')} Некорректный NFT ID",
                    description="Введите числовой ID",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} Ошибка: некорректный NFT ID"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, user_id))
        nft = c.fetchone()

        if not nft:
            conn.close()
            results.append(
                InlineQueryResultArticle(
                    id="not_found",
                    title=f"{pe_plain('cross')} NFT не найден",
                    description="NFT не найден или не принадлежит вам",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} NFT не найден!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        nft = dict(nft)

        c.execute("SELECT trade_id FROM trades WHERE nft_id = ? AND is_active = 1", (nft_id,))
        if c.fetchone():
            conn.close()
            results.append(
                InlineQueryResultArticle(
                    id="busy",
                    title=f"{pe_plain('cross')} NFT на торговле",
                    description="Сначала снимите с торговли",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} NFT на торговле!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        c.execute("SELECT auction_id FROM auctions WHERE nft_id = ? AND is_active = 1", (nft_id,))
        if c.fetchone():
            conn.close()
            results.append(
                InlineQueryResultArticle(
                    id="busy_auc",
                    title=f"{pe_plain('cross')} NFT на аукционе",
                    description="Снимите с аукциона",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} NFT на аукционе!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        c.execute("SELECT rental_id FROM nft_rentals WHERE nft_id = ? AND is_active = 1", (nft_id,))
        if c.fetchone():
            conn.close()
            results.append(
                InlineQueryResultArticle(
                    id="busy_rent",
                    title=f"{pe_plain('cross')} NFT в аренде",
                    description="NFT сдан в аренду",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} NFT в аренде!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        conn.close()

        fee = get_nft_transfer_fee(user_id)
        stars = get_stars(user_id)

        if stars < fee:
            results.append(
                InlineQueryResultArticle(
                    id="no_stars",
                    title=f"{pe_plain('cross')} Недостаточно звёзд (нужно {fee}{pe_plain('star')})",
                    description=f"У вас {stars}{pe_plain('star')}, нужно {fee}{pe_plain('star')} комиссии",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} Недостаточно звёзд для передачи NFT!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        transfer_id = hashlib.md5(f"nft_{nft_id}_{user_id}_{time.time()}".encode()).hexdigest()[:16]

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO inline_transfers (transfer_id, sender_id, nft_id, transfer_type) "
            "VALUES (?, ?, ?, 'nft')",
            (transfer_id, user_id, nft_id)
        )
        conn.commit()
        conn.close()

        crafted = f" {pe_plain('hammer')} Крафт" if nft["is_crafted"] else ""

        results.append(
            InlineQueryResultArticle(
                id=transfer_id,
                title=f"{pe_plain('nft')} Отправить NFT #{nft_id} — {nft['gift_name']}",
                description=(
                    f"{pe_plain('model')}{nft['model_name']}({nft['model_chance']}%) | "
                    f"Комиссия: {fee}{pe_plain('star')}"
                ),
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"{pe('nft')} <b>NFT подарок!</b> {pe('success')}\n\n"
                        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}{crafted}\n"
                        f"{pe('model')} Модель: <b>{nft['model_name']}</b> ({nft['model_chance']}%)\n"
                        f"{pe('pattern')} Узор: <b>{nft['pattern_name']}</b> ({nft['pattern_chance']}%)\n"
                        f"{pe('background')} Фон: <b>{nft['bg_name']}</b> ({nft['bg_chance']}%)\n\n"
                        f"{pe('profile')} От: {inline_query.from_user.first_name}\n"
                        f"{pe('gift')} Нажмите кнопку чтобы получить!"
                    )
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        make_inline_button("Получить NFT!", f"claim_nft_{transfer_id}", "gift")
                    ]]
                )
            )
        )

    # ============================================================
    # INLINE — ОТПРАВКА ПОДАРКА
    # ============================================================
    else:
        try:
            inv_id = int(query)
        except ValueError:
            results.append(
                InlineQueryResultArticle(
                    id="error",
                    title=f"{pe_plain('cross')} Некорректный ID",
                    description="Введите числовой Inv ID или 'nft <id>'",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} Некорректный ID!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, user_id))
        item = c.fetchone()

        if not item:
            conn.close()
            results.append(
                InlineQueryResultArticle(
                    id="not_found",
                    title=f"{pe_plain('cross')} Подарок не найден",
                    description="Подарок не найден в вашем инвентаре",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} Подарок не найден!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        item = dict(item)

        if item["is_nft"]:
            conn.close()
            results.append(
                InlineQueryResultArticle(
                    id="use_nft",
                    title=f"{pe_plain('info')} Для NFT используйте: nft <id>",
                    description="Введите: nft <nft_id>",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('info')} Для отправки NFT используйте: @bot nft <nft_id>"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        conn.close()

        fee = get_gift_transfer_fee(user_id)
        stars = get_stars(user_id)

        if stars < fee:
            results.append(
                InlineQueryResultArticle(
                    id="no_stars",
                    title=f"{pe_plain('cross')} Недостаточно звёзд (нужно {fee}{pe_plain('star')})",
                    description=f"У вас {stars}{pe_plain('star')}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{pe('cross')} Недостаточно звёзд для передачи!"
                    )
                )
            )
            await inline_query.answer(results, cache_time=5, is_personal=True)
            return

        transfer_id = hashlib.md5(f"gift_{inv_id}_{user_id}_{time.time()}".encode()).hexdigest()[:16]

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO inline_transfers (transfer_id, sender_id, inv_id, transfer_type) "
            "VALUES (?, ?, ?, 'gift')",
            (transfer_id, user_id, inv_id)
        )
        conn.commit()
        conn.close()

        rarity_emoji = pe_plain('common') if item["rarity"] == "common" else pe_plain('rare')
        limited_label = f" {pe_plain('limit')} Лимитированный" if item["is_limited"] else ""

        results.append(
            InlineQueryResultArticle(
                id=transfer_id,
                title=f"{pe_plain('gift')} Отправить {item['gift_name']}",
                description=f"Inv ID: {inv_id} | Комиссия: {fee}{pe_plain('star')}",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"{pe('gift')} <b>Подарок для вас!</b> {pe('success')}\n\n"
                        f"{rarity_emoji} {item['gift_emoji']} <b>{item['gift_name']}</b>{limited_label}\n\n"
                        f"{pe('profile')} От: {inline_query.from_user.first_name}\n"
                        f"{pe('gift')} Нажмите кнопку чтобы получить!"
                    )
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        make_inline_button("Получить подарок!", f"claim_gift_{transfer_id}", "gift")
                    ]]
                )
            )
        )

    await inline_query.answer(results, cache_time=5, is_personal=True)


# ============================================================
# ПОЛУЧЕНИЕ ПОДАРКА ЧЕРЕЗ INLINE
# ============================================================

@router.callback_query(F.data.startswith("claim_gift_"))
async def claim_gift_inline(callback: CallbackQuery):
    transfer_id = callback.data[len("claim_gift_"):]
    claimer_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inline_transfers WHERE transfer_id = ?", (transfer_id,))
    transfer = c.fetchone()

    if not transfer:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Передача не найдена!", show_alert=True)
        return

    transfer = dict(transfer)

    if transfer["is_claimed"]:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Этот подарок уже получен!", show_alert=True)
        return

    if transfer["sender_id"] == claimer_id:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Нельзя получить свой подарок!", show_alert=True)
        return

    ensure_user(claimer_id, callback.from_user.username or "", callback.from_user.first_name or "")

    inv_id = transfer["inv_id"]
    sender_id = transfer["sender_id"]

    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, sender_id))
    item = c.fetchone()

    if not item:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Подарок больше не доступен!", show_alert=True)
        return

    item = dict(item)

    fee = get_gift_transfer_fee(sender_id)
    stars = get_stars(sender_id)

    if stars < fee:
        conn.close()
        await callback.answer(
            f"{pe_plain('cross')} У отправителя недостаточно звёзд для комиссии!",
            show_alert=True
        )
        return

    c.execute("UPDATE inventory SET user_id = ? WHERE inv_id = ?", (claimer_id, inv_id))
    c.execute(
        "UPDATE inline_transfers SET is_claimed = 1, claimed_by = ? WHERE transfer_id = ?",
        (claimer_id, transfer_id)
    )
    conn.commit()
    conn.close()

    update_stars(sender_id, -fee)

    claimer_name = callback.from_user.first_name

    try:
        await callback.message.edit_text(
            f"{pe('gift')} <b>Подарок получен!</b> {pe('check')}\n\n"
            f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
            f"{pe('id')} Inv ID: <code>{inv_id}</code>\n\n"
            f"{pe('profile')} Получил: <b>{claimer_name}</b>\n"
            f"{pe('success')} Подарок доставлен!"
        )
    except Exception:
        pass

    await callback.answer(f"{pe_plain('success')} Вы получили {item['gift_name']}!", show_alert=True)

    await send_notification(sender_id,
        f"{pe('send')} <b>Ваш подарок получен!</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('profile')} Получил: {claimer_name} (<code>{claimer_id}</code>)\n"
        f"{pe('money')} Комиссия: {fee} {pe('star')}"
    )


# ============================================================
# ПОЛУЧЕНИЕ NFT ЧЕРЕЗ INLINE
# ============================================================

@router.callback_query(F.data.startswith("claim_nft_"))
async def claim_nft_inline(callback: CallbackQuery):
    transfer_id = callback.data[len("claim_nft_"):]
    claimer_id = callback.from_user.id

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inline_transfers WHERE transfer_id = ?", (transfer_id,))
    transfer = c.fetchone()

    if not transfer:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Передача не найдена!", show_alert=True)
        return

    transfer = dict(transfer)

    if transfer["is_claimed"]:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Этот NFT уже получен!", show_alert=True)
        return

    if transfer["sender_id"] == claimer_id:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} Нельзя получить свой NFT!", show_alert=True)
        return

    ensure_user(claimer_id, callback.from_user.username or "", callback.from_user.first_name or "")

    nft_id = transfer["nft_id"]
    sender_id = transfer["sender_id"]

    c.execute("SELECT * FROM nfts WHERE nft_id = ? AND owner_id = ?", (nft_id, sender_id))
    nft = c.fetchone()

    if not nft:
        conn.close()
        await callback.answer(f"{pe_plain('cross')} NFT больше не доступен!", show_alert=True)
        return

    nft = dict(nft)

    fee = get_nft_transfer_fee(sender_id)
    stars = get_stars(sender_id)

    if stars < fee:
        conn.close()
        await callback.answer(
            f"{pe_plain('cross')} У отправителя недостаточно звёзд!",
            show_alert=True
        )
        return

    c.execute("UPDATE nfts SET owner_id = ? WHERE nft_id = ?", (claimer_id, nft_id))
    c.execute(
        "UPDATE inventory SET user_id = ? WHERE nft_id = ? AND user_id = ?",
        (claimer_id, nft_id, sender_id)
    )
    c.execute(
        "UPDATE inline_transfers SET is_claimed = 1, claimed_by = ? WHERE transfer_id = ?",
        (claimer_id, transfer_id)
    )
    conn.commit()
    conn.close()

    update_stars(sender_id, -fee)

    claimer_name = callback.from_user.first_name
    crafted = f" {pe('hammer')}" if nft["is_crafted"] else ""

    try:
        await callback.message.edit_text(
            f"{pe('nft')} <b>NFT получен!</b> {pe('check')}\n\n"
            f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}{crafted}\n"
            f"{pe('model')} Модель: <b>{nft['model_name']}</b> ({nft['model_chance']}%)\n"
            f"{pe('pattern')} Узор: <b>{nft['pattern_name']}</b> ({nft['pattern_chance']}%)\n"
            f"{pe('background')} Фон: <b>{nft['bg_name']}</b> ({nft['bg_chance']}%)\n\n"
            f"{pe('profile')} Получил: <b>{claimer_name}</b> {pe('check')}\n"
            f"{pe('success')} NFT доставлен!"
        )
    except Exception:
        pass

    await callback.answer(f"{pe_plain('success')} Вы получили NFT #{nft_id}!", show_alert=True)

    is_new = grant_achievement(claimer_id, "first_nft")

    await send_notification(sender_id,
        f"{pe('send')} <b>Ваш NFT получен!</b>\n\n"
        f"{nft['gift_emoji']} <b>{nft['gift_name']}</b> | NFT #{nft_id}\n"
        f"{pe('profile')} Получил: {claimer_name} (<code>{claimer_id}</code>)\n"
        f"{pe('money')} Комиссия: {fee} {pe('star')}"
    )

    if is_new:
        await send_notification(claimer_id,
            f"{pe('achieve')} {pe('medal')} <b>Достижение разблокировано: Первый NFT!</b>"
        )


# ============================================================
# ФОНОВЫЕ ЗАДАЧИ
# ============================================================

async def check_limited_gifts():
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("UPDATE limited_gifts SET is_active = 0 WHERE is_active = 1 AND expires_at <= ?", (now,))
    conn.commit()
    conn.close()


async def check_stardom_expiry():
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "SELECT user_id FROM users WHERE stardom_level > 0 AND stardom_expires != '' AND stardom_expires <= ?",
        (now,)
    )
    expired_users = [dict(row) for row in c.fetchall()]

    for u in expired_users:
        c.execute(
            "UPDATE users SET stardom_level = 0, stardom_expires = '' WHERE user_id = ?",
            (u["user_id"],)
        )
        await send_notification(u["user_id"],
            f"{pe('stardom')} <b>Ваша подписка Stardom истекла!</b>\n\n"
            f"{pe('sparkles')} Продлите подписку в разделе Stardom."
        )

    conn.commit()
    conn.close()


async def check_bans_expiry():
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "SELECT user_id FROM users WHERE is_banned = 1 AND ban_until != 'permanent' "
        "AND ban_until != '' AND ban_until <= ?",
        (now,)
    )
    expired = [dict(row) for row in c.fetchall()]

    for u in expired:
        c.execute(
            "UPDATE users SET is_banned = 0, ban_reason = '', ban_until = '' WHERE user_id = ?",
            (u["user_id"],)
        )
        await send_notification(u["user_id"],
            f"{pe('check')} <b>Ваш бан истёк!</b>\n\n"
            f"{pe('success')} Добро пожаловать обратно!"
        )

    conn.commit()
    conn.close()


async def cleanup_inline_transfers():
    conn = get_db()
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    c.execute("DELETE FROM inline_transfers WHERE is_claimed = 0 AND created_at <= ?", (cutoff,))
    conn.commit()
    conn.close()


async def background_tasks():
    while True:
        try:
            await check_auctions()
            await check_rentals()
            await check_limited_gifts()
            await check_stardom_expiry()
            await check_bans_expiry()
            await cleanup_inline_transfers()
        except Exception as e:
            logger.error(f"Ошибка в фоновых задачах: {e}")

        await asyncio.sleep(60)


# ============================================================
# КНОПКА УЛУЧШЕНИЯ ИЗ ИНВЕНТАРЯ
# ============================================================

@router.callback_query(F.data.startswith("inv_upgrade_"))
async def inv_upgrade_to_nft(callback: CallbackQuery):
    inv_id = int(callback.data.split("_")[2])

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM inventory WHERE inv_id = ? AND user_id = ?", (inv_id, callback.from_user.id))
    item = c.fetchone()
    conn.close()

    if not item:
        await callback.answer(f"{pe_plain('cross')} Подарок не найден!", show_alert=True)
        return

    item = dict(item)

    if item["rarity"] != "rare":
        await callback.answer(f"{pe_plain('cross')} Только редкие подарки!", show_alert=True)
        return

    if item["is_nft"]:
        await callback.answer(f"{pe_plain('cross')} Уже NFT!", show_alert=True)
        return

    fee = get_nft_create_fee(callback.from_user.id)

    kb = InlineKeyboardBuilder()
    kb.row(make_inline_button(f"Улучшить за {fee}{pe_plain('star')}", f"upgrade_to_nft_{inv_id}", "upgrade"))
    kb.row(make_inline_button("Отмена", "inventory_0", "back"))

    await callback.message.edit_text(
        f"{pe('upgrade')} <b>Улучшение до NFT</b>\n\n"
        f"{item['gift_emoji']} <b>{item['gift_name']}</b>\n"
        f"{pe('money')} Комиссия: <b>{fee} {pe('star')}</b>\n"
        f"{pe('money')} Баланс: <b>{get_stars(callback.from_user.id)} {pe('star')}</b>\n\n"
        f"{pe('warning')} Характеристики будут случайными!",
        reply_markup=kb.as_markup()
    )


# ============================================================
# ОБРАБОТКА НЕИЗВЕСТНЫХ СООБЩЕНИЙ
# ============================================================

@router.message(F.text)
async def unknown_message(message: Message):
    if message.text.startswith("/"):
        await message.answer(
            f"{pe('cross')} Неизвестная команда!\n"
            f"Используйте /help для списка команд."
        )
        return

    text = message.text.strip()
    known_buttons = [
        "Профиль", "Маркет", "Маркет #2", "Торговля",
        "Крафт", "Stardom", "Промокоды", "Топ", "Друзья"
    ]

    for btn in known_buttons:
        if btn in text:
            return


# ============================================================
# ЗАПУСК БОТА
# ============================================================

async def on_startup():
    logger.info(f"{pe_plain('star')} Бот запускается...")
    me = await bot.get_me()
    logger.info(f"{pe_plain('check')} Бот @{me.username} ({me.id}) запущен!")


async def main():
    init_db()
    asyncio.create_task(background_tasks())
    await on_startup()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{pe_plain('cross')} Бот остановлен.")
    except Exception as e:
        logger.error(f"{pe_plain('cross')} Критическая ошибка: {e}")


# ============================================================
# КОНЕЦ БОТА — ВСЕ 7 ЧАСТЕЙ
# ============================================================
