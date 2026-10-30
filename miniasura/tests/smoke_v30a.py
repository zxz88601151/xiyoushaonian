# V3.0-A 出口验收 · 八门禁（DESIGN_V3_0_A.md §7）
# 零影响 / 宝石单层 / 碎片与合成 / 套装阈值 / 属性点 / UI / 迁移与校验 / 行数与全链。
import configparser
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name, flush=True)


import attrs
import gear
import gem
import save
import sets

cfg = configparser.ConfigParser()
cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")


def bare(slot, quality=2, key=None):
    """造一件可控装备：清词条、清套装标记（避免随机词条把断言搅浑）。"""
    it = gear.generate(slot, 10, quality)
    it["affixes"] = []
    if key:
        it["set"] = key
    else:
        it.pop("set", None)
    return it


# ── 门禁1：零影响（不主动投入 = 面板一分不变）──
zero = {"atk": 0.0, "hp": 0.0, "def": 0.0, "crit": 0.0}
empty = gear.empty_equipment()
naked = gear.totals(empty, 25)
check("1 零影响：三源空态全 0，extra 全 0 时 totals 与不传 extra 逐键相等",
      gem.bonus({}) == zero and sets.bonus({}) == {}
      and attrs.bonus({"level": 30}, cfg) == {"atk": 0.0, "hp": 0.0, "def": 0.0, "crit": 0.0}
      and gear.totals(empty, 25, dict(zero)) == naked)

# ── 门禁2：宝石单层（孔位按品质 / 镶嵌生效 / 拒重复 / 拆卸无损）──
it = bare("armor")
h = gem.holes_of(it)
base = gear.totals({"armor": it}, 10)["atk"]
r1, _ = gem.socket(it, 0, {"key": "atk", "lv": 3})
mid = gear.totals({"armor": it}, 10)["atk"]
dup, _ = gem.socket(it, 1, {"key": "atk", "lv": 1})
oob, _ = gem.socket(it, 5, {"key": "hp", "lv": 1})
back = gem.unsocket(it, 0)
end = gear.totals({"armor": it}, 10)["atk"]
check("2 宝石单层：紫装 2 孔、3 级赤火石 +12 攻、同类/越界拒绝、拆卸退回并回落",
      h == 2 and r1 and abs(mid - base - 12.0) < 1e-9
      and not dup and not oob and back["key"] == "atk" and abs(end - base) < 1e-9)

# ── 门禁3：碎片开宝 + 三合一（封顶 5 级）──
poor = {"shard": 2, "gems": []}
p1, _ = gem.open_shard(poor, cfg, random.Random(7))
rich = {"shard": 5, "gems": []}
p2, _ = gem.open_shard(rich, cfg, random.Random(7))
key = rich["gems"][0]["key"]
rich["gems"] = [{"key": key, "lv": 1}] * 3
m1, _ = gem.merge(rich, key, 1)
top = {"gems": [{"key": "hp", "lv": gem.MAX_LV}] * 3}
m2, _ = gem.merge(top, "hp", gem.MAX_LV)
check("3 碎片不足拒绝无损、3 碎片开 1 颗、三合一得 2 级、5 级封顶不吃 6 级",
      not p1 and poor == {"shard": 2, "gems": []} and p2 and rich["shard"] == 2
      and m1 and rich["gems"] == [{"key": key, "lv": 2}]
      and not m2 and len(top["gems"]) == 3)

# ── 门禁4：套装阈值（2 件 / 4 件互斥取高 / 判定可复现）──
eq2 = {"weapon": bare("weapon", key="huoyan"), "helm": bare("helm", key="huoyan")}
eq3 = dict(eq2, belt=bare("belt", key="huoyan"))
eq4 = dict(eq3, armor=bare("armor", key="huoyan"))
probe = bare("armor")
check("4 套装：2 件吃 2 件效果、3 件同上、4 件只吃 4 件（不叠）、件判定可复现",
      sets.active(eq4) == {"huoyan": 4}
      and sets.bonus(eq2) == {"atk": 12.0} and sets.bonus(eq3) == {"atk": 12.0}
      and sets.bonus(eq4) == {"critdmg": 30.0, "leech": 3.0}
      and sets.roll_set(dict(probe), cfg) == sets.roll_set(dict(probe), cfg))

# ── 门禁5：属性点（Lv.2 起 3 点/级 / 超量拒绝 / 免费洗点）──
pl = {"level": 3}
tot = attrs.total(pl, cfg)
a1, _ = attrs.add(pl, "atk", 2, cfg)
a2, _ = attrs.add(pl, "atk", 99, cfg)
mid_atk = attrs.bonus(pl, cfg)["atk"]
left = attrs.free(pl, cfg)
attrs.reset(pl)
check("5 属性点：Lv.3 共 6 点、加 2 点攻 +2、超量拒绝、洗点全额退回",
      tot == 6 and a1 and not a2 and abs(mid_atk - 2.0) < 1e-9 and left == 4
      and attrs.bonus(pl, cfg)["atk"] == 0 and attrs.free(pl, cfg) == 6)

