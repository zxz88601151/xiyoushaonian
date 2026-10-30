# V2.9-D2 出口验收 · 八门禁（DESIGN_V2_9_D2 §5）
# 跨日/跨周滚动 / 进度口径 / 领取规则 / 签到 / UI / 迁移与校验 / 行数与全链。
import configparser
import json
import os
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


import daily
import save

cfg = configparser.ConfigParser()
cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
D1, D2 = "2026-01-01", "2026-01-02"
daily.today = lambda: D1
daily.this_week = lambda: "2026-W01"

# ── 门禁1：跨日滚动 ──
state = {"kills": {"a": 2}, "total_damage": 100, "tower_best": 1, "gold": 0}
daily.touch(state)
first = (state["daily"]["date"], dict(state["daily"]["base"]))
state["kills"]["a"], state["total_damage"], state["tower_best"] = 5, 400, 3
daily.today = lambda: D2
daily.touch(state)
check("1 跨日滚动：date 更新、base 取当时累计、claimed 清空",
      first == (D1, {"kills": 2, "damage": 100, "tower": 1})
      and state["daily"]["date"] == D2
      and state["daily"]["base"] == {"kills": 5, "damage": 400, "tower": 3}
      and state["daily"]["claimed"] == [])

# ── 门禁2：跨周滚动（日界不动）──
daily.today, daily.this_week = (lambda: D2), (lambda: "2026-W02")
daily.touch(state)
d_after = (state["daily"]["date"], dict(state["daily"]["base"]))
check("2 跨周滚动：weekly 换周取新 base，daily 原样不动",
      state["weekly"]["week"] == "2026-W02"
      and state["weekly"]["base"] == {"kills": 5, "damage": 400, "tower": 3}
      and state["weekly"]["claimed"] == [] and d_after == (D2, {"kills": 5, "damage": 400, "tower": 3}))

# ── 门禁3：进度口径（差值 / 负数截断 / 上限截到 need）──
base_state = {"kills": {"a": 100, "lose:b": 9}, "total_damage": 0, "tower_best": 2,
              "daily": {"date": D2, "base": {"kills": 10, "damage": 0, "tower": 1}, "claimed": []},
              "weekly": {"week": "2026-W02", "base": {"kills": 0, "damage": 0, "tower": 0}, "claimed": []},
              "checkin": {"last": "", "streak": 0, "total": 0}}
rows = {r["key"]: r for r in daily.status(base_state, cfg)["daily"]}
neg = dict(base_state, daily={"date": D2, "base": {"kills": 500, "damage": 0, "tower": 9}, "claimed": []})
nrows = {r["key"]: r for r in daily.status(neg, cfg)["daily"]}
check("3 进度口径：lose: 不计、差值上限截到 need、负数截断为 0",
      rows["kills"]["cur"] == rows["kills"]["need"] == 8 and rows["tower"]["cur"] == 1
      and rows["damage"]["cur"] == 0 and nrows["kills"]["cur"] == 0 and nrows["tower"]["cur"] == 0)

# ── 门禁4：领取规则（金额精确 + 拒绝路径 + 其它字段零变化）──
st = {"kills": {"a": 8, "lose:b": 3}, "total_damage": 100, "tower_best": 0, "gold": 0,
      "level": 7, "protect": 0,
      "daily": {"date": D2, "base": {"kills": 0, "damage": 0, "tower": 0}, "claimed": []},
      "weekly": {"week": "2026-W02", "base": {"kills": 0, "damage": 10000, "tower": 0}, "claimed": []},
      "checkin": {"last": "", "streak": 0, "total": 0}}
a1, _ = daily.claim(st, cfg, "daily", "kills")
a2, _ = daily.claim(st, cfg, "daily", "kills")
a3, _ = daily.claim(st, cfg, "daily", "damage")
a4, _ = daily.claim(st, cfg, "daily", "level")
a5, _ = daily.claim(st, cfg, "weekly", "damage")
check("4 领取：达标 +40 金、重复/未达/未知拒绝、其它字段零变化",
      a1 and st["gold"] == 40 and st["daily"]["claimed"] == ["kills"]
      and not (a2 or a3 or a4 or a5) and st["gold"] == 40
      and st["level"] == 7 and st["protect"] == 0 and st["total_damage"] == 100)

