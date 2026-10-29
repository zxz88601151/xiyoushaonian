# V2.5 无底洞爬塔窗 —— 一层一层打（点一次打一层），战斗交互仍走 io 抽象。
# 与 gui.py 战斗窗同机制：后台线程跑 tower.run_one，say 走信号刷日志，ask 阻塞在队列等按钮。
import queue
import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QVBoxLayout, QWidget)

import engine
import save
import tower


class Bridge(QObject):
    said = Signal(str)
    asked = Signal(str)
    finished = Signal()


class GuiIo:
    # 与 CliIo 同款 say/ask 接口——tower/combat 认接口不认实现
    def __init__(self, bridge, answers):
        self.bridge = bridge
        self.answers = answers

    def say(self, msg=""):
        self.bridge.said.emit(msg)

    def ask(self, prompt):
        self.bridge.asked.emit(prompt)
        return self.answers.get()


class TowerWindow(QWidget):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.data = None
        self.running = False
        self.answers = None
        self.cfg = tower.load_cfg()

        self.info = QLabel()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.prompt = QLabel("……")
        self.act_row, self.act_btns = self.make_row(
            (("普攻(1)", "1"), ("技能(2)", "2"), ("逃跑(3)", "3"), ("物品(4)", "4")))
        try:
            names = [v[0] for v in engine.parse_kv(engine.load_texts()["skills.txt"]).values()]
        except Exception:
            names = []
        while len(names) < 3:
            names.append("技能%d" % (len(names) + 1))
        self.sk_row, self.sk_btns = self.make_row(
            tuple(("%s(%d)" % (n, i + 1), str(i + 1)) for i, n in enumerate(names[:3])))
        self.pot_row, self.pot_btns = self.make_row(
            (("血瓶(1)", "1"), ("蓝瓶(2)", "2"), ("取消", "x")))
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("输入数字后回车也可以")
        self.entry.returnPressed.connect(self.send_entry)
        self.fight_btn = QPushButton("挑战下一层")
        self.fight_btn.clicked.connect(self.fight)
        self.leave_btn = QPushButton("撤离（本次层数清零）")
        self.leave_btn.clicked.connect(self.leave)
        back_btn = QPushButton("← 返回大厅")
        back_btn.clicked.connect(self.back)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("无底洞（层数即怪物等级）"))
        lay.addWidget(self.info)
        lay.addWidget(self.log)
        lay.addWidget(self.prompt)
        lay.addLayout(self.act_row)
        lay.addLayout(self.sk_row)
        lay.addLayout(self.pot_row)
        lay.addWidget(self.entry)
        lay.addWidget(self.fight_btn)
        lay.addWidget(self.leave_btn)
        lay.addWidget(back_btn)
        self.setLayout(lay)
        self.set_buttons(False)

    def make_row(self, defs):
        row, btns = QHBoxLayout(), []
        for text, cmd in defs:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, c=cmd: self.answer(c))
            row.addWidget(btn)
            btns.append(btn)
        return row, btns

    def set_buttons(self, on, mode="act"):
        rows = {"act": self.act_btns, "skill": self.sk_btns, "potion": self.pot_btns}
        for name, btns in rows.items():
            for b in btns:
                b.setEnabled(bool(on) and name == mode)

    def refresh(self):
        self.data = save.load()
        best = (self.data or {}).get("tower_best", 0)
        layer = (self.data or {}).get("tower_layer", 0)
        if not self.data:
            self.info.setText("（还没有存档——先进一场战斗创建角色）")
        elif not tower.unlocked(self.data):
            self.info.setText("无底洞尚未解锁：通关一次（第 1 周目完结）后才会出现入口。")
        else:
            self.info.setText(f"历史最高 {best} 层   本次所在 {layer} 层"
                              f"   下一层怪物等级 {layer + 1}")
        self.fight_btn.setEnabled(bool(self.data) and tower.unlocked(self.data))
        self.leave_btn.setEnabled(bool(self.data) and tower.unlocked(self.data))

    def fight(self):
        if not self.data or self.running:
            return
        self.running = True
        self.answers = queue.Queue()
        bridge = Bridge()
        bridge.said.connect(self.log.appendPlainText)
        bridge.asked.connect(self.on_ask)
        bridge.finished.connect(self.on_done)
        threading.Thread(target=self.work, args=(bridge, self.answers), daemon=True).start()

    def work(self, bridge, answers):
        try:
            skills = engine.parse_kv(engine.load_texts()["skills.txt"])
            player = tower.load_player(self.cfg, self.data)
            storage = self.data.setdefault("storage", [])
            tower.run_one(self.cfg, skills, player, storage, GuiIo(bridge, answers))
            tower.persist(self.data, player, storage)
        finally:
            bridge.finished.emit()

    def leave(self):
        if not self.data:
            return
        self.data["tower_layer"] = 0            # 撤离：本次层数清零，历史最高保留
        save.write_raw(self.data)
        self.log.appendPlainText("你撤回了洞口，本次层数清零（历史最高层保留）。")
        self.refresh()

    def on_ask(self, prompt):
        mode = "skill" if "选技能" in prompt else "potion" if "用什么" in prompt else "act"
        self.prompt.setText(prompt)
        self.set_buttons(True, mode)

    def on_done(self):
        self.running = False
        self.prompt.setText("（本层结束——点「挑战下一层」继续，或撤离回大厅）")
        self.set_buttons(False)
        self.refresh()

    def answer(self, item):
        if not self.running:
            return
        self.prompt.setText("……")
        self.set_buttons(False)
        self.answers.put(item)

    def send_entry(self):
        self.answer(self.entry.text().strip())
