# V2.9-C 出口验收 · 八门禁（DESIGN_V2_9_C §5）
# io.report 富通道 / CLI 回退不变 / 日志不丢 / 战报卡数字 / reset / 两窗接入 / GUI 实跑 / 行数与全链回归。
import inspect
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["MINIASURA_AUTO"] = ",".join(["1"] * 220)   # 自动普攻+对话确认，与 v20 同机制
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "MINIASURA_AUTO": ""}

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name, flush=True)


import encounter

REP1 = {"rounds": 3, "dealt": 146, "taken": 21, "crits": 0, "misses": 1}
REP2 = {"rounds": 1, "dealt": 224, "taken": 0, "crits": 1, "misses": 0}
LINE1 = "战报：3回合 / 造成146伤害 / 承受21伤害 / 暴击0次 / MISS 1次"


class SayIo:
    def __init__(self):
        self.lines = []

    def say(self, msg=""):
        self.lines.append(msg)

    def ask(self, prompt):
        return "1"


# ── 门禁1：CLI 回退（无 report 的 io 必须逐字节不变）──
io_cli = SayIo()
encounter.print_report(io_cli, REP1)
check("1 CLI 回退：无 report 的 io 走 say 且文本不变", io_cli.lines == [LINE1])


# ── 门禁2：富通道（有 report 时只走 report，不重复 say）──
class RichIo(SayIo):
    def __init__(self):
        super().__init__()
        self.got = []

    def report(self, rep, line):
        self.got.append((dict(rep), line))


io_rich = RichIo()
encounter.print_report(io_rich, REP1)
check("2 富通道：有 report 时命中一次且不走 say",
      len(io_rich.got) == 1 and io_rich.got[0] == (REP1, LINE1) and io_rich.lines == [])
io_none = SayIo()
encounter.print_report(io_none, {})
check("2b 空 rep 不打印（语义不变）", io_none.lines == [])

# ── 门禁3：GuiIo.report 同时走富通道与日志（D3）──
from PySide6.QtWidgets import QApplication

import qtfont

qapp = QApplication.instance() or QApplication([])
qtfont.ensure_cjk_font(qapp)          # offscreen 下字体库为空，中文会变方框

import gui
import gui_report
import gui_tower
import save
import tower

b = gui.Bridge()
seen, said = [], []
b.reported.connect(lambda rep, line: seen.append((dict(rep), line)))
b.said.connect(said.append)
gui.GuiIo(b, None).report(REP1, LINE1)
check("3 日志不丢：GuiIo.report 既发富通道也把原文写日志",
      seen == [(REP1, LINE1)] and said == [LINE1])

bt = gui_tower.Bridge()
seen_t = []
bt.reported.connect(lambda rep, line: seen_t.append((dict(rep), line)))
gui_tower.GuiIo(bt, None).report(REP1, LINE1)
check("3b 爬塔 GuiIo 同构", seen_t == [(REP1, LINE1)])

# ── 门禁4：战报卡数字与累计 ──
card = gui_report.ReportCard()
card.show_report(REP1, LINE1)
card.show_report(REP2, "战报：1回合 / …")
t, d = card.title.text(), card.detail.text()
check("4 卡片：本场取第二场、累计为两场之和",
      "最近一场战报" in t and "1 回合" in t and "224" in t
      and "2 场" in d and "370" in d and "21" in d)

# ── 门禁5：reset 回空态且累计归零 ──
card.reset()
check("5 reset：空态文案 + 累计归零",
      card.title.text() == "（还没有战报）" and all(v == 0 for v in card.total.values()))

# ── 门禁6：两窗接入（结构 + 接线）──
bw = gui.BattleWidget()
tw = gui_tower.TowerWindow(lambda: None)
wired = ("reported.connect(self.card.show_report)" in inspect.getsource(gui.BattleWidget.begin)
         and "reported.connect(self.card.show_report)" in inspect.getsource(gui_tower.TowerWindow.fight))
check("6 两窗均有战报卡且桥接已连",
      isinstance(bw.card, gui_report.ReportCard) and isinstance(tw.card, gui_report.ReportCard) and wired)

# ── 门禁7：GUI 实跑（AUTO 全通）──
TMP = "save_v29c.json"
if os.path.exists(TMP):
    os.remove(TMP)
save.set_path(TMP)
w = gui.BattleWidget()
w.begin()
t0 = time.time()
while w.running and time.time() - t0 < 180:
    qapp.processEvents()
    time.sleep(0.01)
qapp.processEvents()
log_text = w.log.toPlainText()
runs = w.card.total.get("fights", 0)
check("7 GUI 实跑：12 场全部进卡片，日志仍 12 条战报",
      not w.running and runs == 12 and log_text.count("战报：") == 12
      and "最近一场战报" in w.card.title.text())
if runs != 12 or log_text.count("战报：") != 12:
    print("  实跑诊断: fights=%s 战报行=%d" % (runs, log_text.count("战报：")))
    print("  卡片:", w.card.title.text(), "|", w.card.detail.text())
if os.path.exists(TMP):
    os.remove(TMP)

# ── 门禁8：行数纪律 + validate 十六项 + smoke_v29b 全链 ──
limits = {"encounter.py": 170, "gui.py": 210, "gui_tower.py": 200, "gui_report.py": 60,
          "combat.py": 130, "engine.py": 222, "tower.py": 100, "validate.py": 165}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items() if sum(1 for _ in open(f, encoding="utf-8")) > lim]
rv = subprocess.run([WB, "validate.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
rr = subprocess.run([WB, "tests/smoke_v29b.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("8 行数纪律 + validate 十六项 + v20→v29b 全链回归",
      not bad_lines and rv.returncode == 0 and rv.stdout.count("✓") == 16
      and rr.returncode == 0 and "全部通过" in rr.stdout and rr.stdout.count("✗") == 0)
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
