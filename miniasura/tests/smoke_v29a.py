# V2.9-A 出口验收 · 自动化冒烟（DESIGN_V2_9_A §5 六门禁）
# 战报 / BOSS 变招 / 精英稀有 / 保底迁移 / validate 十七项 / 回归。
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # miniasura/
sys.path.insert(0, HERE)
os.chdir(HERE)
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

import shutil as _sh0
for _f in ("save.json", "session.json", "accounts.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh0.rmtree("saves", ignore_errors=True)

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name)


import combat
import encounter
import engine
import gear
import loot
import save
import tower

CFG = tower.load_cfg()
SKILLS = __import__("skills").load_skills()


class Io:
    def __init__(self):
        self.said = []

    def say(self, m=""):
        self.said.append(m)

    def ask(self, p):
        return "1"


def base_player(attack=200, hp=1000):
    return {"level": 25, "exp": 0, "hp": hp, "mp": 100, "max_hp": hp, "attack": attack,
            "def": 10.0, "dodge": 0, "hit": 0, "mitigate": 1.0, "crit_rate": 0,
            "critdmg": 0.0, "leech": 0.0, "exp_bonus": 0.0, "gold": 0, "protect": 0,
            "inventory": [], "equipment": gear.empty_equipment(),
            "potions": {"hp": 0, "mp": 0}, "total_damage": 0, "staff_pity": 0}


# ── 门禁1 战报：一击必杀 → rounds=1、dealt>0、taken=0 ──
rep = {}
res = combat.battle(CFG, SKILLS, {"key": "xiaoyao1", "name": "小妖甲", "intro": "！",
                                  "tribe": "无", "hp": 1, "atk": 1, "exp": 10, "gold": 0},
                    base_player(), Io(), rep)
check("战报：一击必杀 win 且 rounds=1、dealt>0、taken=0、misses=0",
      res == "win" and rep.get("rounds") == 1 and rep.get("dealt", 0) > 0
      and rep.get("taken") == 0 and rep.get("misses") == 0)
io2 = Io()
encounter.print_report(io2, rep)
check("战报打印一行含“战报：”", any("战报：" in s for s in io2.said))

# ── 门禁2 BOSS 变招：hp=200 boss，普攻打到 50/30 阈值 ──
boss = {"key": "boss", "name": "白骨夫人", "intro": "！", "tribe": "妖",
        "hp": 200, "atk": 10, "exp": 10, "gold": 0}  # 200 血才能走满变身→狂暴→骨刺雨（100 血 4 击即死，骨刺雨来不及触发）
io3 = Io()
rep2 = {}
res2 = combat.battle(CFG, SKILLS, boss, base_player(attack=30, hp=1000), io3, rep2)
txt = "\n".join(io3.said)
check("BOSS 变招：变身与狂暴各触发一次（消息各出现 1 次）",
      res2 == "win" and txt.count("现出白骨真身") == 1 and txt.count("狂暴了") == 1)
check("BOSS 变招：atk 累计 ×1.44（10 → 14，取整）且骨刺雨至少触发一次",
      boss["atk"] == 14 and any("骨刺雨" in s for s in io3.said))
check("BOSS 变招：骨刺雨伤害计入 taken", rep2.get("taken", 0) > 0)

# ── 门禁3 精英/稀有：确定性 + 数值 + boss 不变 ──
def mkfight(key="xiaoyao1"):
    return {"key": key, "mon": {"key": key, "name": "小妖甲", "intro": "！", "tribe": "无",
                                "hp": 40, "atk": 8, "exp": 800, "gold": 20}}

f1 = mkfight()
encounter.apply_encounter(f1, 0, 1, 0, CFG)
f2 = mkfight()
encounter.apply_encounter(f2, 0, 1, 0, CFG)
check("精英/稀有：同一 (week, 地图, fi) 两次判定结果相同",
      (f1["mon"]["name"], f1["mon"]["hp"], f1["mon"]["atk"]) ==
      (f2["mon"]["name"], f2["mon"]["hp"], f2["mon"]["atk"]))
kinds = {}
for fi in range(200):
    f = mkfight()
    encounter.apply_encounter(f, 0, 1, fi, CFG)
    if "elite" in f:
        kinds.setdefault("elite", []).append(f)
    elif "rare" in f:
        kinds.setdefault("rare", []).append(f)
check("精英/稀有：200 场里精英与稀有都出现（概率 20%/5% 非零）",
      kinds.get("elite") and kinds.get("rare"))
if kinds.get("elite"):
    e = kinds["elite"][0]
    check("精英：hp×1.5、atk×1.2（灼烧再×1.3）、名前缀精英·",
          e["mon"]["name"].startswith("精英·") and e["mon"]["hp"] == 60
          and e["mon"]["atk"] in (10, 12))
    check("精英词缀合法（armor/burn/swift 三选一）", e["elite"] in encounter.ELITE_AFFIXES)
