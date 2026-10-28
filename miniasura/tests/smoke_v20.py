# V2.0 出口验收 · 自动化冒烟（QT_QPA_PLATFORM=offscreen 无人值守）
# 覆盖：门禁1 全链路 / 门禁2 v1 迁移 / 门禁3 fail-closed（GUI 侧）
import json
import os
import shutil
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["MINIASURA_AUTO"] = ",".join(["1"] * 120)   # 自动普攻+对话确认通关（V2.2 起 12 战+10 段对话）

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # miniasura/
sys.path.insert(0, HERE)
os.chdir(HERE)

# 入口自清理：本测试假设空白起点（重复跑/前次中断不残留脏状态）
for _f in ("accounts.json", "session.json", "save.json"):
    if os.path.exists(_f):
        os.remove(_f)
shutil.rmtree("saves", ignore_errors=True)

import login
import save
import slots
import engine

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name)


# ── 门禁3 fail-closed（账号层）──
check("空注册被拒", login.register("", "x") is not None)
check("首次注册成功", login.register("audit1", "pw") is None)
check("重名注册被拒", login.register("audit1", "pw2") is not None)
check("错密码被拒", login.login("audit1", "wrong") is not None)
check("正确登录通过", login.login("audit1", "pw") is None)

# ── 门禁1 全链路（GUI offscreen）──
from PySide6.QtWidgets import QApplication, QPushButton
import app as appmod

qapp = QApplication.instance() or QApplication([])
w = appmod.App()
check("无会话启动 → 登录窗", w.currentWidget() is w.login)

w.login.user.setText("audit1")
w.login.pwd.setText("pw")
w.login.do_login()
check("登录 → 选区窗", w.currentWidget() is w.server)

w.pick_server("huaguoshan")
check("选区 → 槽位窗", w.currentWidget() is w.slotsw)
check("会话已记录区服", login.get_session().get("server") == "huaguoshan")

w.pick_slot(1)
check("选槽 → 大厅", w.currentWidget() is w.hub)
check("存档路径已注入槽位1",
      save.PATH == slots.slot_path("huaguoshan", "audit1", 1))

w.to_battle()
t0 = time.time()
while w.battle.running and time.time() - t0 < 120:
    qapp.processEvents()
    time.sleep(0.02)
qapp.processEvents()
check("战斗窗自动打完整局", not w.battle.running)
data = json.load(open(save.PATH, encoding="utf-8"))
check("通关写档 schema4/week=1/next=全部战斗/user 注入",
      data.get("schema") == save.SCHEMA and data.get("week") == 1
      and data.get("next") == engine.total_fights() and data.get("user") == "audit1")

w.to_hub()
check("返回大厅", w.currentWidget() is w.hub)

w.slotsw.refresh()
texts = [b.text() for b in w.slotsw.findChildren(QPushButton)]
check("槽位预览出现 Lv.（存档被读到）", any("Lv." in t for t in texts))

# ── 门禁2 v1 → schema2 迁移（两种 cleared 形态）──
p2 = slots.slot_path("huaguoshan", "audit1", 2)
v1 = {"level": 16, "exp": 45, "hp": 100, "mp": 70, "attack": 63,
      "next": 2, "cleared": False}
json.dump(v1, open(p2, "w", encoding="utf-8"), ensure_ascii=False)
save.set_path(p2)
m = save.load()
check("v1 中断档迁移：数值不丢+week=0",
      m["schema"] == save.SCHEMA and m["level"] == 16 and m["exp"] == 45
      and m["next"] == 2 and m["week"] == 0 and m["playtime"] == 0)

v1c = dict(v1, cleared=True, next=4)
json.dump(v1c, open(p2, "w", encoding="utf-8"), ensure_ascii=False)
m = save.load()
check("v1 cleared 档迁移：cleared→week 1", m["week"] == 1 and m["next"] == 4)
os.remove(p2)
save.set_path(slots.slot_path("huaguoshan", "audit1", 1), "audit1")

# ── 会话恢复（模拟杀进程重开）──
w2 = appmod.App()
check("杀进程重开 → 会话恢复直回大厅", w2.currentWidget() is w2.hub)

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
