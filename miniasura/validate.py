# V2.5/V2.7 数据校验器 —— 把数据表当源码编译（蓝图 §7.3）：数据错了直接红，纳入门禁（九项）。
import configparser
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

import combat, enhance, gear, loot, quests, save   # 校验器只读数据层，不碰引擎/GUI


def load_cfg():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    return cfg


def pack_text(name):
    return mypack.read(os.path.join(HERE, "assets.mpak"), name).decode("utf-8")


def check_loot(cfg):
    """1 掉落表：部位合法（staff 或五大部位），品质 0-2，概率 1-100。"""
    bad = []
    for mon, rows in loot.load_table(cfg).items():
        for slot, quality, chance in rows:
            if (slot != "staff" and slot not in gear.SLOTS) \
                    or not 0 <= quality <= 2 or not 1 <= chance <= 100:
                bad.append("[loot.%s] %s/%s/%s" % (mon, slot, quality, chance))
    return not bad, bad


def check_quest_rewards():
    """2 任务奖励里的物品确实存在：gear:部位:等级:品质 合法，staff 免检。"""
    bad = []
    for q in quests.load(quests.load_pack_text()):
        for kind, args in quests.parse_rewards(q["reward"]):
            if kind in ("staff", "exp", "potion_hp", "potion_mp"):
                continue
            if kind != "gear" or len(args) != 3:
                bad.append("%s 奖励种类 %s" % (q["key"], kind))
                continue
            slot, lv, qual = args
            if slot not in gear.SLOTS or int(lv) <= 0 or not 0 <= int(qual) <= 2:
                bad.append("%s gear:%s" % (q["key"], ":".join(args)))
    return not bad, bad


def check_exp_curve(cfg):
    """3 经验曲线严格单调递增（调 battle.lua expneed，公式不在 Python 里重写一遍）。"""
    g = cfg["growth"]
    base, pow100 = g.getint("exp_base"), g.getint("exp_pow_x100")
    needs = [combat.lua("expneed", i, base, pow100)["need"] for i in range(1, g.getint("level_cap"))]
    ok = all(b > a for a, b in zip(needs, needs[1:])) and needs[0] > 0
    return ok, [] if ok else ["非单调：%s" % needs[:5]]


def data_rows(name):
    """数据表逐行（跳过空行与注释）——多处校验共用的唯一读法。"""
    return [l for l in pack_text(name).splitlines() if l.strip() and not l.startswith("#")]


def check_shop():
    """4 商店每件物品可购买：价格 > 0。"""
    bad = [l.split("|")[0] for l in data_rows("shop.txt") if int(l.split("|")[2]) <= 0]
    return not bad, bad


def check_affixes():
    """5 词条不违反部位与品质限制：紫装专属（ponly）只能是武器位。"""
    bad = [a["key"] for a in gear.load_affixes()
           if a["ponly"] and a["slots"] != ["weapon"]]
    return not bad, bad


def check_migrate():
    """6 存档 schema 可迁移：v1 档 → 当前 schema，关键字段一个都不丢。"""
    d = save._migrate({"cleared": True, "level": 14, "exp": 0, "hp": 150,
                       "mp": 100, "attack": 57, "next": 0})
    need = ("schema", "week", "gold", "difficulty", "protect", "tower_best", "tower_layer", "inventory",
            "equipment", "quest_flags", "storage", "achievements", "codex_weapons", "total_damage")
    miss = [k for k in need if k not in d]
    return not miss and d["schema"] == save.SCHEMA and d["week"] == 1, miss


def check_gold_flow(cfg):
    """7 金币收支对账：产出（怪物金币）与去处（商店/回收/保底符）都得有条目。"""
    bad = [s for s in cfg.sections()
           if s.startswith("monster.") and cfg.getint(s, "gold", fallback=0) <= 0]
    if not cfg.has_section("shop") or enhance.PROTECT_PRICE <= 0:
        bad.append("[shop] 缺失" if not cfg.has_section("shop") else "保底符价格缺失")
    return not bad, bad