# ── 门禁5：签到（同日拒绝 / 连签 / 断签重置 / 第 7 天保底符）──
daily.today = lambda: D1
ck = {"gold": 0, "protect": 0, "checkin": {"last": "", "streak": 0, "total": 0}}
b1, _ = daily.claim(ck, cfg, "checkin", "")
b2, _ = daily.claim(ck, cfg, "checkin", "")
daily.today = lambda: D2
b3, _ = daily.claim(ck, cfg, "checkin", "")
s3 = ck["checkin"]["streak"]
daily.today = lambda: "2026-01-05"
b4, _ = daily.claim(ck, cfg, "checkin", "")
s4 = ck["checkin"]["streak"]
daily.today = lambda: "2026-01-07"
ck["checkin"] = {"last": "2026-01-06", "streak": 6, "total": 10}
protect_before = ck["protect"]
b5, _ = daily.claim(ck, cfg, "checkin", "")
check("5 签到：同日拒绝、连签递增、断签重置为 1、第 7 天 +1 保底符",
      b1 and not b2 and s3 == 2 and s4 == 1 and b3 and b4 and b5
      and ck["protect"] == protect_before + 1
      and ck["checkin"]["streak"] == 7 and ck["checkin"]["total"] == 11)

# ── 门禁6：UI（offscreen 真窗口 + 领取写档）──
from PySide6.QtWidgets import QApplication

import qtfont

qapp = QApplication.instance() or QApplication([])
qtfont.ensure_cjk_font(qapp)
import gui_daily

TMP = "save_v29d2.json"
if os.path.exists(TMP):
    os.remove(TMP)
save.set_path(TMP)
daily.today, daily.this_week = (lambda: D2), (lambda: "2026-W02")
save.write_raw({"schema": save.SCHEMA, "level": 5, "gold": 0, "kills": {"a": 8},
                "total_damage": 0, "tower_best": 0,
                "daily": {"date": D2, "base": {"kills": 0, "damage": 0, "tower": 0}, "claimed": []},
                "weekly": {"week": "2026-W02", "base": {"kills": 0, "damage": 0, "tower": 0}, "claimed": []},
                "checkin": {"last": "", "streak": 0, "total": 0}})
w = gui_daily.DailyWindow(lambda: None)
w.refresh()
btn = w.btns[("daily", "kills")]
ready = btn.isEnabled() and "领取" in btn.text()
w.claim("daily", "kills")
after = json.load(open(TMP, encoding="utf-8"))
check("6 UI：达标可点、领取后金币 +40 且按钮变已领取、未达项禁用",
      ready and after["gold"] == 40 and "已领取" in btn.text() and not btn.isEnabled()
      and not w.btns[("daily", "damage")].isEnabled())

# ── 门禁7：v10→v11 迁移 + validate 十八项 ──
v10 = {"schema": 10, "level": 22, "exp": 33, "hp": 210, "mp": 90, "attack": 71, "next": 5,
       "week": 1, "playtime": 1234, "gold": 456, "difficulty": 1, "protect": 2,
       "tower_best": 17, "tower_layer": 3, "maps_cleared": 10, "total_damage": 8888,
       "staff_pity": 7, "achievements": ["clear_all"], "codex_weapons": ["金箍棒"],
       "kills": {"huoyao": 4}, "quest_flags": {"m1": "done"},
       "elite_kills": 4, "rare_kills": 2, "title": "clear_all",
       "records": {"best_dealt": 615, "best_dealt_mon": "白骨夫人", "best_rounds": 1, "best_rounds_mon": "小妖甲"}}
m = save._migrate(dict(v10))
kept = all(m.get(k) == v for k, v in v10.items() if k != "schema")
check("7 v10→v%d 迁移：D2 三字段就位且旧值一字未动" % save.SCHEMA,
      kept and m["schema"] == save.SCHEMA and m["daily"] == {"date": "", "base": {}, "claimed": []}
      and m["weekly"]["week"] == "" and m["checkin"] == {"last": "", "streak": 0, "total": 0})
rv = subprocess.run([WB, "validate.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("7b validate 十八项全绿", rv.returncode == 0 and rv.stdout.count("✓") == 18)
if rv.returncode:
    print(rv.stdout[-800:])

# ── 门禁8：行数纪律 + v20→v29d1 全链回归 ──
limits = {"daily.py": 110, "gui_daily.py": 120, "save.py": 145, "gui_hub.py": 65,
          "app.py": 140, "validate.py": 180, "engine.py": 225, "progress.py": 110,
          "gui_codex.py": 120, "tower.py": 100, "combat.py": 130, "encounter.py": 170}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items() if sum(1 for _ in open(f, encoding="utf-8")) > lim]
rr = subprocess.run([WB, "tests/smoke_v29d1.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("8 行数纪律 + v20→v29d1 全链回归",
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
