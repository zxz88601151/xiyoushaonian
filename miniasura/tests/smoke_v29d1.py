# V2.9-D1 出口验收 · 八门禁（DESIGN_V2_9_D1 §5）
# D1a：变体计数 / 图鉴不受污染 / 成就 / 称号表 / 幻影榜 / 迁移 / 行数与全链；D1b：佩戴写档与大厅显示。
import configparser
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # D1b：本文件要开真窗口断言控件
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name, flush=True)


import encounter
import engine
import progress
import save

TMP = "save_v29d1.json"
if os.path.exists(TMP):
    os.remove(TMP)
save.set_path(TMP)


class Io:
    def __init__(self):
        self.said = []

    def say(self, msg=""):
        self.said.append(msg)

    def ask(self, prompt=""):
        return "1"          # 难度取普通；对话看完；战斗普攻


# ── 门禁1：主线 win 的变体计数（真跑一局，非纯单测）──
engine.run_game(Io())
data = json.load(open(TMP, encoding="utf-8"))
cfg = configparser.ConfigParser()
cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
texts = engine.load_texts()
maps = engine.build_maps(texts["maps.txt"], cfg, engine.parse_kv(texts["monsters.txt"]))
fi, expect_elite = 0, 0
for m in maps:
    for f in m["fights"]:
        if f["mon"].get("key") != "boss" and encounter.roll_kind(0, m["no"], fi) < 20:
            expect_elite += 1
        fi += 1
check("1 变体计数：week0 全通精英数吻合 %d、稀有 0、schema%d" % (expect_elite, save.SCHEMA),
      data.get("schema") == save.SCHEMA and data.get("elite_kills") == expect_elite
      and data.get("rare_kills") == 0)

# ── 门禁2：kills 键不被污染（图鉴口径不变）──
mon_keys = set(engine.parse_kv(texts["monsters.txt"]))
bad_keys = [k for k in data.get("kills", {}) if k.startswith(("elite:", "rare:", "golden:"))]
check("2 图鉴口径：kills 键全是怪物 key，无变体前缀",
      not bad_keys and set(data.get("kills", {})) <= mon_keys)

# ── 门禁3：新成就按阈值解锁，老成就并集不回归 ──
base = {"level": 1, "kills": {}, "maps_cleared": 0, "week": 0, "tower_best": 0,
        "codex_weapons": [], "inventory": [], "storage": [], "equipment": {}}
got10 = progress.evaluate(dict(base, elite_kills=10))
got9 = progress.evaluate(dict(base, elite_kills=9))
got3 = progress.evaluate(dict(base, rare_kills=3))
got_old = progress.evaluate(dict(base, kills={"huoyao": 1}))
check("3 成就：精英 10/稀有 3 解锁，差 1 不解锁，老 kills 成就照常",
      "elite_hunter" in got10 and "elite_hunter" not in got9
      and "rare_hunter" in got3 and "first_blood" in got_old)

# ── 门禁4：称号表与成就 1:1，引用全部存在 ──
titles = progress.load_titles()
ach_ids = {a["id"] for a in progress.load_achievements()}
check("4 称号表：%d 条、id 唯一、引用成就全存在、1:1" % len(titles),
      len(titles) == 8 and len({t["id"] for t in titles}) == 8
      and {t["ach"] for t in titles} == ach_ids)

# ── 门禁5：佩戴写档 + 大厅显示（D1b 表现层）──
from PySide6.QtWidgets import QApplication

import qtfont

qapp = QApplication.instance() or QApplication([])
qtfont.ensure_cjk_font(qapp)
import gui_codex
import gui_hub

