# V2.5 出口验收 · 自动化冒烟（DESIGN_V2_5.md §6 七门禁）
# Windows + lua.exe + PySide6 环境；核心掷骰用注入 rng，不靠运气。
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
import loot
import quests
import rewards
import save
import tower

CFG = tower.load_cfg()


class SilentIo:                     # 一律普攻/继续：脚本化爬塔与自动结算
    def say(self, msg=""):
        pass

    def ask(self, prompt):
        return "1"


class SeqRng:                       # 注入掷骰：验证 1% 掉率这类靠运气的分支
    def __init__(self, vals):
        self.vals = vals

    def randint(self, a, b):
        return self.vals.pop(0)


def new_player(level=14):
    p = {"level": level, "exp": 0, "mp": 100, "gold": 0,
         "inventory": [], "equipment": gear.empty_equipment(),
         "potions": {"hp": 0, "mp": 0}, "tower_best": 0, "tower_layer": 0}
    engine.apply_gear(CFG, p)
    p["hp"] = p["max_hp"]
    return p


# ── 门禁1 无级武器：ATK = 10 + 等级×6 随等级重算、三词条满值、吃强化倍率 ──
eq = gear.empty_equipment()
eq["weapon"] = gear.make_staff()
check("Lv.1 ATK=16 / Lv.30 ATK=190（蓝图 §2.4）",
      gear.totals(eq, 1)["atk"] == 16 and gear.totals(eq, 30)["atk"] == 190)
t30 = gear.totals(eq, 30)
check("三词条固定满值（吸血5 / 暴伤25 / 暴击5）",
      t30["leech"] == 5 and t30["critdmg"] == 25 and t30["crit"] == 5)
staff10 = gear.make_staff()
staff10["enh"] = 10
check("+10 强化 ×1.5：Lv.30 ATK=285",
      gear.totals({"weapon": staff10, **{s: None for s in gear.SLOTS[1:]}}, 30)["atk"] == 285)
check("item_name/item_line 认无级标记",
      "如意金箍棒·无级" in gear.item_name(staff10) and "随等级" in gear.item_line(staff10))
p30 = new_player(30)
p30["equipment"]["weapon"] = gear.make_staff()
engine.apply_gear(CFG, p30)
# V2.7 基线重定：Lv.30 解锁被动斗战之心（攻击 ×1.10）→ attack = round((105+190)×1.10) = 324
check("apply_gear 与 totals 同源（面板=实战，等级入参，含被动 ×1.10）", p30["attack"] == 324)

# ── 门禁2 获取双轨：隐藏任务必得 + boss 1% 掉率，共用同一个发放口 ──
T = quests.Tracker(quests.load(quests.load_pack_text()))
check("h2 开局挂监听（hidden 类型）", T.state("h2") == "active")
done = [q for q in T.on_event("map", 10) if q["key"] == "h2"]
check("通第 10 图 → h2 done", bool(done))
io = SilentIo()
p = new_player()
rewards.apply_rewards(CFG, p, io, done, [])
check("h2 奖励 = 无级武器进背包", gear.has_staff(p))
check("已持有则不再发（幂等，防刷出一背包棒子）",
      gear.grant_staff(p, [], io) is None and len(p["inventory"]) == 1)
p2 = new_player()
item = loot.roll(CFG, "boss", p2, [], io, rng=SeqRng([1]))     # 第一项 staff 1% 掷中
check("boss 1% 掉率命中 → 发无级武器", item is not None and item.get("scaling") == "owner")
item2 = loot.roll(CFG, "boss", p2, [], io, rng=SeqRng([1, 1]))  # 已持有 → 跳过，继续掷紫武器
check("已持有时掷中 staff 跳过、继续掷普通掉落",
      item2 is not None and item2.get("scaling") != "owner" and item2["quality"] == 2)

# ── 门禁3 爬塔：层号即等级、每 5 层掉落、金币经验入账；死亡清零、最高层保留 ──
m30 = tower.layer_mon(CFG, 30)
check("第 30 层：hp 570 / atk 72（层数即怪物等级）", m30["hp"] == 570 and m30["atk"] == 72)
skills = engine.parse_kv(engine.load_texts()["skills.txt"])
p = new_player(30)
p["equipment"]["weapon"] = gear.make_staff()
engine.apply_gear(CFG, p)
p["hp"] = p["max_hp"]
gold0 = p["gold"]
for i in range(5):
    # 注入 rng：只有第 5 层会掷一次掉落（SeqRng 给 1 必中），不靠运气
    tower.run_one(CFG, skills, p, [], io, rng=SeqRng([1]) if i == 4 else SeqRng([]))
check("连爬 5 层：tower_layer=5、tower_best=5", p["tower_layer"] == 5 and p["tower_best"] == 5)
check("金币入账（爬塔是金币产出）", p["gold"] == gold0 + sum(
    tower.layer_mon(CFG, n)["gold"] for n in range(1, 6)))
