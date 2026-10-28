# V2.4 铁匠窗 —— 强化入口。只调 enhance 核心，不自己算概率与费用。
# 列表 = 背包 + 已穿戴（穿戴中也能直接强化，不用先卸下再穿回）。
import os
import sys

from PySide6.QtWidgets import (QCheckBox, QLabel, QListWidget, QListWidgetItem,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))

import enhance
import gear
import save


class EnhanceWindow(QWidget):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.items = []                      # (来源, 引用) 与列表行号平行
        self.data = None
        self.info = QLabel()
        self.gold_lab = QLabel()
        self.listw = QListWidget()
        self.listw.currentRowChanged.connect(lambda _: self._update_info())
        self.use_protect = QCheckBox("使用保底符（失败时保级，成功不消耗）")
        btn = QPushButton("强化选中装备")
        btn.clicked.connect(self.do_enhance)
        back_btn = QPushButton("← 返回大厅")
        back_btn.clicked.connect(self.back)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("铁匠（强化 +1~+10）"))
        lay.addWidget(self.gold_lab)
        lay.addWidget(self.listw)
        lay.addWidget(self.info)
        lay.addWidget(self.use_protect)
        lay.addWidget(btn)
        lay.addWidget(back_btn)
        self.setLayout(lay)

    def refresh(self):
        self.data = save.load()
        self.items = []
        self.listw.clear()
        if not self.data:
            self.gold_lab.setText("（还没有存档——先进一场战斗创建角色）")
            self.info.setText("")
            return
        gold = self.data.get("gold", 0)
        protect = self.data.get("protect", 0)
        self.gold_lab.setText(f"金币：{gold}   保底符：{protect} 张（商店 100 金币一张）")
        for it in self.data.get("inventory", []):
            self.items.append(("inventory", it))
            self.listw.addItem(f"[背包] {gear.item_line(it)}")
        for slot, it in (self.data.get("equipment") or {}).items():
            if it:
                self.items.append(("equipment", it))
                self.listw.addItem(f"[已穿戴·{gear.SLOT_NAMES[slot]}] {gear.item_line(it)}")
        self._update_info()

    def _update_info(self):
        row = self.listw.currentRow()
        if not (0 <= row < len(self.items)):
            self.info.setText("（先选一件装备）")
            return
        it = self.items[row][1]
        enh = it.get("enh", 0)
        if enh >= enhance.MAX_ENH:
            self.info.setText(f"{gear.item_line(it)} —— 已 +10，到顶了。")
        else:
            self.info.setText(f"{gear.item_line(it)} —— 下一级费用 {enhance.cost(it)} 金币，"
                              f"成功率 {enhance.success_rate(it)}%（+7 起失败降级）")

    def do_enhance(self):
        row = self.listw.currentRow()
        if not (0 <= row < len(self.items)) or not self.data:
            return
        it = self.items[row][1]
        gold = self.data.get("gold", 0)
        protect = self.data.get("protect", 0)
        ok, gold, protect, msg = enhance.enhance(
            it, gold, protect, self.use_protect.isChecked())
        self.data["gold"] = gold
        self.data["protect"] = protect
        save.write_raw(self.data)
        QMessageBox.information(self, "强化成功" if ok else "强化结果", msg)
        self.refresh()
