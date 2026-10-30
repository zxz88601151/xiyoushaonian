# MiniAsura V2.1 装备数据层 —— 词条池读 mpak，公式调 scripts/equip.lua（细案 §1 契约）
# 本文件只做"挑选 + 装配 + 加法簿记"，任何成长/区间/品质公式都不在这里
import configparser
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack
import gem    # V3.0-A：宝石（gem 只依赖 mypack，无循环导入）
import sets   # V3.0-A：套装（同上）

LUA = os.path.join(HERE, "..", "tools", "lua-5.1.5", "lua.exe")
EQUIP_LUA = os.path.join(HERE, "scripts", "equip.lua")

SLOTS = ["weapon", "helm", "armor", "belt", "boots"]
SLOT_NAMES = {"weapon": "武器", "helm": "头盔", "armor": "护甲",
              "belt": "腰带", "boots": "靴子"}
QUALITY_NAMES = ["白", "蓝", "紫"]
AFFIX_COUNT = (0, 1, 2)          # 白/蓝/紫词条数（蓝本 §2.1）
# V2.7 武器谱（蓝图 §2.4 十把；紫档武器生成时取名并挂特效，桃木棍无特效）
WEAPON_NAMES = ["桃木棍", "定水枪", "齐眉棍", "降魔杖", "白骨剑",
                "缠丝爪", "芭蕉扇", "混妖斧", "乾坤圈", "弥陀弓"]


def load_weapon_effects():
    """weapon_effects.txt（武器|effect|参数）→ {武器名: (effect, 参数)}，数据外置。"""
    text = mypack.read(os.path.join(HERE, "assets.mpak"), "weapon_effects.txt").decode("utf-8")
    table = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, effect, param = line.split("|")
        table[name] = (effect, param)
    return table


def capacity():
    # 背包容量是策划数值（终审 F3）——住 game.ini，仓库扩容（金币去处）迟早要调它
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    return cfg.getint("bag", "capacity", fallback=20)


def lua(*args):
    out = subprocess.run([LUA, EQUIP_LUA] + [str(a) for a in args],
                         capture_output=True, text=True, encoding="utf-8").stdout
    line = next(l for l in out.splitlines() if "{" in l).strip()
    return json.loads(line)


def load_affixes():
    pack = os.path.join(HERE, "assets.mpak")
    text = mypack.read(pack, "affixes.txt").decode("utf-8")
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        key, name, kind, lo, hi, slots, ponly = line.split("|")
        rows.append({"key": key, "name": name, "kind": kind,
                     "lo": float(lo), "hi": float(hi),
                     "slots": list(SLOTS) if slots == "any" else slots.split(","),
                     "ponly": ponly == "1"})
    return rows


def _pick(rows, slot, quality, used, rng):
    cand = [a for a in rows
            if slot in a["slots"]
            and not (a["ponly"] and quality != 2)
            and a["key"] not in used]
    if not cand:   # fail-closed（终审 F2）：宁可明确报错，不裸抛 IndexError
        raise ValueError(f"{SLOT_NAMES[slot]} 的词条池已耗尽"
                         f"（品质 {quality}，已占用 {sorted(used)}）——检查 affixes.txt 部位限制")
    return rng.choice(cand)


