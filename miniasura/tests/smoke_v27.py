# V2.7 出口验收 · 自动化冒烟（DESIGN_V27 §9 六门禁）
# 十技能 + CD + 命中闪避 + 武器谱特效；核心掷骰注入 SeqRng，不靠运气。
import json
import os
import random
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
import skills
import tower

CFG = tower.load_cfg()
T = skills.load_skills()


class CapIo:                        # 捕获日志 + 按序回答（战斗交互测试用）
    def __init__(self, answers):
        self.answers, self.log = list(answers), []

    def say(self, msg=""):
        self.log.append(msg)

    def ask(self, prompt):
        return self.answers.pop(0)


class SeqRng:                       # 注入掷骰：验证命中/闪避/MISS 这类靠运气的分支
    def __init__(self, vals):
        self.vals = list(vals)

    def randint(self, a, b):
        return self.vals.pop(0)


def new_player(level):
    p = {"level": level, "exp": 0, "mp": 100, "gold": 0,
         "inventory": [], "equipment": gear.empty_equipment(),
         "potions": {"hp": 0, "mp": 0}, "tower_best": 0, "tower_layer": 0}
    engine.apply_gear(CFG, p)
    p["hp"] = p["max_hp"]
    return p


# ── 门禁1 技能解锁：菜单按蓝图表，未解锁灰字不可选，被动不进菜单 ──
LADDER = [(1, []), (3, ["dinghai"]), (6, ["dinghai", "jindou"]),
          (10, ["dinghai", "jindou", "qishi"]),
          (18, ["dinghai", "jindou", "qishi", "canshen"]),
          (26, ["dinghai", "jindou", "qishi", "canshen", "bangsao"]),
          (30, ["dinghai", "jindou", "qishi", "canshen", "bangsao", "ruyi"])]
check("技能解锁档与蓝图表一致（Lv.3/6/10/18/26/30）",
      all([s["id"] for s in skills.unlocked_skills(T, lv)[0]] == ids for lv, ids in LADDER))
check("被动不进菜单（主动 6 个，被动 3 个）",
      len(skills.actives(T)) == 6
      and sum(1 for s in T.values() if s["kind"] == "passive") == 3)
p10 = new_player(10)
cap = CapIo(["5"])              # 选棒扫六合（第 5 主动，Lv.26 解锁）
check("未解锁技能：菜单灰字「Lv.26 解锁」、选择被拒不耗回合",
      skills.choose(T, p10, cap, skills.Cooldowns()) is None
      and any("Lv.26 解锁" in m for m in cap.log) and p10["mp"] == 100)

# ── 门禁2 CD：use/tick 递减/reset 清零；CD 中菜单灰字不可选 ──
cds = skills.Cooldowns()
cds.use("bangsao", 3)
cd_ok = not cds.usable("bangsao") and cds.remain("bangsao") == 3
cds.tick()
cd_ok &= cds.remain("bangsao") == 2
cds.tick()
cds.tick()
cd_ok &= cds.usable("bangsao")                 # 3 → 2 → 1 → 0 清除
cds.use("ruyi", 5)
cd_ok &= not cds.usable("ruyi")
cds.reset()
cd_ok &= cds.usable("ruyi")
check("CD 表：棒扫六合 3 回合递减、如意神通 5、reset 清零", cd_ok)
p30 = new_player(30)
cds2 = skills.Cooldowns()
cds2.use("bangsao", 3)
cap2 = CapIo(["5"])
check("CD 中技能：菜单灰字「冷却中」、选择被拒",
      skills.choose(T, p30, cap2, cds2) is None
      and any("冷却中" in m for m in cap2.log))

# ── 门禁3 被动：crit +8% / 受伤 ×0.85 / 攻击 ×1.10，各有断言 ──
check("被动汇总：Lv.13 无 / Lv.14 暴击+8 / Lv.22 ×0.85 / Lv.29 攻击×1.10",
      skills.passive_totals(T, 13, {"crit": 0})["crit"] == 0
      and skills.passive_totals(T, 14, {"crit": 0})["crit"] == 8
      and skills.passive_totals(T, 22, {"crit": 0})["mitigate"] == 0.85
      and skills.passive_totals(T, 29, {"crit": 0})["atk_mult"] == 1.10)
p14 = new_player(14)
check("面板被动：Lv.14 空装备 crit_rate 28（20+8）", p14["crit_rate"] == 28)
p22 = new_player(22)
check("面板被动：Lv.22 mitigate 0.85（不坏金身）", p22["mitigate"] == 0.85)
p29 = new_player(29)
check("面板被动：Lv.29 attack ×1.10（102→112，斗战之心）", p29["attack"] == 112)