# ── 门禁6：UI（offscreen 真窗口，五个操作逐一写档）──
from PySide6.QtWidgets import QApplication

import qtfont

qapp = QApplication.instance() or QApplication([])
qtfont.ensure_cjk_font(qapp)
import gui_grow

TMP = "save_v30a.json"
if os.path.exists(TMP):
    os.remove(TMP)
save.set_path(TMP)
armor = bare("armor")
save.write_raw({"schema": save.SCHEMA, "level": 5, "gold": 0, "shard": 3, "gems": [],
                "attr": {"spent": {"atk": 0, "hp": 0, "def": 0, "crit": 0}},
                "equipment": {s: None for s in gear.SLOTS} | {"armor": armor}})
w = gui_grow.GrowWindow(lambda: None)
w.refresh()
w.btns["open"].click()
d1 = json.load(open(TMP, encoding="utf-8"))
w.gem_box.setCurrentIndex(0)
w.btns["socket"].click()
d2 = json.load(open(TMP, encoding="utf-8"))
w.btns["unsocket"].click()
d3 = json.load(open(TMP, encoding="utf-8"))
w.btns[("attr", "atk")].click()
d4 = json.load(open(TMP, encoding="utf-8"))
w.reset_btn.click()
d5 = json.load(open(TMP, encoding="utf-8"))
check("6 UI：开宝→镶嵌→拆卸→加点→洗点全部落盘（拒绝路径零副作用不另测，见门禁2/5）",
      d1["shard"] == 0 and len(d1["gems"]) == 1
      and d2["gems"] == [] and d2["equipment"]["armor"]["gems"][0]
      and d3["gems"] and not d3["equipment"]["armor"]["gems"][0]
      and d4["attr"]["spent"]["atk"] == 1
      and d5["attr"]["spent"] == {"atk": 0, "hp": 0, "def": 0, "crit": 0})

# ── 门禁7：v11→v12 迁移 + validate 十九项 ──
v11 = {"schema": 11, "level": 22, "exp": 33, "hp": 210, "mp": 90, "attack": 71, "next": 5,
       "week": 1, "playtime": 1234, "gold": 456, "difficulty": 1, "protect": 2,
       "tower_best": 17, "tower_layer": 3, "maps_cleared": 10, "total_damage": 8888,
       "staff_pity": 7, "achievements": ["clear_all"], "codex_weapons": ["金箍棒"],
       "kills": {"huoyao": 4}, "quest_flags": {"m1": "done"},
       "elite_kills": 4, "rare_kills": 2, "title": "clear_all",
       "records": {"best_dealt": 615, "best_dealt_mon": "白骨夫人", "best_rounds": 1, "best_rounds_mon": "小妖甲"},
       "daily": {"date": "2026-01-01", "base": {"kills": 3, "damage": 10, "tower": 0}, "claimed": ["kills"]},
       "weekly": {"week": "2026-W01", "base": {"kills": 0, "damage": 0, "tower": 0}, "claimed": []},
       "checkin": {"last": "2026-01-01", "streak": 2, "total": 3}}
m = save._migrate(dict(v11))
kept = all(m.get(k) == v for k, v in v11.items() if k != "schema")
check("7 v11→v12 迁移：四新字段就位且旧值一字未动",
      kept and m["schema"] == save.SCHEMA and m["shard"] == 0 and m["gems"] == [] and m["set_seen"] == []
      and m["attr"] == {"spent": {"atk": 0, "hp": 0, "def": 0, "crit": 0}})
rv = subprocess.run([WB, "validate.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("7b validate 十九项全绿", rv.returncode == 0 and rv.stdout.count("✓") == 19)
if rv.returncode:
    print(rv.stdout[-800:])

# ── 门禁8：行数纪律 + v20→v29d2 全链回归（含 CLI 全通零影响）──
limits = {"gem.py": 150, "sets.py": 150, "attrs.py": 100, "gui_grow.py": 180,
          "gear.py": 250, "save.py": 145, "app.py": 145, "validate.py": 215,
          "engine.py": 225, "gui_bag.py": 190, "gui_hub.py": 65, "loot.py": 100}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items() if sum(1 for _ in open(f, encoding="utf-8")) > lim]
rr = subprocess.run([WB, "tests/smoke_v29d2.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("8 行数纪律 + v20→v29d2 全链回归（CLI 全通 Lv.25 / 798 原样）",
      not bad_lines and rr.returncode == 0 and "全部通过" in rr.stdout and rr.stdout.count("✗") == 0)
if bad_lines:
    print("  超标:", bad_lines)
if rr.returncode or rr.stdout.count("✗"):
    print(rr.stdout[-1500:])

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
for _f in ("accounts.json", "session.json", "save.json", TMP):
    if os.path.exists(_f):
        os.remove(_f)
print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