save.write_raw({"schema": save.SCHEMA, "level": 20, "achievements": ["clear_all"], "title": ""})
cx = gui_codex.CodexWindow(lambda: None)
cx.refresh()
locked_hidden = cx.title_box.findData("tower30") == -1          # 未解锁不进下拉
can_wear = cx.title_box.findData("clear_all") >= 0
cx.title_box.setCurrentIndex(cx.title_box.findData("clear_all"))
cx.wear_title()
worn = (save.load() or {}).get("title") == "clear_all"
preset = cx.title_box.currentData() == "clear_all"      # 重新打开时预选当前佩戴
hub = gui_hub.HubWindow(lambda: None, lambda: None, lambda: None)
hub.refresh()
shown = "称号：西行者" == hub.title_lbl.text()
cx.title_box.setCurrentIndex(0)                                  # 回到「不佩戴」
cx.wear_title()
cleared = (save.load() or {}).get("title") == ""
check("5 佩戴：未解锁不进下拉、佩戴写档、重开预选、大厅显示、可取消",
      locked_hidden and can_wear and worn and preset and shown and cleared
      and "● 西行者" in cx.title_list.toPlainText())

# ── 门禁6：幻影榜只刷新更优值（更高伤害 / 更少回合）──
p = {}
progress.on_battle_win(p, {"mon": {"name": "小妖甲"}}, {"dealt": 146, "rounds": 3})
progress.on_battle_win(p, {"mon": {"name": "火妖"}}, {"dealt": 224, "rounds": 1})
progress.on_battle_win(p, {"mon": {"name": "白骨夫人"}}, {"dealt": 100, "rounds": 5})
r = p["records"]
better = (r["best_dealt"], r["best_dealt_mon"], r["best_rounds"], r["best_rounds_mon"]) == (224, "火妖", 1, "火妖")
progress.on_battle_win(p, {"mon": {"name": "白骨夫人"}}, {"dealt": 900, "rounds": 6})
r2 = p["records"]
check("6 幻影榜：低伤害/高回合不覆盖，更高伤害只换伤害不动回合",
      better and r2["best_dealt"] == 900 and r2["best_dealt_mon"] == "白骨夫人"
      and r2["best_rounds"] == 1 and r2["best_rounds_mon"] == "火妖")

# ── 门禁7：v9 档迁移不丢值 + validate 十八项 ──
v9 = {"schema": 9, "level": 22, "exp": 33, "hp": 210, "mp": 90, "attack": 71, "next": 5,
      "week": 1, "playtime": 1234, "gold": 456, "difficulty": 1, "protect": 2,
      "tower_best": 17, "tower_layer": 3, "maps_cleared": 10, "total_damage": 8888,
      "staff_pity": 7, "achievements": ["first_blood", "clear_all"],
      "codex_weapons": ["金箍棒"], "kills": {"huoyao": 4}, "quest_flags": {"m1": "done"}}
m = save._migrate(dict(v9))
kept = all(m.get(k) == v for k, v in v9.items() if k != "schema")
check("7 v9→v%d 迁移：D1+D2 七新字段就位且旧值一字未动" % save.SCHEMA,
      kept and m["schema"] == save.SCHEMA and m["elite_kills"] == 0 and m["rare_kills"] == 0
      and m["title"] == "" and m["records"]["best_dealt"] == 0
      and m["daily"] == {"date": "", "base": {}, "claimed": []}
      and m["weekly"] == {"week": "", "base": {}, "claimed": []}
      and m["checkin"] == {"last": "", "streak": 0, "total": 0})
rv = subprocess.run([WB, "validate.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("7b validate 十八项全绿", rv.returncode == 0 and rv.stdout.count("✓") == 18)
if rv.returncode:
    print(rv.stdout[-800:])

# ── 门禁8：行数纪律 + v20→v29c 全链回归 ──
limits = {"progress.py": 110, "save.py": 145, "engine.py": 225, "validate.py": 180,
          "gui_codex.py": 120, "gui_hub.py": 65, "tower.py": 100,
          "encounter.py": 170, "combat.py": 130}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items() if sum(1 for _ in open(f, encoding="utf-8")) > lim]
rr = subprocess.run([WB, "tests/smoke_v29c.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("8 行数纪律 + v20→v29c 全链回归",
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
