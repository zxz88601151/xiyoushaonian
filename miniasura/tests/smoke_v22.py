# V2.2 出口验收 · 自动化冒烟（DESIGN_V2_2.md §5 七门禁）
# 门禁：对话可跳可重看 / 任务状态机 / 十任务全通 / 隐藏任务真触发 / 商店闭环 / GM 三命令 / 回归
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


import dialogue
import quests
import save

# ── 门禁1 对话系统 ──
blocks = dialogue.load("[a]\n你好\n# 旁白一行\n[b]\n再见")
check("dialogue.load 分节+舞台指示", blocks["a"] == ["你好", "# 旁白一行"])
check("block_text 重看拼接", "旁白" in dialogue.block_text(blocks, "a"))


class ScriptIo:
    def __init__(self, rules):
        self.rules = rules

    def say(self, msg=""):
        pass

    def ask(self, prompt):
        for sub, ans in self.rules:
            if sub in prompt:
                return ans
        return "1"


check("看完→True / 跳过→False / 未知id→False",
      dialogue.play(ScriptIo([]), blocks, "a")
      and not dialogue.play(ScriptIo([("略过", "s")]), blocks, "a")
      and not dialogue.play(ScriptIo([]), blocks, "nope"))

# ── 门禁2 任务状态机（单测）──
T = quests.Tracker(quests.load(quests.load_pack_text()))
check("无前置任务开局即激活", T.state("m1") == "active" and T.state("m2") == "locked")
done = T.on_event("map", 2)
check("通图2→m1完成→m2激活", T.state("m1") == "done"
      and [q["key"] for q in done] == ["m1"] and T.state("m2") == "active"
      and T.state("s2") == "active")            # s2/s3 前置 m1
T.on_event("win", "xiaoyao2")
done = T.on_event("win", "xiaoyao2")
check("击杀计数达标注销 s1", T.state("s1") == "done")
T.on_event("talk", "d_map6")
check("看完对话→s3 完成", T.state("s3") == "done")
H = quests.Tracker(quests.load(quests.load_pack_text()))
H.on_event("lose", "xiaoyao1")
check("败给小怪不触发 h1", H.state("h1") == "active")   # hidden 开局即挂监听（Bug A 修复）
done = H.on_event("lose", "boss")
check("败给 boss 触发 h1（lose:boss:1）", H.state("h1") == "done")

# ── 门禁5 跳过路径：全跳对话 → talk 任务不推进（进程内真实跑一局）──
import engine
if os.path.exists("save.json"):
    os.remove("save.json")
engine.run_game(ScriptIo([("略过", "s")]))
after = json.load(open("save.json", encoding="utf-8"))
flags = after["quest_flags"]
check("跳过对话：主线全 done", all(flags.get(k) == "done" for k in
      ("m1", "m2", "m3", "m4", "m5", "m6")))
check("跳过对话：s2/s3 停在 active（不推进）",
      flags.get("s2") == "active" and flags.get("s3") == "active")
check("跳过对话：击杀型 s1 照常 done", flags.get("s1") == "done")
os.remove("save.json")

# ── 门禁3 主门禁：CLI 全通十任务（9 链任务 done；h1 需败北另行验证）──
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 400) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
check("CLI 全通：9 任务 done + 地图 10/10",
      r.stdout.count("[done]") == 9 and "地图推进 10/10" in r.stdout)
after = json.load(open("save.json", encoding="utf-8"))
check("通关档 schema4/week1/task完整", after["schema"] == save.SCHEMA
      and after["week"] == 1 and after["maps_cleared"] == 10)
os.remove("save.json")

# ── 门禁4 隐藏任务真触发：残血败给 boss → 死亡落盘 → h1 done ──
# 注意：next 与 maps_cleared 是两个游标，必须一致——maps_cleared=9 表示前 9 图已通，
# 第 10 图未完成；若写 0，引擎会把 1~10 图重放、任务奖励装备自动穿上，玩家反而赢。
save.write_raw({"schema": save.SCHEMA, "user": "", "level": 14, "exp": 0,
                "hp": 10, "mp": 100, "attack": 57, "next": 11, "week": 0,
                "playtime": 0, "maps_cleared": 9})
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 40) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
after = json.load(open("save.json", encoding="utf-8"))
check("败给 boss → h1 done（死亡落盘）", after["quest_flags"].get("h1") == "done"
      and after["hp"] > 0)
os.remove("save.json")

# ── 门禁6 商店闭环（GUI offscreen）──
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QMessageBox
qapp = QApplication.instance() or QApplication([])
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)