def check_skills(cfg):
    # V27-01 skills.txt 每行 id 必有 [skill.*]+unlock_lv；主动必有 power，被动不得有 power
    bad = []
    for line in data_rows("skills.txt"):
        sid = line.split("|")[0]
        sec = "skill." + sid
        if not cfg.has_section(sec) or "unlock_lv" not in cfg[sec]:
            bad.append(f"{sid} 缺 [{sec}] 或 unlock_lv")
            continue
        kind = cfg.get(sec, "kind", fallback="active")
        if kind == "active" and not cfg.has_option(sec, "power"):
            bad.append(f"{sid} 主动缺 power")
        if kind == "passive" and cfg.has_option(sec, "power"):
            bad.append(f"{sid} 被动不得有 power")
    return not bad, bad


def check_weapon_tribes():
    # V27-02 vs_tribe:X 的 X 必属 D2 合法 tribe 集合（防拼写；V2.8 水族/火抗实怪已补）
    tribes = {"无", "妖", "水族", "火抗"}   # D2 全集
    bad = [l.split("|")[1] for l in data_rows("weapon_effects.txt")
           if l.split("|")[1].startswith("vs_tribe:")
           and l.split("|")[1].split(":", 1)[1] not in tribes]
    return not bad, bad


def check_v28(cfg):
    """V28-01 成就条件合法 / V28-02 新怪三件套 / V28-03 地图 key 存在 + 武器谱口径一致。"""
    ach, keys = data_rows("achievements.txt"), {l.split("|")[0] for l in data_rows("monsters.txt")}
    legal = {"kills", "maps", "level", "arsenal", "tower", "enhance"}
    bad1 = [l for l in ach if len(l.split("|")) != 5 or l.split("|")[3] not in legal
            or int(l.split("|")[4]) <= 0]
    bad2 = [k for k in ("xiabing", "xiejian", "huoyao") if not cfg.has_section("monster." + k)
            or not cfg.has_section("loot." + k) or k not in keys]
    bad3 = [l for l in data_rows("maps.txt")
            if any(k != "-" and k not in keys for k in l.split("|")[2].split(","))]
    th = [int(l.split("|")[4]) for l in ach if l.split("|")[3] == "arsenal"]
    if len(gear.WEAPON_NAMES) != 10 or th[:1] != [10]:
        bad3.append("武器谱 %d / 阈值 %s" % (len(gear.WEAPON_NAMES), th))
    return [("10 成就条件合法（V28-01）", (not bad1, bad1)),
            ("11 新怪三件套齐全（V28-02）", (not bad2, bad2)),
            ("12 地图 key 与武器谱口径（V28-03）", (not bad3, bad3))]


def main():
    cfg = load_cfg()
    rows = [("1 掉落表部位/品质/概率合法", check_loot(cfg)),
            ("2 任务奖励物品存在", check_quest_rewards()),
            ("3 经验曲线单调递增", check_exp_curve(cfg)),
            ("4 商店每件物品可购买", check_shop()),
            ("5 词条部位与品质限制", check_affixes()),
            ("6 存档 v1→v%d 迁移" % save.SCHEMA, check_migrate()),
            ("7 金币收支对账", check_gold_flow(cfg)),
            ("8 技能必有解锁等级（V27-01）", check_skills(cfg)),
            ("9 特效 tribe 合法（V27-02）", check_weapon_tribes())] + check_v28(cfg)
    bad = sum(0 if ok else 1 for _, (ok, _) in rows)
    for name, (ok, detail) in rows:
        print(("✓" if ok else "✗"), name, ("" if ok else "  → %s" % detail))
    print("\n=== 汇总 ===")
    print("validate 全绿 ✅" if not bad else "validate 失败 %d 项 ❌" % bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
