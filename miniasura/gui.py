# MiniAsura 战斗窗（V2.0：由 v1.2 主窗口降级为 app.py 路由中的一员）
# 引擎在后台线程跑：say 走信号刷日志，ask 阻塞在队列上等界面把答案塞进来
# （环境钩子 MINIASURA_AUTO / MINIASURA_SHOT 仅供无人值守冒烟测试）
import os
import queue
import sys
import threading

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QVBoxLayout, QWidget)

import engine

AUTO = [x for x in os.environ.get("MINIASURA_AUTO", "").split(",") if x]
SHOT = os.environ.get("MINIASURA_SHOT", "")


class Bridge(QObject):
    said = Signal(str)
    asked = Signal(str)
    finished = Signal()


class GuiIo:
    # 与 CliIo 同款 say/ask 接口——引擎认接口不认实现，这就是注入
    def __init__(self, bridge, answers):
        self.bridge = bridge
        self.answers = answers

    def say(self, msg=""):
        self.bridge.said.emit(msg)

    def ask(self, prompt):
        self.bridge.asked.emit(prompt)
        return self.answers.get()


class BattleWidget(QWidget):
    back_to_hub = Signal()

    def __init__(self):
        super().__init__()
        self.running = False
        self.answers = None

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.prompt = QLabel("……")

        self.act_row, self.act_btns = self.make_row(
            (("普攻(1)", "1"), ("技能(2)", "2"), ("逃跑(3)", "3")))
        self.sk_row, self.sk_btns = self.make_row(
            (("技能1", "1"), ("技能2", "2"), ("技能3", "3")))

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("输入数字后回车也可以")
        self.entry.returnPressed.connect(self.send_entry)

        restart = QPushButton("重开（删除存档）")
        restart.clicked.connect(self.restart)
        back = QPushButton("返回大厅")
        back.clicked.connect(self.back_to_hub.emit)

        side = QVBoxLayout()
        side.addWidget(restart)
        side.addWidget(back)
        side.addLayout(self.act_row)
        side.addLayout(self.sk_row)
        side.addWidget(self.entry)
        side.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(self.log)
        layout.addWidget(self.prompt)
        top = QWidget()
        top.setLayout(side)
        layout.addWidget(top)
        self.setLayout(layout)

        self.set_buttons(False)

    def make_row(self, defs):
        row, btns = QHBoxLayout(), []
        for text, cmd in defs:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, c=cmd: self.answer(c))
            row.addWidget(btn)
            btns.append(btn)
        return row, btns

    def set_buttons(self, on, skill=False):
        for b in self.act_btns:
            b.setEnabled(on and not skill)
        for b in self.sk_btns:
            b.setEnabled(on and skill)

    def begin(self, wipe=False):
        if wipe and os.path.exists(engine.save.PATH):
            os.remove(engine.save.PATH)
        self.log.clear()
        self.running = True
        self.answers = queue.Queue()
        bridge = Bridge()
        bridge.said.connect(self.log.appendPlainText)
        bridge.asked.connect(self.on_ask)
        bridge.finished.connect(self.on_done)
        threading.Thread(target=self.work, args=(bridge, self.answers),
                         daemon=True).start()

    def restart(self):
        self.begin(wipe=True)

    def work(self, bridge, answers):
        try:
            engine.run_game(GuiIo(bridge, answers))
        finally:
            bridge.finished.emit()

    def on_ask(self, prompt):
        skill = "选技能" in prompt
        self.prompt.setText(prompt)
        self.set_buttons(True, skill)
        if AUTO:
            item = AUTO.pop(0)
            QTimer.singleShot(50, lambda: self.answer(item))

    def on_done(self):
        self.running = False
        self.prompt.setText("（本局结束——点「重开」再来，或返回大厅）")
        self.set_buttons(False)
        if SHOT:
            self.grab().save(SHOT)
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()

    def answer(self, item):
        if not self.running:
            return
        self.prompt.setText("……")
        self.set_buttons(False)
        self.answers.put(item)

    def send_entry(self):
        self.answer(self.entry.text().strip())


def main():  # 独立运行 = 直接进战斗窗（dev 快捷通道，走默认存档路径）
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = BattleWidget()
    win.show()
    win.begin()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