def generate(slot, lv, quality, rows=None, rng=random):
    """生成一件装备；rng 可注入（测试用固定种子）。数值全部出自 equip.lua。"""
    rows = rows if rows is not None else load_affixes()
    q = int(quality)
    if slot not in SLOTS:
        raise ValueError(f"未知部位: {slot}（合法值 {SLOTS}）")
    if not 0 <= q <= 2:
        raise ValueError(f"品质必须是 0/1/2（白/蓝/紫），收到 {quality}")
    si = SLOTS.index(slot)
    main = lua("main", si, lv, q)
    item = {"slot": si, "lv": int(lv), "quality": q, "enh": 0,
            "main": {k: main[k] for k in ("atk", "hp", "def", "dodge")},
            "affixes": []}
    used = set()
    for i in range(AFFIX_COUNT[q]):
        a = _pick(rows, slot, q, used, rng)
        used.add(a["key"])
        # 紫装第 2 条词条保底 ≥ 区间中位（蓝本 §2.3）
        mid = 1 if (q == 2 and i == 1) else 0
        kind = 0 if a["kind"] == "flat" else 1
        r = rng.randint(0, 10000)                # 掷骰归引擎侧，公式归 Lua
        v = lua("affix", kind, lv, r, a["lo"], a["hi"], mid)["val"]
        item["affixes"].append({"key": a["key"], "name": a["name"], "val": v})
    if q == 2 and slot == "weapon":              # V2.7 紫档武器：武器谱取名 + 特效（蓝/白档为空）
        item["name"] = rng.choice(WEAPON_NAMES)
        eff = load_weapon_effects().get(item["name"])
        if eff:
            item["effect"] = {"kind": eff[0], "param": eff[1]}
    if q == 2:                                   # V3.0-A：紫装按稳定种子判套装件（不吃随机流，G8）
        key = sets.roll_set(item)
        if key:
            item["set"] = key
    return item


STAFF_NAME = "如意金箍棒·无级"
STAFF_ATK_BASE, STAFF_ATK_PER_LEVEL = 10, 6   # 蓝图 §2.4：ATK = 10 + 持有者等级 × 6


def make_staff():
    """无级别武器（蓝图 §2.4）：攻击随持有者等级重算，词条固定三条满值，不掷骰。"""
    return {"slot": 0, "lv": 0, "quality": 2, "enh": 0, "scaling": "owner",
            "main": {"atk": 0, "hp": 0, "def": 0, "dodge": 0},
            "affixes": [{"key": "leech", "name": "吸血%", "val": 5.0},
                        {"key": "critdmg", "name": "暴伤%", "val": 25.0},
                        {"key": "crit", "name": "暴击率%", "val": 5.0}]}


def has_staff(player, storage=None):
    """是否已持有无级武器（背包 + 仓库 + 已穿戴全查）——发放口的幂等闸。"""
    items = list(player.get("inventory", [])) + list(storage or []) + [
        it for it in (player.get("equipment") or {}).values() if it]
    return any(it.get("scaling") == "owner" for it in items)


def grant_staff(player, storage, io):
    """唯一发放口（隐藏任务 h2 与 boss 掉率共用）——已持有则不再发，防刷出一背包棒子。"""
    if has_staff(player, storage):
        io.say(f"  （{STAFF_NAME} 已在手，不再重复发放）")
        return None
    it = make_staff()
    bag = player.setdefault("inventory", [])
    if len(bag) < capacity():
        bag.append(it)
        io.say(f"  🗡 获得 {item_line(it)}（已进背包）")
    else:
        storage.append(it)
        io.say(f"  🗡 获得 {item_line(it)}（背包已满，转入仓库）")
    return it


def item_name(item):
    if item.get("scaling") == "owner":
        return STAFF_NAME + (f" +{item['enh']}" if item.get("enh") else "")
    if item.get("name"):                          # V2.7 武器谱紫武有专名（旧档无 name 走原格式）
        name = f"{QUALITY_NAMES[item['quality']]}·{item['name']} Lv{item['lv']}"
    else:
        name = f"{QUALITY_NAMES[item['quality']]}·{SLOT_NAMES[SLOTS[item['slot']]]} Lv{item['lv']}"
    if item.get("enh", 0):
        name += f" +{item['enh']}"
    return name


def item_line(item):
    """一行人话描述（背包列表/详情用）。"""
    parts = [item_name(item)]
    if item.get("scaling") == "owner":
        parts.append(f"攻击+随等级（{STAFF_ATK_BASE} + 等级×{STAFF_ATK_PER_LEVEL}）")
    if item["main"]["atk"]:
        parts.append(f"攻击+{item['main']['atk']}")
    if item["main"]["hp"]:
        parts.append(f"HP+{item['main']['hp']}")
    if item["main"]["def"]:
        parts.append(f"防御+{item['main']['def']:.1f}")
    if item["main"]["dodge"]:
        parts.append(f"闪避+{item['main']['dodge']:.1f}%")
    for a in item["affixes"]:
        parts.append(f"{a['name']}+{a['val']:.1f}")
    return "  ".join(parts)


