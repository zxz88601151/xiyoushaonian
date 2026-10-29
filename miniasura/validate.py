# V2.5 数据校验器 —— 把数据表当源码编译（蓝图 §7.3）：数据错了直接红，纳入门禁。
# 七项检查（DESIGN_V2_5.md §4）：掉落来源 / 任务奖励 / 经验曲线 / 商店 / 词条限制 / 迁移 / 金币对账。
import configparser
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

import combat
import enhance
import gear
import loot
import quests
import save


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
            if slot != "staff" and slot not in gear.SLOTS:
                bad.append("[loot.%s] 部位 %s" % (mon, slot))
            if not 0 <= quality <= 2 or not 1 <= chance <= 100:
                bad.append("[loot.%s] 品质%s/概率%s" % (mon, quality, chance))
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
    needs = [combat.lua("expneed", i, base, pow100)["need"]
             for i in range(1, g.getint("level_cap"))]
    ok = all(b > a for a, b in zip(needs, needs[1:])) and needs[0] > 0
    return ok, [] if ok else ["非单调：%s" % needs[:5]]


def check_shop():
    """4 商店每件物品可购买：价格 > 0。"""
    bad = []
    for line in pack_text("shop.txt").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, name, price = line.split("|")
        if int(price) <= 0:
            bad.append("%s 价格 %s" % (key, price))
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
    need = ("schema", "week", "gold", "difficulty", "protect", "tower_best",
            "tower_layer", "inventory", "equipment", "quest_flags", "storage")
    miss = [k for k in need if k not in d]
    return not miss and d["schema"] == save.SCHEMA and d["week"] == 1, miss


def check_gold_flow(cfg):
    """7 金币收支对账：产出（怪物金币）与去处（商店/回收/保底符）都得有条目。"""
    bad = [s for s in cfg.sections()
           if s.startswith("monster.") and cfg.getint(s, "gold", fallback=0) <= 0]
    if not cfg.has_section("shop"):
        bad.append("[shop] 缺失")
    if enhance.PROTECT_PRICE <= 0:
        bad.append("保底符价格缺失")
    return not bad, bad


def main():
    cfg = load_cfg()
    rows = [("1 掉落表部位/品质/概率合法", check_loot(cfg)),
            ("2 任务奖励物品存在", check_quest_rewards()),
            ("3 经验曲线单调递增", check_exp_curve(cfg)),
            ("4 商店每件物品可购买", check_shop()),
            ("5 词条部位与品质限制", check_affixes()),
            ("6 存档 v1→v%d 迁移" % save.SCHEMA, check_migrate()),
            ("7 金币收支对账", check_gold_flow(cfg))]
    bad = 0
    for name, (ok, detail) in rows:
        print(("✓" if ok else "✗"), name, ("" if ok else "  → %s" % detail))
        bad += 0 if ok else 1
    print("\n=== 汇总 ===")
    print("validate 全绿 ✅" if not bad else "validate 失败 %d 项 ❌" % bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
