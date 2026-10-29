# V2.4 出口验收 · 自动化冒烟（DESIGN_V2_4.md §6 六门禁）
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


import enhance
import gear
import rewards
import save

# ── 门禁1 强化数值：totals 加成与显示──
eq = {"weapon": {"slot": 0, "lv": 14, "quality": 0, "enh": 0,
                  "main": {"atk": 100, "hp": 50, "def": 10, "dodge": 5}, "affixes": []},
      "helm": None, "armor": None, "belt": None, "boots": None}
check("totals +0 不变", gear.totals(eq)["atk"] == 100)
eq["weapon"]["enh"] = 10
tot = gear.totals(eq)
check("+10：atk/hp/def ×1.5，闪避不动",
      tot["atk"] == 150 and tot["hp"] == 75 and tot["def"] == 15 and tot["dodge"] == 5)
check("item_line 显示 +10", "+10" in gear.item_line(eq["weapon"]))

# ── 门禁2 强化流程：费用/必成/失败降级/保底符/金币不足/到顶──
class SeqRng:
    def __init__(self, vals): self.vals = vals
    def randint(self, a, b): return self.vals.pop(0)


it = {"slot": 0, "lv": 14, "quality": 0, "enh": 0,
      "main": {"atk": 1, "hp": 0, "def": 0, "dodge": 0}, "affixes": []}
check("费用：Lv14 +0→+1 = 48", enhance.cost(it) == 48)
ok2, gold, prot, _ = enhance.enhance(it, 100, 0, False, SeqRng([1]))
check("+0 必成、金币 100→52", ok2 and it["enh"] == 1 and gold == 52)
ok2, gold, prot, _ = enhance.enhance(it, 10, 0, False, SeqRng([1]))
check("金币不足不扣钱不改装备", not ok2 and gold == 10 and it["enh"] == 1)
it["enh"] = 7
ok2, gold, prot, msg = enhance.enhance(it, 1000, 0, False, SeqRng([100]))
check("+7 失败降级到 +6、金币照扣（费用 188）", not ok2 and it["enh"] == 6 and gold == 1000 - 188)
it["enh"] = 7
ok2, gold, prot, msg = enhance.enhance(it, 1000, 1, True, SeqRng([100]))
check("+7 失败有保底符：保级、只耗 1 张", not ok2 and it["enh"] == 7 and prot == 0)
it["enh"] = 10
ok2, gold, prot, _ = enhance.enhance(it, 1000, 0, False, SeqRng([1]))
check("+10 到顶不扣钱", not ok2 and gold == 1000 and it["enh"] == 10)

# ── 门禁3 死亡惩罚：10% 向下取整、不掉级、<10 不扣──
class SilentIo:
    def say(self, msg=""): pass


pl = {"exp": 50, "level": 14}
check("exp 50 死一次扣 5 变 45", rewards.apply_death_penalty(pl, SilentIo()) == 5
      and pl["exp"] == 45 and pl["level"] == 14)
pl = {"exp": 9}
check("exp 9 死一次扣 0", rewards.apply_death_penalty(pl, SilentIo()) == 0
      and pl["exp"] == 9)

# ── 门禁4 存档迁移：v5 档 → schema 6──
if os.path.exists("save.json"):
    os.remove("save.json")
save.write_raw({"schema": 5, "user": "", "level": 14, "exp": 0, "hp": 150, "mp": 100,
                "attack": 57, "next": 0, "week": 0, "playtime": 0, "gold": 100,
                "difficulty": 0,
                "inventory": [{"slot": 0, "lv": 5, "quality": 0,
                               "main": {"atk": 1, "hp": 0, "def": 0, "dodge": 0},
                               "affixes": []}],
                "equipment": {"weapon": None, "helm": None, "armor": None,
                              "belt": None, "boots": None}})
d = save.load()
check("v5→v%d：schema %d、protect 0、旧装备 enh=0、金币不丢" % (save.SCHEMA, save.SCHEMA),
      d["schema"] == save.SCHEMA and d["protect"] == 0 and d["inventory"][0]["enh"] == 0
      and d["gold"] == 100)
os.remove("save.json")

# ── 门禁5 GM protect + UI（offscreen 商店保底符、铁匠窗列装）──
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QMessageBox
qapp = QApplication.instance() or QApplication([])
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
import gui_enhance
import gui_shop
import login
import slots
login.register("audit24", "pw")
login.start_session("audit24", "huaguoshan", 1)
path = slots.slot_path("huaguoshan", "audit24", 1)
save.set_path(path, "audit24")
save.write_raw({"schema": save.SCHEMA, "user": "audit24", "level": 14, "exp": 0,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0,
                "playtime": 0, "gold": 500, "difficulty": 0, "protect": 0,
                "inventory": [gear.generate("weapon", 5, 0)],
                "equipment": gear.empty_equipment()})
r = subprocess.run([WB, "gm.py", "protect", "3"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm protect 3", r.returncode == 0 and d["protect"] == 3)
r = subprocess.run([WB, "gm.py", "protect", "abc"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("gm protect 非数字被拒", r.returncode == 1)
shop = gui_shop.ShopWindow(lambda: None, lambda: None)
shop.refresh()
shop.buy("protect")
d = json.load(open(path, encoding="utf-8"))
check("商店买保底符：金币 500→400、保底符 3→4",
      d["gold"] == 400 and d["protect"] == 4)
ew = gui_enhance.EnhanceWindow(lambda: None)
ew.refresh()
check("铁匠窗列出背包装备", ew.listw.count() == 1)
ew.listw.setCurrentRow(0)
ew.do_enhance()
d = json.load(open(path, encoding="utf-8"))
check("铁匠窗强化 Lv5 白装 +0→+1（费用 30，金币 400→370）",
      d["inventory"][0]["enh"] == 1 and d["gold"] == 370)
login.logout()
for f in ("accounts.json", "session.json"):
    if os.path.exists(f):
        os.remove(f)
save.set_path(os.path.join(HERE, "save.json"))

# ── 门禁6 行数与回归──
limits = {"engine.py": 220, "enhance.py": 150, "gui_enhance.py": 200,
          "tower.py": 100, "validate.py": 150, "gui_tower.py": 200}
bad_lines = []
for f, lim in limits.items():
    n = sum(1 for _ in open(f, encoding="utf-8"))
    if n > lim:
        bad_lines.append(f"{f}={n}>{lim}")
check("行数纪律（engine≤220、enhance≤150、gui_enhance≤200）", not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("CLI 全通回归：地图 10/10、金币 798（V2.6 重定）、难度 0（不死不强化，金币不动）",
      "地图推进 10/10" in r.stdout and after["maps_cleared"] == 10
      and after["gold"] == 798 and after["difficulty"] == 0)
os.remove("save.json")
r = subprocess.run([WB, "tests/smoke_v23.py"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("smoke_v23 回归", "全部通过" in r.stdout)
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