def totals(equipment, owner_level=1, extra=None):
    """聚合穿戴加成（细案 §1 簿记约定：百分比词条以 主属性+平铺 为基数）。
    owner_level：无级别武器（scaling:"owner"）按持有者等级算攻击——本期架构上唯一的有意破例。
    extra：V3.0-A 属性点加成（player 派生，不是装备派生，故由调用方传入）。"""
    base = {"atk": 0.0, "hp": 0.0, "def": 0.0, "dodge": 0.0}
    pct = {"atk": 0.0, "hp": 0.0}
    add = {"crit": 0.0, "critdmg": 0.0, "leech": 0.0, "exp": 0.0}
    mult_pct, hit = {"atk": 1.0, "hp": 1.0, "def": 1.0}, 0.0   # V2.7 武器谱特效汇总（乘区/命中）
    for it in equipment.values():
        if not it:
            continue
        # V2.4 强化：主属性 atk/hp/def × (1 + 0.05 × enh)，闪避与词条不乘。
        mult = 1 + 0.05 * it.get("enh", 0)
        if it.get("scaling") == "owner":   # 无级别武器：攻击 = (10 + 等级×6) × 强化倍率
            base["atk"] += (STAFF_ATK_BASE + STAFF_ATK_PER_LEVEL * owner_level) * mult
        else:
            for k, v in it["main"].items():
                base[k] += v * mult if k != "dodge" else v
        for a in it["affixes"]:
            if a["key"] in ("atkflat", "defflat"):
                base["atk" if a["key"] == "atkflat" else "def"] += a["val"]
            elif a["key"] == "atkp":
                pct["atk"] += a["val"]
            elif a["key"] == "hpp":
                pct["hp"] += a["val"]
            elif a["key"] in add:
                add[a["key"]] += a["val"]
            else:
                raise ValueError(f"未知词条 key: {a['key']}"
                                 f"（affixes.txt 与 totals 白名单不对齐）")
        eff = it.get("effect") or {}          # V2.7 武器谱特效：vs_tribe 由 combat 按 tribe 匹配
        kind, param = eff.get("kind", ""), float(eff.get("param", 0) or 0)
        if kind.startswith("vs_tribe:"):
            pass                              # 战斗内倍率，不进面板汇总
        elif kind in ("atk_pct", "hp_pct", "def_pct"):
            mult_pct[kind.split("_")[0]] *= 1 + param
        elif kind == "hit":
            hit += param
        elif kind in ("leech", "critdmg"):
            add[kind] += param * 100
        elif kind:
            raise ValueError(f"未知武器特效 kind: {kind}（weapon_effects.txt 白名单不对齐）")
    # V3.0-A：宝石 / 套装 / 属性点三源平铺进基数——都在百分比放大之前，与词条口径一致（三层可分别断言）
    gb, sb, ex = gem.bonus(equipment), sets.bonus(equipment), (extra or {})
    for k in ("atk", "hp", "def"):
        base[k] += gb.get(k, 0.0) + sb.get(k, 0.0) + ex.get(k, 0.0)
    add["crit"] += gb.get("crit", 0.0) + sb.get("crit", 0.0) + ex.get("crit", 0.0)
    add["critdmg"] += sb.get("critdmg", 0.0)
    add["leech"] += sb.get("leech", 0.0)
    pct["atk"] += sb.get("atkp", 0.0)
    pct["hp"] += sb.get("hpp", 0.0)
    for k in ("atk", "hp"):
        base[k] *= 1 + pct[k] / 100
    for k in mult_pct:                        # 武器谱百分比特效乘区（在词条%之后）
        base[k] *= mult_pct[k]
    add["leech"] = min(10.0, add["leech"])    # D3：吸血叠加上限 10%（词条+缠丝爪收口处）
    return {**base, **add, "hit": hit}


def empty_equipment():
    return {s: None for s in SLOTS}
