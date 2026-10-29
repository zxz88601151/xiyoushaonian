# V2.8 出口验收 · 自动化冒烟（DESIGN_V2_8 §8 六门禁）
# 成就 / 图鉴 / 统计 / tribe 实怪 / schema 8 迁移 / 回归。
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # miniasura/
sys.path.insert(0, HERE)
os.chdir(HERE)
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

# 开场清场：上次运行（含中途崩溃）残留的账号/会话/存档一律清掉，保证可重复执行
import shutil as _sh0
for _f in ("save.json", "session.json", "accounts.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh0.rmtree("saves", ignore_errors=True)

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name)


import engine
import gear
import progress
import save
import skills
import tower

CFG = tower.load_cfg()
T = skills.load_skills()
WEAPONS = list(gear.WEAPON_NAMES)


def norm(**kw):
    base = {"level": 1, "kills": {}, "maps_cleared": 0, "week": 0, "tower_best": 0,
            "codex_weapons": [], "inventory": [], "storage": [], "equipment": {}}
    base.update(kw)
    return base


# ── 门禁1 成就：6 项条件各有断言 + 并集不回归 ──
check("成就表 6 项、条件类型合法（V28-01 口径）",
      len(progress.load_achievements()) == 6
      and {a["kind"] for a in progress.load_achievements()} <= set(progress.COND_KINDS))
check("first_blood：总击杀 ≥1（0 不解锁）",
      "first_blood" in progress.evaluate(norm(kills={"xiaoyao1": 1}))
      and "first_blood" not in progress.evaluate(norm()))
check("clear_all：maps≥10 或 week≥1 兜底（周目重开 maps 归零仍解锁）",
      "clear_all" in progress.evaluate(norm(maps_cleared=10))
      and "clear_all" in progress.evaluate(norm(maps_cleared=0, week=1))
      and "clear_all" not in progress.evaluate(norm(maps_cleared=9)))
check("max_level：Lv.30 解锁（29 不解锁）",
      "max_level" in progress.evaluate(norm(level=30))
      and "max_level" not in progress.evaluate(norm(level=29)))
check("full_arsenal：武器谱 10 把集齐",
      "full_arsenal" in progress.evaluate(norm(codex_weapons=WEAPONS))
      and "full_arsenal" not in progress.evaluate(norm(codex_weapons=WEAPONS[:9])))
check("tower30：爬塔最高 ≥30 层",
      "tower30" in progress.evaluate(norm(tower_best=30))
      and "tower30" not in progress.evaluate(norm(tower_best=29)))
enh10 = {"slot": 0, "lv": 30, "quality": 2, "enh": 10, "name": "白骨剑",
         "main": {"atk": 1, "hp": 0, "def": 0, "dodge": 0}, "affixes": []}
check("enhance10：任一装备 enh≥10（+9 不解锁）",
      "enhance10" in progress.evaluate(norm(equipment={"weapon": enh10}))
      and "enhance10" not in progress.evaluate(norm(equipment={"weapon": dict(enh10, enh=9)})))

# 并集不回归：+10 装备放进背包 → save.write；再把装备清空（模拟回收）→ 成就仍在
save.set_path(os.path.join(HERE, "save.json"))
player = {"level": 30, "exp": 0, "hp": 100, "mp": 100, "attack": 1, "gold": 0,
          "inventory": [enh10], "equipment": gear.empty_equipment(),
          "potions": {"hp": 0, "mp": 0}, "tower_best": 0, "tower_layer": 0}
save.write(player, 0, 1, 3661)
d = json.load(open("save.json", encoding="utf-8"))
first = set(d["achievements"])
player["inventory"] = []                      # 模拟 +10 装备被回收
save.write(player, 0, 1, 3661)
d = json.load(open("save.json", encoding="utf-8"))
check("并集不回归：回收 +10 装备后 enhance10 仍在", "enhance10" in first
      and "enhance10" in d["achievements"])
check("成就解锁同时按现状算（Lv.30/maps 兜底 week1 → max_level+clear_all）",
      "max_level" in first and "clear_all" in first)
os.remove("save.json")

# ── 门禁2 图鉴：卖出过仍亮灯；怪物击杀数与 kills 一致、lose: 不计 ──
codex = progress.merge_codex(["定水枪"], {"inventory": []}, [])
check("codex 并集：卖出过的定水枪仍在图鉴（背包已空）", codex == ["定水枪"])
codex2 = progress.merge_codex(["定水枪"], {"equipment": gear.empty_equipment()},
                              [{"name": "白骨剑", "slot": 0, "lv": 1, "quality": 2,
                                "enh": 0, "main": {}, "affixes": []}])
check("codex 并集：旧档 ∪ 仓库新武器（定水枪 + 白骨剑）",
      codex2 == ["定水枪", "白骨剑"] or codex2 == ["白骨剑", "定水枪"])
mons = engine.parse_kv(engine.load_texts()["monsters.txt"])
rows = progress.monster_codex({"kills": {"boss": 3, "lose:boss": 5, "huoyao": 2}},
                              [(k, v[0]) for k, v in mons.items()])
by_key = {k: (n, seen) for k, _name, n, seen in rows}
check("怪物图鉴：7 行齐全（含 3 新怪）", len(rows) == 7)
check("怪物图鉴击杀数与 kills 一致、lose: 不计",
      by_key["boss"][0] == 3 and by_key["huoyao"][0] == 2 and by_key["xiaoyao1"] == (0, False))
check("怪物图鉴 tribe 列可读（虾兵/蟹将=水族、火妖=火抗）",
      mons["xiabing"][2] == "水族" and mons["xiejian"][2] == "水族" and mons["huoyao"][2] == "火抗")

