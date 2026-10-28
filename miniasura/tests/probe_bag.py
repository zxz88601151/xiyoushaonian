# V2.1 视觉探针 —— 预置会话+带装备存档，程序化进入背包窗截图（windows 平台，中文可读）
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)

import gear
import login
import save
import slots
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

rows = gear.load_affixes()
login.register("probe", "pw")
login.start_session("probe", "huaguoshan", 1)
path = slots.slot_path("huaguoshan", "probe", 1)
save.set_path(path, "probe")
w = gear.generate("weapon", 15, 2, rows, random.Random(7))
a = gear.generate("armor", 14, 1, rows, random.Random(3))
b = gear.generate("helm", 16, 2, rows, random.Random(11))
save.write_raw({"schema": 3, "user": "probe", "level": 14, "exp": 0,
                "hp": 150, "mp": 100, "attack": 57, "next": 0, "week": 0,
                "playtime": 0, "inventory": [a, b],
                "equipment": {**gear.empty_equipment(), "weapon": w}})

import app as appmod
qapp = QApplication(sys.argv)
win = appmod.App()
win.show()
shot = os.path.join(HERE, "gui_bag_20261028.png")


def step():
    win.to_bag()                      # 大厅 → 背包
    QTimer.singleShot(400, snap)


def snap():
    win.grab().save(shot)
    qapp.quit()


QTimer.singleShot(400, step)
qapp.exec()
print("截图:", shot, os.path.getsize(shot), "bytes")
