# V2.3 出口验收 · 自动化冒烟（DESIGN_V2_3.md §7 七门禁）
# 门禁：金币/迁移/掉落/难度/商店金币/GM/行数/回归（Windows + lua.exe + PySide6 环境）
import configparser
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
import loot
import save

cfg = configparser.ConfigParser()
cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
texts = engine.load_texts()
monsters = engine.parse_kv(texts["monsters.txt"])

# ── 门禁1 金币与难度倍率（build_maps 纯数据层，无需 Lua）──
maps0 = engine.build_maps(texts["maps.txt"], cfg, monsters, 0)
gold0 = sum(f["mon"]["gold"] for m in maps0 for f in m["fights"])
# V2.6 基线重定：图10 倍率 1.6→1.0（boss 本体已加强），全通金币 918→798；boss 数值重钉
check("普通难度金币合计 798（V2.6 重定）", gold0 == 798)
maps1 = engine.build_maps(texts["maps.txt"], cfg, monsters, 1)
boss1 = [f["mon"] for m in maps1 for f in m["fights"] if f["key"] == "boss"][0]
check("精英 boss：血 780 / 攻 52 / 经验 82500 / 金币 300（V2.6 重钉）",
      (boss1["hp"], boss1["atk"], boss1["exp"], boss1["gold"]) == (780, 52, 82500, 300))
check("难度询问：1/2/3 与非法输入",
      loot.ask_difficulty(type("I", (), {"ask": lambda s, p: "2"})()) == 1
      and loot.ask_difficulty(type("I", (), {"ask": lambda s, p: "x"})()) == 0)

# ── 门禁1b 迁移：v4 档 → schema 6（V2.4），金币/难度/保底符/强化补默认值、旧字段不丢──
if os.path.exists("save.json"):
    os.remove("save.json")
save.write_raw({"schema": 4, "user": "", "level": 14, "exp": 10, "hp": 100, "mp": 50,
                "attack": 57, "next": 3, "week": 0, "playtime": 0,
                "inventory": [{"slot": 0, "lv": 5, "quality": 0,
                               "main": {"atk": 1, "hp": 0, "def": 0, "dodge": 0}, "affixes": []}]})
d = save.load()
check("v4→v%d 迁移：schema %d、金币 0、难度 0、保底符 0、旧装备 enh=0、等级不丢" % (save.SCHEMA, save.SCHEMA),
      d["schema"] == save.SCHEMA and d["gold"] == 0 and d["difficulty"] == 0 and d["protect"] == 0
      and d["inventory"][0]["enh"] == 0 and d["level"] == 14)
os.remove("save.json")

# ── 门禁2 掉落：掷中/掷不中/满包转仓库/品质加成封顶──
class SeqRng:
    def __init__(self, vals): self.vals = vals
    def randint(self, a, b): return self.vals.pop(0)


class SilentIo:
    def say(self, msg=""): pass


player = {"level": 14, "inventory": [], "equipment": gear.empty_equipment()}
storage = []
item = loot.roll(cfg, "xiaoyao1", player, storage, SilentIo(), 0, SeqRng([1]))
check("掉落掷中：第一项武器白装进背包",
      item is not None and item["slot"] == 0 and item["quality"] == 0
      and len(player["inventory"]) == 1)
item = loot.roll(cfg, "xiaoyao1", player, storage, SilentIo(), 0, SeqRng([100, 100]))
check("掉落掷不中：无掉落", item is None)
player2 = {"level": 14, "inventory": [{"x": 1}] * gear.capacity(),
           "equipment": gear.empty_equipment()}
storage2 = []
item = loot.roll(cfg, "boss", player2, storage2, SilentIo(), 2, SeqRng([1]))
check("满包掉落转仓库、噩梦品质封顶紫",
      item is not None and item["quality"] == 2 and len(storage2) == 1
      and len(player2["inventory"]) == gear.capacity())

# ── 门禁4 商店金币闭环（GUI offscreen，与 smoke_v22 同套路）──
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QMessageBox
qapp = QApplication.instance() or QApplication([])
import qtfont; qtfont.ensure_cjk_font(qapp)   # 字体引导：offscreen 下字体库为空，中文会变方框
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
import gui_shop
save.write_raw({"schema": save.SCHEMA, "user": "", "level": 14, "exp": 100, "gold": 100,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0, "playtime": 0,
                "inventory": [gear.generate("weapon", 5, 0)],
                "equipment": gear.empty_equipment()})
shop = gui_shop.ShopWindow(lambda: None, lambda: None)
shop.refresh()
shop.buy("hp_potion")
d = json.load(open("save.json", encoding="utf-8"))
check("商店金币买药：金币 100→70、库存+1、经验不动",
      d["gold"] == 70 and d["potions"]["hp"] == 1 and d["exp"] == 100)
shop.recycle_list.setCurrentRow(0)
shop.recycle()
d = json.load(open("save.json", encoding="utf-8"))
check("商店回收返金币：装备消失、金币 70→76",
      len(d["inventory"]) == 0 and d["gold"] == 70 + round((5 + 5 * 3) * 0.3))
os.remove("save.json")

# ── 门禁5 GM gold / difficulty + fail-closed──
import login
import slots
login.register("audit23", "pw")
login.start_session("audit23", "huaguoshan", 1)
path = slots.slot_path("huaguoshan", "audit23", 1)
save.set_path(path, "audit23")
save.write_raw({"schema": save.SCHEMA, "user": "audit23", "level": 14, "exp": 0,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0, "playtime": 0})
r = subprocess.run([WB, "gm.py", "gold", "500"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm gold 500", r.returncode == 0 and d["gold"] == 500)
r = subprocess.run([WB, "gm.py", "difficulty", "2"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm difficulty 2", r.returncode == 0 and d["difficulty"] == 2)
r = subprocess.run([WB, "gm.py", "difficulty", "3"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("gm difficulty 越界被拒", r.returncode == 1)
r = subprocess.run([WB, "gm.py", "gold", "abc"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("gm gold 非数字被拒", r.returncode == 1)
login.logout()
for f in ("accounts.json", "session.json"):
    if os.path.exists(f):
        os.remove(f)
save.set_path(os.path.join(HERE, "save.json"))

# ── 门禁6 行数纪律──
limits = {"engine.py": 220, "loot.py": 100, "gui_shop.py": 200}
bad_lines = []
for f, lim in limits.items():
    n = sum(1 for _ in open(f, encoding="utf-8"))
    if n > lim:
        bad_lines.append(f"{f}={n}>{lim}")
check("行数纪律（engine≤220、loot≤100、gui_shop≤200）", not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)

# ── 门禁7 回归：CLI 全通（难度提示首个“1”=普通）+ smoke_v22──
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("CLI 全通：地图 10/10、金币 798（V2.6 重定）、难度 0",
      "地图推进 10/10" in r.stdout and after["maps_cleared"] == 10
      and after["gold"] == 798 and after["difficulty"] == 0)
os.remove("save.json")
r = subprocess.run([WB, "tests/smoke_v22.py"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("smoke_v22 回归", "全部通过" in r.stdout)
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
