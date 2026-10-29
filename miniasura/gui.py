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
import gui_report
import skills

AUTO = [x for x in os.environ.get("MINIASURA_AUTO", "").split(",") if x]
SHOT = os.environ.get("MINIASURA_SHOT", "")


class Bridge(QObject):
    said = Signal(str)
    asked = Signal(str)
    reported = Signal(dict, str)   # V2.9-C：战报富通道（结构化 rep + 日志原文）
    finished = Signal()


class GuiIo:
    # 与 CliIo 同款 say/ask 接口——引擎认接口不认实现，这就是注入
    def __init__(self, bridge, answers):
        self.bridge = bridge
        self.answers = answers

    def say(self, msg=""):
        self.bridge.said.emit(msg)

    def report(self, rep, line):
        self.bridge.reported.emit(rep, line)   # V2.9-C：显眼通道（战报卡）
        self.say(line)                          # D3：日志仍保留完整原文，不丢记录

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
        self.card = gui_report.ReportCard()   # V2.9-C：常驻战报卡（放日志上方，滚动不带走）
        self.prompt = QLabel("……")

        # 2026-10-28 逃跑补丁：战斗按钮补“物品(4)”（之前 CLI 有、GUI 没有，
        # 玩家在窗口里根本喝不了药）；技能按钮用 skills.txt 的真名，读不到才回退。
        self.act_row, self.act_btns = self.make_row(
            (("普攻(1)", "1"), ("技能(2)", "2"), ("逃跑(3)", "3"), ("物品(4)", "4")))
        try:
            # V2.7：技能按钮动态生成（全部主动技能，顺序与 skills.choose 菜单一致 = skills.txt 行序）
            _acts = [s for s in skills.load_skills().values() if s["kind"] == "active"]
            _names = [s["name"] for s in _acts]
        except Exception:
            _names = []
        while len(_names) < 3:
            _names.append("技能%d" % (len(_names) + 1))
        self.sk_row, self.sk_btns = self.make_row(
            tuple(("%s(%d)" % (n, i + 1), str(i + 1)) for i, n in enumerate(_names)))
        # 对话 / 药水各给一排专按钮：之前这两类提示也亮着战斗按钮，
        # 点“普攻”会被对话当成“看完”、被药水当成“血瓶”，容易误触。
        self.dia_row, self.dia_btns = self.make_row(
            (("继续", ""), ("略过(s)", "s")))
        self.pot_row, self.pot_btns = self.make_row(
            (("血瓶(1)", "1"), ("蓝瓶(2)", "2"), ("取消", "x")))
        # V2.3 难度：新档/新周目开局问一次，专排按钮与对话/药水同机制。
        self.diff_row, self.diff_btns = self.make_row(
            (("普通(1)", "1"), ("精英(2)", "2"), ("噩梦(3)", "3")))

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
        side.addLayout(self.dia_row)
        side.addLayout(self.pot_row)
        side.addLayout(self.diff_row)
        side.addWidget(self.entry)
        side.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(self.card)
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
        # skill=True 保留旧调用兼容；新分流走 _set_mode。
        self._set_mode(on, "skill" if skill else "act")

    def _set_mode(self, on, mode):
        rows = {"act": self.act_btns, "skill": self.sk_btns,
                "dialogue": self.dia_btns, "potion": self.pot_btns,
                "difficulty": self.diff_btns}
        for name, btns in rows.items():
            for b in btns:
                b.setEnabled(bool(on) and name == mode)

    def begin(self, wipe=False):
        if wipe and os.path.exists(engine.save.PATH):
            os.remove(engine.save.PATH)
        self.log.clear()
        self.card.reset()
        self.running = True
        self.answers = queue.Queue()
        bridge = Bridge()
        bridge.said.connect(self.log.appendPlainText)
        bridge.reported.connect(self.card.show_report)
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
        # 按提示词分流按钮排：只亮当前问题对应的那一排，其他排全暗。
        if "选技能" in prompt:
            mode = "skill"
        elif "略过" in prompt:
            mode = "dialogue"
        elif "用什么" in prompt:
            mode = "potion"
        elif "选择难度" in prompt:
            mode = "difficulty"
        else:
            mode = "act"
        self.prompt.setText(prompt)
        self._set_mode(True, mode)
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