import gear
import gui_quests
import gui_shop

save.write_raw({"schema": save.SCHEMA, "user": "", "level": 14, "exp": 100, "gold": 100,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0,
                "playtime": 0, "inventory": [gear.generate("weapon", 5, 0)],
                "equipment": gear.empty_equipment()})
shop = gui_shop.ShopWindow(lambda: None, lambda: None)
shop.refresh()
shop.buy("hp_potion")
d = json.load(open("save.json", encoding="utf-8"))
check("买血瓶：金币 100→70、库存+1", d["gold"] == 70
      and d["potions"]["hp"] == 1)
shop.buy("mp_potion")
shop.buy("mp_potion")
shop.buy("mp_potion")
shop.buy("mp_potion")          # 第 4 次：70-20*3=10 < 20 → 应被拒
d = json.load(open("save.json", encoding="utf-8"))
check("金币不足拒购（fail-closed）", d["gold"] == 10 and d["potions"]["mp"] == 3)
shop.recycle_list.setCurrentRow(0)
shop.recycle()
d = json.load(open("save.json", encoding="utf-8"))
check("白装回收：装备消失、金币入账", len(d["inventory"]) == 0
      and d["gold"] == 10 + round((5 + 5 * 3) * 0.3))
os.remove("save.json")

# ── 门禁6b 任务窗：重看对话（只读）──
captured = []
QMessageBox.information = staticmethod(
    lambda *a, **k: captured.append(k or a) or QMessageBox.StandardButton.Ok)
save.write_raw({"schema": save.SCHEMA, "user": "", "level": 14, "exp": 0,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0,
                "playtime": 0})
qw = gui_quests.QuestWindow(lambda: None)
qw.refresh()
check("任务窗列出 10 个任务", qw.listw.count() == 10)
qw.listw.setCurrentRow(0)
qw.rewatch()
check("重看对话弹出内容（不推进任务）", captured
      and "仙石出世" in str(captured[0]))
os.remove("save.json")

# ── 门禁6c GM 三命令 + fail-closed（真会话真 CLI）──
import login
import slots
login.register("audit3", "pw")
login.start_session("audit3", "huaguoshan", 1)
path = slots.slot_path("huaguoshan", "audit3", 1)
save.set_path(path, "audit3")
save.write_raw({"schema": save.SCHEMA, "user": "audit3", "level": 14, "exp": 0,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0,
                "playtime": 0})
r = subprocess.run([WB, "gm.py", "quest", "m3"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm quest m3 → done", r.returncode == 0
      and d["quest_flags"].get("m3") == "done")
r = subprocess.run([WB, "gm.py", "quest", "haha"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("gm quest 未知key被拒", r.returncode == 1 and "未知任务" in r.stdout)
r = subprocess.run([WB, "gm.py", "map", "5"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm map 5", r.returncode == 0 and d["maps_cleared"] == 5)
r = subprocess.run([WB, "gm.py", "map", "11"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("gm map 越界被拒", r.returncode == 1 and "1-10" in r.stdout)
r = subprocess.run([WB, "gm.py", "potion", "hp", "3"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm potion hp 3", r.returncode == 0 and d["potions"]["hp"] == 3)
login.logout()
for f in ("accounts.json", "session.json"):
    if os.path.exists(f):
        os.remove(f)
save.set_path(os.path.join(HERE, "save.json"))

# ── 门禁5 行数纪律 ──
limits = {"engine.py": 220, "loot.py": 100, "dialogue.py": 80, "quests.py": 100,
          "combat.py": 130, "rewards.py": 60, "gui_shop.py": 200,
          "gui_quests.py": 200, "gui_bag.py": 200}
bad_lines = []
for f, lim in limits.items():
    n = sum(1 for _ in open(f, encoding="utf-8"))
    if n > lim:
        bad_lines.append(f"{f}={n}>{lim}")
check("行数纪律（engine≤200 等）", not bad_lines)
if bad_lines:
    print("  超标:", bad_lines)

# ── 门禁7 回归：V2.0/V2.1 冒烟 ──
r = subprocess.run([WB, "tests/smoke_v20.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("V2.0 冒烟回归", "全部通过" in r.stdout)
r = subprocess.run([WB, "tests/smoke_v21.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("V2.1 冒烟回归", "全部通过" in r.stdout)
if "失败" in r.stdout:
    print(r.stdout[-800:])

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]

# 终清理：回归冒烟会留下账号/会话/存档，恢复空白起点
import shutil as _sh
for _f in ("accounts.json", "session.json", "save.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh.rmtree("saves", ignore_errors=True)

print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
