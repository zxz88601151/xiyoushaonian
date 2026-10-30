# V3.0-A 属性点 —— 升级得点 / 四维分配 / 免费无限洗点（G9-G11）。
# 只维护 player["attr"]["spent"]；加成本身由 engine.apply_gear 经 gear.totals 一次并入。
import configparser
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DIMS = ("atk", "hp", "def", "crit")
NAMES = {"atk": "攻击", "hp": "生命", "def": "防御", "crit": "暴击"}
_BLANK = {"atk": 0, "hp": 0, "def": 0, "crit": 0}


def _cfg():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    return cfg


def state(player):
    """{spent: 四维}——脏数据按 0 处理，未知维度丢弃（fail-closed）。"""
    st = player.get("attr") or {}
    spent = dict(_BLANK)
    for k, v in (st.get("spent") or {}).items():
        if k in DIMS:
            spent[k] = max(0, int(v))
    return {"spent": spent}


def total(player, cfg=None):
    """累计可获得点数：Lv.2 起每级 3 点（G9），等级上限由 game.ini 控制。"""
    cfg = cfg or _cfg()
    return max(0, int(player.get("level", 1)) - 1) * cfg.getint("attr", "points_per_level", fallback=3)


def free(player, cfg=None):
    return total(player, cfg) - sum(state(player)["spent"].values())


def add(player, dim, n=1, cfg=None):
    """分配 n 点；点数不足或维度非法一律拒绝，不改档（Q8 同款：拒绝路径零副作用）。"""
    if dim not in DIMS:
        return False, "未知属性 %s" % dim
    if n <= 0:
        return False, "点数必须为正"
    left = free(player, cfg)
    if left < n:
        return False, "可用点数不足（剩 %d）" % left
    st = state(player)
    st["spent"][dim] += n
    player["attr"] = st
    return True, "%s +%d" % (NAMES[dim], n)


def reset(player):
    """免费无限洗点（G10）：spent 清零，点数全额退回 free。"""
    player["attr"] = {"spent": dict(_BLANK)}
    return True, "已洗点，点数全额退回"


def bonus(player, cfg=None):
    """面板加成：全 0 时返回全 0（零影响红线，门禁第 1 条）。"""
    cfg = cfg or _cfg()
    sp = state(player)["spent"]
    return {"atk": sp["atk"] * cfg.getfloat("attr", "atk_flat", fallback=0),
            "hp": sp["hp"] * cfg.getfloat("attr", "hp_flat", fallback=0),
            "def": sp["def"] * cfg.getfloat("attr", "def_flat", fallback=0),
            "crit": sp["crit"] * cfg.getfloat("attr", "crit_bp", fallback=0) / 100.0}
