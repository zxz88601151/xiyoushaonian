# V3.0-A 宝石 —— 碎片开宝 / 同级三合一 / 镶嵌 / 拆卸 / 面板汇总（G1-G6）。
# 只做簿记与查表：数值住 gems.txt，镶嵌状态长在装备上（holes/gems），不占 schema 新字段。
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

HOLES = (0, 1, 2)          # 白/蓝/紫孔位（G1，与 gear.AFFIX_COUNT 同构；此处独立定义避免循环导入）
MAX_LV = 5                 # G6：5 级封顶
MERGE_COST = 3             # 三份同级同种合成一份高一级
_ROWS = {}


def load():
    """gems.txt（key|名称|属性|每级数值）→ {key: 行}；加宝石 = 加数据行，不改代码。"""
    if not _ROWS:
        text = mypack.read(os.path.join(HERE, "assets.mpak"), "gems.txt").decode("utf-8")
        for line in text.splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            key, name, stat, per = line.split("|")
            _ROWS[key] = {"key": key, "name": name, "stat": stat, "per": float(per)}
    return _ROWS


def label(gem):
    row = load().get((gem or {}).get("key"))
    return "%s %d 级" % (row["name"], int(gem.get("lv", 1))) if row else "?"


def holes_of(item):
    """孔位按品质补算：旧档装备没有 holes 字段也不写档改写（G1 迁移纪律）。"""
    return int(item.get("holes", HOLES[int(item.get("quality", 0))]))


def slots_of(item):
    """已开孔的槽位（长度 = holes_of，空槽为 None）；不修改传入 item。"""
    gs = list(item.get("gems") or [])
    return (gs + [None] * holes_of(item))[:holes_of(item)]


def socket(item, idx, gem):
    """把 gem 镶进第 idx 孔：越界 / 已占用 / 同类重复一律拒绝（G2 无损，故不掷骰）。"""
    if not 0 <= idx < holes_of(item):
        return False, "这件装备只有 %d 个孔" % holes_of(item)
    gs = slots_of(item)
    if gs[idx]:
        return False, "第 %d 个孔已经镶了 %s" % (idx + 1, label(gs[idx]))
    if any(g and g.get("key") == gem.get("key") for g in gs):
        return False, "同一件装备不能镶两颗同类宝石"
    gs[idx] = dict(gem)
    item["gems"] = gs
    return True, "已镶嵌 %s" % label(gem)


def unsocket(item, idx):
    """拆卸：宝石原样退回、孔位清空、无损免费（G2）。返回宝石 dict 或 None。"""
    gs = slots_of(item)
    if not (0 <= idx < len(gs)) or not gs[idx]:
        return None
    gem = dict(gs[idx])
    gs[idx] = None
    item["gems"] = gs
    return gem


def open_shard(player, cfg, rng=random):
    """3 碎片开 1 颗 1 级宝石（种类随机，只随种类不随成败——没有赌输这回事）。"""
    have, stash = int(player.get("shard", 0)), cfg.getint("gem", "stash", fallback=20)
    if have < MERGE_COST:
        return False, "碎片不足（%d/%d）" % (have, MERGE_COST)
    if len(player.get("gems") or []) >= stash:
        return False, "宝石栏已满（%d 格），先合成或镶嵌" % stash
    key = rng.choice(sorted(load()))
    player["shard"] = have - MERGE_COST
    player.setdefault("gems", []).append({"key": key, "lv": 1})
    return True, "开出一颗 %s" % label({"key": key, "lv": 1})


def merge(player, key, lv):
    """3 颗同级同种 → 1 颗高一级；封顶 5 级不吃 6 级（G6）。"""
    lv = int(lv)
    if lv >= MAX_LV:
        return False, "已是最高级（%d 级）" % MAX_LV
    gems = player.get("gems") or []
    same = [g for g in gems if g.get("key") == key and int(g.get("lv", 1)) == lv]
    if len(same) < MERGE_COST:
        return False, "同类同级不足（%d/%d）" % (len(same), MERGE_COST)
    for g in same[:MERGE_COST]:
        gems.remove(g)
    gems.append({"key": key, "lv": lv + 1})
    player["gems"] = gems
    return True, "合成 %s" % label({"key": key, "lv": lv + 1})


def bonus(equipment):
    """面板加成（只平铺）：{atk, hp, def, crit}；未镶宝石时全 0（零影响红线）。"""
    out = {"atk": 0.0, "hp": 0.0, "def": 0.0, "crit": 0.0}
    for it in (equipment or {}).values():
        if not it:
            continue
        for g in slots_of(it):
            row = load().get((g or {}).get("key"))
            if row:
                out[row["stat"]] += row["per"] * int(g.get("lv", 1))
    return out
