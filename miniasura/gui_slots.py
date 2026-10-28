# V2.0 选区窗 + 存档槽窗（伪区服 = 本地目录分组，纯数据）。
import os

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

import login
import slots

HERE = os.path.dirname(os.path.abspath(__file__))


def load_servers():
    with open(os.path.join(HERE, "servers.txt"), encoding="utf-8") as f:
        return [line.strip().split("|") for line in f if line.strip()]


class ServerWindow(QWidget):
    def __init__(self, pick):
        super().__init__()
        lay = QVBoxLayout()
        lay.addWidget(QLabel("选择区服（伪区服 = 本地存档分组，永不联网）"))
        for sid, name in load_servers():
            b = QPushButton(name)
            b.clicked.connect(lambda _, s=sid: pick(s))
            lay.addWidget(b)
        self.setLayout(lay)


class SlotsWindow(QWidget):
    def __init__(self, enter, go_server):
        super().__init__()
        self.enter = enter
        self.lay = QVBoxLayout()
        back = QPushButton("← 换个区服")
        back.clicked.connect(go_server)
        self.lay.addWidget(QLabel("选择存档槽"))
        self.lay.addStretch()
        outer = QVBoxLayout()
        outer.addLayout(self.lay)
        outer.addWidget(back)
        self.setLayout(outer)

    def refresh(self):
        # 清掉除标题/stretch 之外的旧行再重画
        while self.lay.count() > 2:
            item = self.lay.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
        sess = login.get_session()
        for row in slots.list_slots(sess["server"], sess["user"]):
            if row["exists"]:
                text = (f"槽位 {row['slot']}：Lv.{row['level']}  "
                        f"第 {row['week'] + 1} 周目  进度 第 {row['next'] + 1} 战  "
                        f"时长 {row['playtime']} 秒")
            else:
                text = f"槽位 {row['slot']}：空"
            line = QHBoxLayout()
            b = QPushButton(text)
            b.clicked.connect(lambda _, s=row["slot"]: self.enter(s))
            line.addWidget(b)
            if row["exists"]:
                del_b = QPushButton("删除")
                del_b.clicked.connect(lambda _, s=row["slot"]: self.remove(s))
                line.addWidget(del_b)
            wrap = QWidget()
            wrap.setLayout(line)
            self.lay.insertWidget(self.lay.count() - 1, wrap)

    def remove(self, slot):
        if QMessageBox.question(self, "确认", "删除该存档？不可恢复！") == QMessageBox.Yes:
            sess = login.get_session()
            slots.delete_slot(sess["server"], sess["user"], slot)
            self.refresh()
