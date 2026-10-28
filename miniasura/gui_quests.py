# V2.2 任务窗 —— 状态一览 + 对话重看（只读展示，重看不推进任何任务）。
import os
import sys

from PySide6.QtWidgets import (QLabel, QListWidget, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

import dialogue
import quests
import save

STATE_NAMES = {"locked": "未解锁", "active": "进行中", "done": "已完成"}


class QuestWindow(QWidget):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.rows = []                       # 与列表行号平行的任务引用
        self.states = {}                     # key → locked/active/done（refresh 时刷新）
        pack = os.path.join(HERE, "assets.mpak")
        self.blocks = dialogue.load(
            mypack.read(pack, "dialogue.txt").decode("utf-8"))

        self.listw = QListWidget()
        self.tip = QLabel("（选中任务后可重看其对话——重看不推进任务）")
        btn = QPushButton("重看对话")
        btn.clicked.connect(self.rewatch)
        back_btn = QPushButton("← 返回大厅")
        back_btn.clicked.connect(self.back)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("任务"))
        lay.addWidget(self.listw)
        lay.addWidget(self.tip)
        lay.addWidget(btn)
        lay.addWidget(back_btn)
        self.setLayout(lay)

    def refresh(self):
        self.rows = quests.load(quests.load_pack_text())
        data = save.load()
        flags = (data or {}).get("quest_flags", {})
        kills = (data or {}).get("kills", {})
        tracker = quests.Tracker(self.rows, flags, kills)
        self.listw.clear()
        self.states = {}
        for q in self.rows:
            st = tracker.state(q["key"])
            self.states[q["key"]] = st
            if q["type"] == "hidden" and st != "done":
                # 隐藏任务防剧透：未完成前不露名称与触发条件
                self.listw.addItem("🔒 ???  [隐藏任务]")
                continue
            mark = {"locked": "🔒", "active": "▶", "done": "✔"}[st]
            self.listw.addItem(f"{mark} {q['name']}  "
                               f"[{STATE_NAMES[st]}]  {q['reward']}")

    def rewatch(self):
        row = self.listw.currentRow()
        if not (0 <= row < len(self.rows)):
            return
        q = self.rows[row]
        if q["type"] == "hidden" and self.states.get(q["key"]) != "done":
            QMessageBox.information(self, "隐藏任务", "（完成后才能重看这段对话）")
            return
        if q["dialogue"] == "-":
            QMessageBox.information(self, q["name"], "（这个任务没有专属对话）")
            return
        QMessageBox.information(self, q["name"],
                                dialogue.block_text(self.blocks, q["dialogue"]))
