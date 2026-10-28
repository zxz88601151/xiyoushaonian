# MiniAsura 存档外围 —— schema 5（V2.0 §3 + V2.1 §2 + V2.2 §3 + V2.3 金币/难度）。
# 路径由登录链经 set_path() 注入；engine 只调 load/write，不认识账号。
# CLI dev 模式（python engine.py）不注入 = 用默认路径，v1 行为保持。
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "save.json")
_USER = ""

SCHEMA = 5
SLOT_KEYS = ("weapon", "helm", "armor", "belt", "boots")


def set_path(path, user=""):
    global PATH, _USER
    PATH = path
    _USER = user


def load():
    if not os.path.exists(PATH):
        return None
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("schema") != SCHEMA:
        data = _migrate(data)
        write_raw(data)
    return data


def _migrate(old):
    # 迁移链：v1（cleared 布尔）→ v2（week/playtime）→ v3（背包/装备）→ v4（任务/图/药/仓库）→ v5（金币/难度）
    # 规则只补默认值不改已有数值——升档不许丢东西
    if "cleared" in old:
        old["week"] = 1 if old.pop("cleared") else 0
    old.setdefault("week", 0)
    old.setdefault("playtime", 0)
    old.setdefault("user", _USER)
    old.setdefault("inventory", [])
    old.setdefault("equipment", {k: None for k in SLOT_KEYS})
    old.setdefault("quest_flags", {})      # V2.2：任务状态
    old.setdefault("kills", {})            # V2.2：击杀/败北计数
    old.setdefault("maps_cleared", 0)      # V2.2：已通图数
    old.setdefault("potions", {"hp": 0, "mp": 0})
    old.setdefault("storage", [])          # V2.2：仓库（背包第二页）
    old.setdefault("gold", 0)              # V2.3：金币
    old.setdefault("difficulty", 0)        # V2.3：难度 0普通/1精英/2噩梦
    old["schema"] = SCHEMA
    return old


def write(player, next_index, week, playtime, maps_cleared=0,
          tracker=None, storage=None, difficulty=0):
    write_raw({
        "schema": SCHEMA, "user": _USER,
        "level": player["level"], "exp": player["exp"],
        "hp": player["hp"], "mp": player["mp"], "attack": player["attack"],
        "gold": player.get("gold", 0), "difficulty": difficulty,
        "next": next_index, "week": week, "playtime": playtime,
        "inventory": player.get("inventory", []),
        "equipment": player.get("equipment", {k: None for k in SLOT_KEYS}),
        "quest_flags": dict(tracker.flags) if tracker else {},
        "kills": dict(tracker.kills) if tracker else {},
        "maps_cleared": maps_cleared,
        "potions": player.get("potions", {"hp": 0, "mp": 0}),
        "storage": storage or [],
    })


def write_raw(data):
    d = os.path.dirname(PATH)
    if d and not os.path.exists(d):
        os.makedirs(d)          # 首次写档时补建 saves/<server>/<user>/ 目录链
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
