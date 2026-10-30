# V3.0-A 套装 —— 2 件 / 4 件效果（G7：4 件不叠 2 件），紫装掉落按稳定种子掷（G8）。
# 套装件只是装备上的一个 set 标记，不加新存档字段；判定与汇总只读 equipment。
import configparser
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

FLAT = ("atk", "hp", "def", "crit", "critdmg", "leech")   # 平铺键（crit/critdmg 为百分点）
PCT = ("atkp", "hpp")                                      # 百分比键（按平铺基数放大）
SLOTS = ("weapon", "helm", "armor", "belt", "boots")       # 与 gear.SLOTS 同序（此处独立定义免循环导入）
_SETS = {}


def load():
    """sets.txt（key|名称|槽位|2 件效果|4 件效果）→ {key: 行}；加套装 = 加数据行。"""
    if not _SETS:
        text = mypack.read(os.path.join(HERE, "assets.mpak"), "sets.txt").decode("utf-8")
        for line in text.splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            key, name, slots, two, four = line.split("|")
            _SETS[key] = {"key": key, "name": name, "slots": slots.split(","),
                          "two": _parse(two), "four": _parse(four)}
    return _SETS


def _parse(text):
    """'atk:12;critdmg:30' → {'atk': 12.0, 'critdmg': 30.0}；空串 = 无效果。"""
    out = {}
    for part in (text or "").split(";"):
        part = part.strip()
        if part:
            k, v = part.split(":")
            out[k.strip()] = float(v)
    return out


def active(equipment):
    """{套装 key: 已穿戴件数}——只数认得出来的套装件。"""
    known, cnt = load(), {}
    for it in (equipment or {}).values():
        key = (it or {}).get("set")
        if key in known:
            cnt[key] = cnt.get(key, 0) + 1
    return cnt


def bonus(equipment):
    """2 件触发 2 件效果；4 件只吃 4 件效果（互斥取高，G7）。"""
    out = {}
    for key, n in active(equipment).items():
        row = load()[key]
        eff = row["four"] if n >= 4 else (row["two"] if n >= 2 else {})
        for k, v in eff.items():
            out[k] = out.get(k, 0.0) + v
    return out


def _seed(item):
    """稳定种子：部位+等级+品质+主属性，md5 取模（与 encounter 掷骰同思路，不吃进程随机）。"""
    raw = "|".join([str(item.get("slot")), str(item.get("lv")), str(item.get("quality")),
                    ",".join("%s=%.3f" % (k, v) for k, v in sorted((item.get("main") or {}).items()))])
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)


def roll_set(item, cfg=None):
    """紫装掉落时判定是否成套件（G8）：只改"是不是套装件"，不改品质概率、不吃随机流。"""
    if int(item.get("quality", 0)) < 2:
        return None
    if cfg is None:
        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    if _seed(item) % 100 >= cfg.getint("set", "drop_pct", fallback=0):
        return None
    slot = SLOTS[int(item.get("slot", 0))]
    cand = sorted(k for k, r in load().items() if slot in r["slots"])
    return cand[_seed(item) // 100 % len(cand)] if cand else None
