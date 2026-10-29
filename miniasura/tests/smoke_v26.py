# V2.6 出口验收 · 自动化冒烟（DESIGN_V2_6.md §4 六门禁）
# Lv.1 开局 + 经验曲线恢复蓝图原值 60×lv^1.65 + 十图数值重钉。
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


import combat
import engine
import gear
import save
import tower

CFG = tower.load_cfg()


class SilentIo:
    def say(self, msg=""):
        pass

    def ask(self, prompt):
        return "1"


def new_player(level=1):
    p = {"level": level, "exp": 0, "mp": 100, "gold": 0,
         "inventory": [], "equipment": gear.empty_equipment(),
         "potions": {"hp": 0, "mp": 0}, "tower_best": 0, "tower_layer": 0}
    engine.apply_gear(CFG, p)
    p["hp"] = p["max_hp"]
    return p


io = SilentIo()
skills = engine.parse_kv(engine.load_texts()["skills.txt"])

# ── 门禁1 Lv.1 开局：新档 level=1，第一图教学战纯普攻可过 ──
check("game.ini 开局等级 = 1（蓝图 §1）", CFG.getint("player", "level") == 1)
p = new_player(1)
check("Lv.1 裸装面板：attack 18 / hp 150", p["attack"] == 18 and p["max_hp"] == 150)
maps = engine.build_maps(engine.load_texts()["maps.txt"], CFG,
                         engine.parse_kv(engine.load_texts()["monsters.txt"]))
mon1 = maps[0]["fights"][0]["mon"]
hp0 = p["hp"]
res = combat.battle(CFG, skills, mon1, p, io)
check("图1 教学战：纯普攻可过、掉血不过半",
      res == "win" and mon1["hp"] == 40 and p["hp"] >= hp0 * 0.8)

# ── 门禁2 经验曲线恢复蓝图原值：need = 60×lv^1.65，30 级封顶 ──
# 蓝图表 §1.1 中 30 级档（16715）与公式 floor(60×30^1.65)=16419 不一致（蓝图表手算误差）——
# 门禁以蓝图明确写出的公式 round(60×lv^1.65) 为权威，expected 用 Python 当场算，不硬编码手算值
import math
check("need(1)=60 / need(30)=floor(60×30^1.65)（公式权威，非蓝图表手算值）",
      combat.lua("expneed", 1, 60, 165)["need"] == 60
      and combat.lua("expneed", 30, 60, 165)["need"] == math.floor(60 * 30 ** 1.65))
needs = [combat.lua("expneed", i, 60, 165)["need"] for i in range(1, 30)]
check("曲线严格单调递增", all(b > a for a, b in zip(needs, needs[1:])))
p = new_player(29)
combat.grant_exp(CFG, p, io, 999999)
check("30 级封顶：999999 经验也只到 30", p["level"] == 30)

# ── 门禁3 纯普攻全通：CLI 400×「1」不死通关，Lv.25 / 金币 798 / h2 done ──
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("CLI 全通：不死通关（无「你倒下了」）、地图 10/10",
      "你倒下了" not in r.stdout and "地图推进 10/10" in r.stdout
      and after["maps_cleared"] == 10 and after["week"] == 1)
check("全通基线：Lv.25、金币 798、h2 done（DESIGN_V2_6 §4.3 实测钉死）",
      after["level"] == 25 and after["gold"] == 798
      and after["quest_flags"].get("h2") == "done")
check("升级回满血（V2.6：否则十图磨血必死于终幕）", "HP 回满" in r.stdout)
os.remove("save.json")

# ── 门禁4 爬塔曲线：exp = 30×层数^1.65；通关档续爬可顶到 30 级封顶 ──
m30 = tower.layer_mon(CFG, 30)
check("第 30 层 exp = 30×30^1.65 ≈ 8205（曲线产出）",
      m30["exp"] == round(30 * 30 ** 1.65))
p = new_player(25)
for s in gear.SLOTS[1:]:                       # 满配（与 v25 门禁4 同款）
    it = gear.generate(s, 30, 2)
    it["enh"] = 10
    p["equipment"][s] = it
p["equipment"]["weapon"] = gear.make_staff()
engine.apply_gear(CFG, p)
p["hp"] = p["max_hp"]
for _ in range(30):
    if tower.run_one(CFG, skills, p, [], io) != "win":
        break
check("通关档（Lv.25 满配）爬 30 层顶到 30 级封顶",
      p["tower_layer"] == 30 and p["level"] == 30 and p["hp"] > 0)

# ── 门禁5 回归：smoke_v25 + validate.py ──
r = subprocess.run([WB, "tests/smoke_v25.py"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("smoke_v25 回归", "全部通过" in r.stdout)
if "失败" in r.stdout:
    print(r.stdout[-800:])
r = subprocess.run([WB, "validate.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("validate 十六项全绿（V2.9-A 起含 V29-01/02/03；V2.9-B 起含 V30-01）（V2.8 起含 V27-01/02 + V28-01/02/03）", r.returncode == 0 and r.stdout.count("✓") == 16)

# ── 门禁6 行数纪律 ──
limits = {"engine.py": 222, "tower.py": 100, "combat.py": 130,
          "validate.py": 165, "gui_tower.py": 200, "rewards.py": 60}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items()
             if sum(1 for _ in open(f, encoding="utf-8")) > lim]
check("行数纪律（engine≤222、tower≤100、combat≤130、validate≤165）", not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
import shutil as _sh
for _f in ("accounts.json", "session.json", "save.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh.rmtree("saves", ignore_errors=True)
print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
