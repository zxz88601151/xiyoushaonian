# MiniAsura 存档外围 —— schema 12（V2.0 §3 + V2.1 §2 + V2.2 §3 + V2.3 金币/难度 + V2.4 强化/保底符 + V2.5 爬塔 + V2.8 图鉴/成就/统计 + V2.9-A 保底计数 + V2.9-D1 称号/变体击杀/幻影榜 + V2.9-D2 日常/周常/签到 + V3.0-A 碎片/宝石/属性点）。
# 路径由登录链经 set_path() 注入；engine 只调 load/write，不认识账号。
# CLI dev 模式（python engine.py）不注入 = 用默认路径，v1 行为保持。
import json
import os

import daily     # V2.9-D2：跨日/跨周滚动（daily 不依赖 save，无循环导入）
import progress  # V2.8：成就/图鉴口径（progress 只依赖 mypack，无循环导入）

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "save.json")
_USER = ""

SCHEMA = 12
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
    # 迁移链：v1（cleared）→ v2（week/playtime）→ v3（背包/装备）→ v4（任务/图/药/仓库）→ v5（金币/难度）→ v6（强化/保底符）→ v7（爬塔）→ v8（图鉴/成就/统计）→ v9（保底计数）
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
    old.setdefault("protect", 0)           # V2.4：保底符张数
    old.setdefault("tower_best", 0)        # V2.5：无底洞历史最高层
    old.setdefault("tower_layer", 0)       # V2.5：本次爬塔所在层（支持续爬）
    old.setdefault("achievements", [])     # V2.8：已解锁成就 id（并集永不回归）
    old.setdefault("codex_weapons", [])    # V2.8：曾经拥有过的武器名（卖出不灭灯）
    old.setdefault("total_damage", 0)      # V2.8：累计总伤害
    old.setdefault("staff_pity", 0)        # V2.9-A：无级别保底计数（跨周目继承）
    old.setdefault("elite_kills", 0)       # V2.9-D1：精英击杀累计（跨周目继承，与 kills 分离）
    old.setdefault("rare_kills", 0)        # V2.9-D1：稀有击杀累计
    old.setdefault("title", "")            # V2.9-D1：当前佩戴称号 id（空串=无）
    old.setdefault("records", {"best_dealt": 0, "best_dealt_mon": "",
                               "best_rounds": 0, "best_rounds_mon": ""})   # V2.9-D1：幻影榜
    old.setdefault("daily", {"date": "", "base": {}, "claimed": []})       # V2.9-D2：日常
    old.setdefault("weekly", {"week": "", "base": {}, "claimed": []})      # V2.9-D2：周常
    old.setdefault("checkin", {"last": "", "streak": 0, "total": 0})       # V2.9-D2：签到
    old.setdefault("shard", 0)            # V3.0-A：宝石碎片（不占格，G3）
    old.setdefault("gems", [])            # V3.0-A：宝石栏（独立于装备背包）
    old.setdefault("attr", {"spent": {"atk": 0, "hp": 0, "def": 0, "crit": 0}})   # V3.0-A：属性点
    old.setdefault("set_seen", [])        # V3.0-A：见过的套装 key（纯记录）
    for it in list(old.get("inventory", [])) + list(old.get("storage", [])):
        if isinstance(it, dict):
            it.setdefault("enh", 0)        # V2.4：旧装备补强化等级
    for it in (old.get("equipment") or {}).values():
        if isinstance(it, dict):
            it.setdefault("enh", 0)
    old["schema"] = SCHEMA
    return old


def _prev():
    """读旧档（只读本文件，不触发迁移写）：codex/成就并集合并用。读不到/读坏返回 {}。"""
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write(player, next_index, week, playtime, maps_cleared=0,
          tracker=None, storage=None, difficulty=0):
    # V2.8：codex/成就取“旧档 ∪ 本次”并集（+10 装备被回收后成就仍保留；周目重开也继承）
    prev = _prev()
    kills = dict(tracker.kills) if tracker else {}
    codex = progress.merge_codex(prev.get("codex_weapons", []), player, storage)
    norm = {"level": player["level"], "kills": kills, "maps_cleared": maps_cleared,
            "week": week, "tower_best": player.get("tower_best", 0), "codex_weapons": codex,
            "inventory": player.get("inventory", []), "storage": storage or [],
            "equipment": player.get("equipment", {}),
            "elite_kills": player.get("elite_kills", 0), "rare_kills": player.get("rare_kills", 0)}
    ach = sorted(set(prev.get("achievements", [])) | progress.evaluate(norm))
    write_raw({
        "schema": SCHEMA, "user": _USER,
        "level": player["level"], "exp": player["exp"],
        "hp": player["hp"], "mp": player["mp"], "attack": player["attack"],
        "gold": player.get("gold", 0), "difficulty": difficulty,
        "protect": player.get("protect", 0),
        "next": next_index, "week": week, "playtime": playtime,
        "inventory": player.get("inventory", []),
        "equipment": player.get("equipment", {k: None for k in SLOT_KEYS}),
        "quest_flags": dict(tracker.flags) if tracker else {},
        "kills": dict(tracker.kills) if tracker else {},
        "maps_cleared": maps_cleared,
        "potions": player.get("potions", {"hp": 0, "mp": 0}),
        "storage": storage or [],
        "tower_best": player.get("tower_best", 0),
        "tower_layer": player.get("tower_layer", 0),
        "achievements": ach,
        "codex_weapons": codex,
        "total_damage": player.get("total_damage", 0),
        "staff_pity": player.get("staff_pity", 0),
        "elite_kills": player.get("elite_kills", 0), "rare_kills": player.get("rare_kills", 0),
        "title": player.get("title", ""),
        "records": player.get("records") or {"best_dealt": 0, "best_dealt_mon": "",
                                             "best_rounds": 0, "best_rounds_mon": ""},
        "daily": prev.get("daily") or {}, "weekly": prev.get("weekly") or {}, "checkin": prev.get("checkin") or {},
        "shard": player.get("shard", 0), "gems": player.get("gems") or [],
        "attr": player.get("attr") or {"spent": {"atk": 0, "hp": 0, "def": 0, "crit": 0}},
        "set_seen": player.get("set_seen") or [],
    })


def write_raw(data):
    daily.touch(data)          # V2.9-D2：跨日/跨周滚动（所有写档路径统一收口）
    d = os.path.dirname(PATH)
    if d and not os.path.exists(d):
        os.makedirs(d)          # 首次写档时补建 saves/<server>/<user>/ 目录链
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