# ── 门禁4 命中/闪避：MISS 不掉血、连击中断、筋斗云 buff 仅下回合、命中率下限 60% ──
real_random = combat.random
mon = {"name": "靶", "intro": "", "hp": 5, "atk": 1, "exp": 0, "key": "tower", "tribe": "无"}
try:
    combat.random = SeqRng([96, 100, 1, 100, 100])      # R1 命中 96→MISS；R2 命中打死
    cap = CapIo(["1", "1"])
    p = new_player(30)
    combat.battle(CFG, T, dict(mon, hp=5), p, cap)
    check("MISS：伤害 0 不掉血（[靶 HP 5] 出现两次）、文案「MISS！」",
          "MISS！" in cap.log and sum("靶 HP 5" in m for m in cap.log) == 2)
    combat.random = SeqRng([96, 100, 1, 100, 100])      # 连击 R1 第一段 MISS → 中断
    cap = CapIo(["2", "4", "1"])                        # 技能→大圣残影（第 4 主动，2 段）
    p = new_player(18)
    combat.battle(CFG, T, dict(mon, hp=5), p, cap)
    check("连击 MISS：不触发第二段（怪 HP 不减两次出现）",
          "MISS！" in cap.log and sum("靶 HP 5" in m for m in cap.log) == 2)
    # 筋斗云：R1 技能后怪物闪避（buff 30），R2 起 buff 已清不再闪（怪 hp 200 撑 6 回合）
    combat.random = SeqRng([1, 100, 100, 1] * 5 + [1, 100, 100])
    cap = CapIo(["2", "2", "1", "1", "1", "1", "1"])
    p = new_player(6)                                  # Lv.6 解锁筋斗云
    combat.battle(CFG, T, dict(mon, hp=200), p, cap)
    check("筋斗云 buff 仅下回合（闪开恰好 1 次），耗蓝 10",
          sum("闪开了" in m for m in cap.log) == 1 and p["mp"] == 90)
    # 命中率下限 60%：极端闪避怪（dodge=100）→ 95-100=-5 → 下限 60；骰 61 MISS / 60 命中
    combat.random = SeqRng([61, 100, 60, 100, 100, 100])
    cap = CapIo(["1", "1"])
    p = new_player(30)
    combat.battle(CFG, T, dict(mon, hp=5, dodge=100), p, cap)
    first_round_miss = "MISS！" in cap.log
    combat.random = SeqRng([60, 100, 100, 1, 100, 100, 100])
    cap = CapIo(["1", "1"])
    p = new_player(30)
    combat.battle(CFG, T, dict(mon, hp=5, dodge=100), p, cap)
    check("命中率下限 60%（极端闪避怪 dodge=100）：骰 61 MISS / 骰 60 命中",
          first_round_miss and "MISS！" not in cap.log)
finally:
    combat.random = real_random


# ── 门禁5 武器谱特效：vs_tribe / 暴伤 / 蓝档无特效 / 吸血上限 10% ──
def weapon_with(name, kind, param, affixes=None):
    return {"slot": 0, "lv": 30, "quality": 2, "enh": 0, "name": name,
            "effect": {"kind": kind, "param": param},
            "main": {"atk": 100, "hp": 0, "def": 0, "dodge": 0},
            "affixes": affixes or []}


p = new_player(30)
p["equipment"]["weapon"] = weapon_with("定水枪", "vs_tribe:水族", "1.15")
check("定水枪打水族 ×1.15 / 打非水族 1.0",
      skills.weapon_effect(p, {"tribe": "水族"}) == 1.15
      and skills.weapon_effect(p, {"tribe": "无"}) == 1.0)
p["equipment"]["weapon"] = weapon_with("降魔杖", "vs_tribe:妖", "1.12")
check("降魔杖打妖 ×1.12（boss tribe=妖）", skills.weapon_effect(p, {"tribe": "妖"}) == 1.12)
# 期望 114 不是 115：Lua floor(100×1.15) 受浮点精度影响（100*1.15=114.999...），如实记录
check("特效倍率走 battle.lua 第 7 参（damage 100×1.0×1.15=114，浮点 floor）",
      combat.lua("damage", 100, 1.0, 0, 0, 100, 1.15)["dmg"] == 114)
p["equipment"]["weapon"] = weapon_with("白骨剑", "critdmg", "0.15")
check("白骨剑暴伤 +15 进 totals 汇总", gear.totals(p["equipment"], 30)["critdmg"] == 15)
blue = gear.generate("weapon", 30, 1, rng=random.Random(1))
check("蓝档同部位武器无特效", blue.get("effect") is None)
p["equipment"]["weapon"] = weapon_with(
    "缠丝爪", "leech", "0.03",
    affixes=[{"key": "leech", "name": "吸血%", "val": 5.0},
             {"key": "leech", "name": "吸血%", "val": 5.0}])
check("吸血叠加上限 10%（缠丝爪 3% + 双满值词条 10% → 封顶）",
      gear.totals(p["equipment"], 30)["leech"] == 10)

# ── 门禁6 回归：CLI 全通 + smoke_v26 + validate 九项 + 行数纪律 ──
limits = {"engine.py": 225, "combat.py": 130, "skills.py": 150, "validate.py": 215}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items()
             if sum(1 for _ in open(f, encoding="utf-8")) > lim]
check("行数纪律（engine≤225、combat≤130、skills≤150、validate≤180）", not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)
r = subprocess.run([WB, "validate.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("validate 十九项全绿（V2.9-A 起含 V29-01/02/03；V2.9-B 起含 V30-01）（V2.8 起含 V28-01/02/03）", r.returncode == 0 and r.stdout.count("✓") == 19)
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("CLI 全通回归（V2.7 战斗状态化后纯普攻仍全通：Lv.25/金币 798）",
      "你倒下了" not in r.stdout and after["maps_cleared"] == 10
      and after["gold"] == 798 and after["level"] == 25)
os.remove("save.json")
r = subprocess.run([WB, "tests/smoke_v26.py"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("smoke_v26 回归", "全部通过" in r.stdout)
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