if kinds.get("rare"):
    r0 = kinds["rare"][0]
    check("稀有：hp×0.5、atk×0.5、名前缀金色·",
          r0["mon"]["name"].startswith("金色·") and r0["mon"]["hp"] == 20 and r0["mon"]["atk"] == 4)
fb = {"key": "boss", "mon": {"key": "boss", "name": "白骨夫人", "intro": "！", "tribe": "妖",
                         "hp": 600, "atk": 40, "exp": 10, "gold": 0}}
encounter.apply_encounter(fb, 0, 10, 11, CFG)
check("boss 不变精英/稀有", "elite" not in fb and "rare" not in fb and fb["mon"]["name"] == "白骨夫人")

# ── 门禁4 保底 + 迁移 ──
class SeqRng:
    def __init__(self, v):
        self.v = v

    def randint(self, a, b):
        return self.v.pop(0) if self.v else 100


class FakeGear:
    pass


orig_generate = gear.generate
gear.generate = lambda slot, lv, quality, rows=None, rng=None: {
    "slot": gear.SLOTS.index(slot), "lv": lv, "quality": quality, "enh": 0,
    "main": {"atk": 10, "hp": 0, "def": 0, "dodge": 0}, "affixes": []}
pl = base_player()
pl["staff_pity"] = 0
# 仓库必须跨轮共用：boss 池里 weapon:2:100 是必掉紫装，49 轮足以填满 20 格背包，
# 之后所有掉落（含第 50 次的 staff）都转仓；每次新传 [] 会把物品扔进看不见的临时列表，
# 导致 has_staff 查不到、pity 被误判。这里模拟引擎里那份持久的 storage。
store = []
# boss staff 连续掷失败 49 次：每次 roll 的第一掷（staff 1%）都用 100 失败，之后普通掉落也用 100 失败
for _ in range(49):
    loot.roll(CFG, "boss", pl, store, Io(), difficulty=0, rng=SeqRng([100, 100, 100]))
check("保底：49 次 boss 失败后 pity=49", pl["staff_pity"] == 49)
loot.roll(CFG, "boss", pl, store, Io(), difficulty=0, rng=SeqRng([100, 100, 100]))
check("保底：第 50 次 boss 必中 staff 且 pity 清零",
      pl["staff_pity"] == 0 and gear.has_staff(pl, store))
# 已持有 staff 时 pity 不变
before = pl["staff_pity"]
loot.roll(CFG, "boss", pl, store, Io(), difficulty=0, rng=SeqRng([100, 100, 100]))
check("保底：已持有 staff 时 pity 不变", pl["staff_pity"] == before)
gear.generate = orig_generate

save.set_path(os.path.join(HERE, "save.json"))
v8 = {"schema": 8, "user": "", "level": 22, "exp": 99, "hp": 200, "mp": 80, "attack": 90,
      "next": 5, "week": 1, "playtime": 3600, "gold": 456, "difficulty": 1, "protect": 3,
      "inventory": [], "equipment": gear.empty_equipment(), "quest_flags": {"m1": "done"},
      "kills": {"boss": 2}, "maps_cleared": 4, "potions": {"hp": 1, "mp": 2},
      "storage": [], "tower_best": 17, "tower_layer": 0, "achievements": [],
      "codex_weapons": [], "total_damage": 123}
save.write_raw(v8)
d = save.load()
check("v8→v10：旧值不动、staff_pity=0、schema=10、D1 四新字段就位",
      d["schema"] == save.SCHEMA and d["gold"] == 456 and d["staff_pity"] == 0
      and d["total_damage"] == 123 and d["elite_kills"] == 0 and d["title"] == ""
      and d["records"]["best_dealt"] == 0)
os.remove("save.json")

# ── 门禁5 validate 十七项 + 行数纪律 ──
limits = {"engine.py": 225, "combat.py": 130, "encounter.py": 170,
          "loot.py": 100, "validate.py": 170}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items()
             if sum(1 for _ in open(f, encoding="utf-8")) > lim]
check("行数纪律（engine≤225、combat≤130、encounter≤170、loot≤100、validate≤170）",
      not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)
r = subprocess.run([WB, "validate.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("validate 十七项全绿（12 + V29-01/02/03 + V30-01）", r.returncode == 0 and r.stdout.count("✓") == 17)

# ── 门禁6 回归：smoke_v28 + CLI 全通基线 ──
r = subprocess.run([WB, "tests/smoke_v28.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("smoke_v28 回归", "全部通过" in r.stdout)
if "失败" in r.stdout:
    print(r.stdout[-800:])
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("CLI 全通基线不变（Lv.25 / 金币 798 / maps 10 / 战报出现）",
      after["maps_cleared"] == 10 and after["level"] == 25 and after["gold"] == 798
      and "战报：" in r.stdout)
os.remove("save.json")

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
for _f in ("accounts.json", "session.json", "save.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh0.rmtree("saves", ignore_errors=True)
print("全部通过 ✅" if not bad else "失败: %s" % bad)