# ── 门禁3 统计口径：总击杀 / 总伤害 / 时长格式化 ──
s = progress.stats({"kills": {"xiaoyao1": 4, "lose:boss": 9}, "total_damage": 12345,
                    "playtime": 3661, "week": 2, "tower_best": 12, "level": 25, "gold": 798})
check("统计：3661 秒 → 1小时1分；总击杀排除 lose:；总伤害/周目/爬塔/等级/金币",
      s["playtime"] == "1小时1分" and s["kills"] == 4 and s["damage"] == 12345
      and (s["week"], s["tower_best"], s["level"], s["gold"]) == (2, 12, 25, 798))
check("统计：不足 1 小时显示 X分钟（1800 秒 → 30分钟）",
      progress.stats({"playtime": 1800})["playtime"] == "30分钟")

# ── 门禁4 tribe 实怪：图4 出虾兵/蟹将、图7 出火妖；特效有实怪可打 ──
maps = engine.build_maps(engine.load_texts()["maps.txt"], CFG, mons)
m4 = [f["mon"] for m in maps if m["no"] == 4 for f in m["fights"]]
m7 = [f["mon"] for m in maps if m["no"] == 7 for f in m["fights"]]
check("图4 东海龙宫：虾兵 + 蟹将（tribe 水族、倍率后 72/14 与 91/18）",
      [x["name"] for x in m4] == ["虾兵", "蟹将"]
      and (m4[0]["hp"], m4[0]["atk"]) == (72, 14) and (m4[1]["hp"], m4[1]["atk"]) == (91, 18))
check("图7 八卦炉：火妖 ×2（tribe 火抗、倍率后 112/22）",
      [x["name"] for x in m7] == ["火妖", "火妖"] and (m7[0]["hp"], m7[0]["atk"]) == (112, 22))


def wield(name, kind, param):
    return {"slot": 0, "lv": 30, "quality": 2, "enh": 0, "name": name,
            "effect": {"kind": kind, "param": param},
            "main": {"atk": 100, "hp": 0, "def": 0, "dodge": 0}, "affixes": []}


p = {"equipment": dict(gear.empty_equipment())}
p["equipment"]["weapon"] = wield("定水枪", "vs_tribe:水族", "1.15")
check("定水枪 ×1.15 打虾兵（实怪 tribe 命中）", skills.weapon_effect(p, m4[0]) == 1.15)
p["equipment"]["weapon"] = wield("芭蕉扇", "vs_tribe:火抗", "1.18")
check("芭蕉扇 ×1.18 打火妖（实怪 tribe 命中）", skills.weapon_effect(p, m7[0]) == 1.18)
p["equipment"]["weapon"] = wield("降魔杖", "vs_tribe:妖", "1.12")
boss = [f["mon"] for m in maps if m["no"] == 10 for f in m["fights"]][0]
check("降魔杖 ×1.12 打 boss（妖）", skills.weapon_effect(p, boss) == 1.12)

# ── 门禁5 迁移：v7 旧档 → schema 8，旧值一字不动、新字段齐全 ──
v7 = {"schema": 7, "user": "", "level": 22, "exp": 99, "hp": 200, "mp": 80, "attack": 90,
      "next": 5, "week": 1, "playtime": 3600, "gold": 456, "difficulty": 1, "protect": 3,
      "inventory": [], "equipment": gear.empty_equipment(), "quest_flags": {"m1": "done"},
      "kills": {"boss": 2}, "maps_cleared": 4, "potions": {"hp": 1, "mp": 2},
      "storage": [], "tower_best": 17, "tower_layer": 0}
save.write_raw(v7)
d = save.load()
check("v7→v8：等级/金币/击杀/爬塔/周目一字不动",
      (d["level"], d["gold"], d["kills"]["boss"], d["tower_best"], d["week"]) == (22, 456, 2, 17, 1))
check("v7→v8：新字段默认值齐全（achievements/codex_weapons/total_damage = []/[]/0）",
      d["schema"] == save.SCHEMA and d["achievements"] == []
      and d["codex_weapons"] == [] and d["total_damage"] == 0)
os.remove("save.json")

# ── 门禁6 回归：smoke_v27 + validate 十五项 + 行数纪律 + CLI 全通基线 ──
limits = {"engine.py": 220, "combat.py": 130, "tower.py": 100,
          "validate.py": 160, "progress.py": 150}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items()
             if sum(1 for _ in open(f, encoding="utf-8")) > lim]
check("行数纪律（engine≤220、combat≤130、tower≤100、validate≤160、progress≤150）",
      not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)
r = subprocess.run([WB, "validate.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("validate 十五项全绿（V2.9-A 起含 V29-01/02/03）（9 + V28-01/02/03）", r.returncode == 0 and r.stdout.count("✓") == 15)
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("CLI 全通基线不变（Lv.25 / 金币 798 / 图鉴与统计落盘）",
      after["maps_cleared"] == 10 and after["level"] == 25 and after["gold"] == 798
      and after["total_damage"] > 0 and len(after["codex_weapons"]) > 0)
os.remove("save.json")
# 字体引导（V2.8）：offscreen 下 Qt 字体库为空（实测 0 族）→ 中文全方框；
# 门禁自证能加载系统中文 TTF，保证任何截图取证可读
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
import qtfont
qapp = QApplication.instance() or QApplication([])
check("字体引导：offscreen 下可加载系统中文字体（截图/测试可读）",
      qtfont.ensure_cjk_font(qapp) != "")
r = subprocess.run([WB, "tests/smoke_v27.py"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("smoke_v27 回归", "全部通过" in r.stdout)
if "失败" in r.stdout:
    print(r.stdout[-800:])

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
import shutil as _sh
for _f in ("accounts.json", "session.json", "save.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh.rmtree("saves", ignore_errors=True)
print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