check("第 5 层掉落一次", len(p["inventory"]) >= 1)
weak = new_player(1)                           # 1 级裸装打第 12 层：必死（检验死亡路径）
weak["tower_layer"], weak["tower_best"] = 11, 5
res = tower.run_one(CFG, skills, weak, [], io)
check("死亡：本次层数清零、历史最高保留（续爬语义）",
      res == "dead" and weak["tower_layer"] == 0 and weak["tower_best"] == 5)

# ── 门禁4 出口验收：30 级满配通关无底洞 30 层不死 ──
p = new_player(30)
for s in gear.SLOTS[1:]:                       # 满配：其它部位 Lv30 紫装 +10
    it = gear.generate(s, 30, 2)
    it["enh"] = 10
    p["equipment"][s] = it
p["equipment"]["weapon"] = gear.make_staff()   # 无级武器（未强化，检验裸数值够不够）
engine.apply_gear(CFG, p)
p["hp"] = p["max_hp"]
for _ in range(30):
    if tower.run_one(CFG, skills, p, [], io) != "win":
        break
check("30 级满配通 30 层不死（蓝图出口验收）",
      p["tower_layer"] == 30 and p["tower_best"] == 30 and p["hp"] > 0)

# ── 门禁5 等级与曲线：30 级封顶、need = 60×级数^1.65 单调 ──
p = new_player(30)
combat.grant_exp(CFG, p, io, 999999)
check("30 级封顶：给 999999 经验也不再涨", p["level"] == 30)
p = new_player(1)
combat.grant_exp(CFG, p, io, 60)
check("Lv.1→2 需 60（V2.6 曲线恢复蓝图原值 60×lv^1.65）", p["level"] == 2 and p["exp"] == 0)
needs = [combat.lua("expneed", i, 60, 165)["need"] for i in range(1, 6)]
check("经验曲线严格单调递增", all(b > a for a, b in zip(needs, needs[1:])))

# ── 门禁6 validate.py 七项全绿（OD-V25-04：纳入门禁，全绿才算出期）──
r = subprocess.run([WB, "validate.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("validate.py 九项全绿（V2.7 起含 V27-01/02）", r.returncode == 0 and r.stdout.count("✓") == 9)

# ── 门禁7 GM tower/staff 命令（数字走 _int fail-closed）──
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
qapp = QApplication.instance() or QApplication([])
import login
import slots
login.register("audit25", "pw")
login.start_session("audit25", "huaguoshan", 1)
path = slots.slot_path("huaguoshan", "audit25", 1)
save.set_path(path, "audit25")
save.write_raw({"schema": save.SCHEMA, "user": "audit25", "level": 14, "exp": 0,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0,
                "playtime": 0, "gold": 0, "difficulty": 0, "protect": 0,
                "inventory": [], "equipment": gear.empty_equipment()})
r = subprocess.run([WB, "gm.py", "tower", "7"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm tower 7", r.returncode == 0 and d["tower_layer"] == 7)
r = subprocess.run([WB, "gm.py", "tower", "abc"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("gm tower 非数字被拒", r.returncode == 1)
r = subprocess.run([WB, "gm.py", "staff"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm staff 发无级武器", r.returncode == 0
      and any(i.get("scaling") == "owner" for i in d["inventory"]))

# ── 门禁8 爬塔窗与大厅入口（offscreen）──
import gui_tower
tw = gui_tower.TowerWindow(lambda: None)
tw.refresh()
check("未通关：爬塔窗按钮禁用（OD-V25-03 解锁门）", not tw.fight_btn.isEnabled())
d["week"] = 1
save.write_raw(d)
tw.refresh()
check("通关一次后：爬塔窗按钮启用", tw.fight_btn.isEnabled() and "历史最高" in tw.info.text())
from gui_hub import HubWindow
hub = HubWindow(lambda: None, lambda: None, lambda: None)
hub.refresh()
check("大厅「无底洞」按钮按解锁状态显隐", not hub.tower_btn.isHidden())
d["week"] = 0
save.write_raw(d)
hub.refresh()
check("未通关时大厅按钮隐藏", hub.tower_btn.isHidden())
login.logout()
for f in ("accounts.json", "session.json"):
    if os.path.exists(f):
        os.remove(f)
save.set_path(os.path.join(HERE, "save.json"))

# ── 门禁9 行数纪律与回归 ──
limits = {"engine.py": 220, "tower.py": 100, "validate.py": 150,
          "gui_tower.py": 200, "combat.py": 130, "quests.py": 100, "rewards.py": 60}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items()
             if sum(1 for _ in open(f, encoding="utf-8")) > lim]
check("行数纪律（engine≤220、tower≤100、validate≤150、gui_tower≤200）", not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
# V2.6 基线重定：Lv.1 开局 + 曲线恢复 60×lv^1.65 → 全通 Lv.25；图10 倍率 1.0 → 金币 798
check("CLI 全通回归：地图 10/10、金币 798、Lv.25、h2 done（V2.6 重定）",
      "地图推进 10/10" in r.stdout and after["maps_cleared"] == 10
      and after["gold"] == 798 and after["level"] == 25
      and after["quest_flags"].get("h2") == "done")
os.remove("save.json")
r = subprocess.run([WB, "tests/smoke_v24.py"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("smoke_v24 回归", "全部通过" in r.stdout)
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
