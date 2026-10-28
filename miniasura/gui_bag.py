# V2.1 背包/装备窗 + V2.2 仓库模式 —— 穿、卸、丢、仓库存取；只经 save 层落盘。
# 数值一律来自 gear 层（公式住 equip.lua），本窗不做任何算术。
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QListWidget,
                               QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
                               QWidget)

import gear
import save


class BagWindow(QWidget):
    def __init__(self, back, source="inventory"):
        super().__init__()
        self.back = back
        self.source = source          # "inventory"=背包 / "storage"=仓库（V2.2）
        self.data = None
        self.items = []               # 与列表框行号平行的物品引用

        self.equip_lab = []
        self.unequip_btn = []
        grid = QGridLayout()
        for i, s in enumerate(gear.SLOTS):
            lab = QLabel("（空）")
            btn = QPushButton("卸下")
            btn.clicked.connect(lambda _, sl=s: self.unequip(sl))
            grid.addWidget(QLabel(gear.SLOT_NAMES[s]), i, 0)
            grid.addWidget(lab, i, 1)
            grid.addWidget(btn, i, 2)
            self.equip_lab.append(lab)
            self.unequip_btn.append(btn)

        self.stats = QLabel()
        self.bag = QListWidget()
        self.bag.itemSelectionChanged.connect(self.show_details)
        self.cap_lab = QLabel()
        self.detail = QLabel()        # 选中物品的词条详情（终审 F6：内嵌展示）
        btn_main = QPushButton("装备选中" if source == "inventory" else "取回（进背包）")
        btn_main.clicked.connect(self.main_action)
        btn_store = QPushButton("存入仓库")
        btn_store.clicked.connect(self.transfer_out)
        btn_drop = QPushButton("丢弃选中")
        btn_drop.clicked.connect(self.drop)
        back = QPushButton("← 返回大厅")
        back.clicked.connect(self.go_back)

        left = QVBoxLayout()
        left.addWidget(QLabel("已穿戴"))
        left.addLayout(grid)
        left.addWidget(self.stats)
        left.addStretch()

        right = QVBoxLayout()
        right.addWidget(QLabel("仓库" if source == "storage" else "背包"))
        right.addWidget(self.bag)
        right.addWidget(self.detail)
        right.addWidget(self.cap_lab)
        right.addWidget(btn_main)
        if source == "inventory":
            right.addWidget(btn_store)
        right.addWidget(btn_drop)

        top = QHBoxLayout()
        top.addLayout(left)
        top.addLayout(right)
        lay = QVBoxLayout()
        lay.addLayout(top)
        lay.addWidget(back)
        self.setLayout(lay)

    def go_back(self):
        self.back()

    def _list(self):
        # 仓库模式操作 storage，背包模式操作 inventory（数据搬家不改逻辑）
        if self.source == "storage":
            return self.data.setdefault("storage", [])
        return self.data.setdefault("inventory", [])

    def refresh(self):
        self.data = save.load()
        if not self.data:
            self.stats.setText("（还没有存档——先进一场战斗创建角色）")
            self.cap_lab.setText("")
            self.bag.clear()
            return
        eq = self.data.get("equipment") or gear.empty_equipment()
        for i, s in enumerate(gear.SLOTS):
            it = eq.get(s)
            self.equip_lab[i].setText(gear.item_line(it) if it else "（空）")
            self.unequip_btn[i].setEnabled(bool(it) and self.source == "inventory")
        tot = gear.totals(eq)
        self.stats.setText(
            f"装备加成合计：攻击+{tot['atk']:.1f}  HP+{tot['hp']:.0f}  "
            f"防御+{tot['def']:.1f}\n暴击率+{tot['crit']:.1f}%  暴伤+{tot['critdmg']:.0f}%  "
            f"吸血+{tot['leech']:.1f}%  经验+{tot['exp']:.1f}%")
        self.items = self._list()
        self.bag.clear()
        for it in self.items:
            self.bag.addItem(gear.item_line(it))
        self.cap_lab.setText(f"容量 {len(self.items)}/{gear.capacity()}")
        self.detail.setText("（选中物品查看词条详情）")

    def show_details(self):
        row = self.bag.currentRow()
        if 0 <= row < len(self.items):
            it = self.items[row]
            lines = [gear.item_line(it)]
            for a in it["affixes"]:
                lines.append(f"  · {a['name']} +{a['val']:.2f}")
            self.detail.setText("\n".join(lines))

    def main_action(self):
        if self.source == "storage":
            self.take_back()
        else:
            self.equip()

    def equip(self):
        row = self.bag.currentRow()
        if not (0 <= row < len(self.items)):
            return
        it = self.items[row]
        slot = gear.SLOTS[it["slot"]]
        old = self.data["equipment"].get(slot)
        inv = self._list()
        if old and len(inv) >= gear.capacity():
            QMessageBox.warning(self, "背包已满",
                                f"卸下的旧装备放不进背包（容量 {gear.capacity()}）")
            return
        self.data["equipment"][slot] = it
        inv.remove(it)
        if old:
            inv.append(old)
        save.write_raw(self.data)
        self.refresh()

    def unequip(self, slot):
        it = self.data["equipment"].get(slot)
        if not it:
            return
        inv = self._list()
        if len(inv) >= gear.capacity():
            QMessageBox.warning(self, "背包已满",
                                f"背包放不下了（容量 {gear.capacity()}）")
            return
        self.data["equipment"][slot] = None
        inv.append(it)
        save.write_raw(self.data)
        self.refresh()

    def take_back(self):
        """仓库 → 背包（容量校验 fail-closed）。"""
        row = self.bag.currentRow()
        if not (0 <= row < len(self.items)):
            return
        if len(self.data.get("inventory", [])) >= gear.capacity():
            QMessageBox.warning(self, "背包已满",
                                f"背包放不下了（容量 {gear.capacity()}）——先丢一件")
            return
        it = self._list().pop(row)
        self.data["inventory"].append(it)
        save.write_raw(self.data)
        self.refresh()

    def transfer_out(self):
        """背包 → 仓库（容量校验 fail-closed）。"""
        row = self.bag.currentRow()
        if not (0 <= row < len(self.items)):
            return
        if len(self.data.get("storage", [])) >= gear.capacity():
            QMessageBox.warning(self, "仓库已满",
                                f"仓库放不下了（容量 {gear.capacity()}）")
            return
        it = self._list().pop(row)
        self.data.setdefault("storage", []).append(it)
        save.write_raw(self.data)
        self.refresh()

    def drop(self):
        row = self.bag.currentRow()
        if not (0 <= row < len(self.items)):
            return
        it = self.items[row]
        if QMessageBox.question(self, "确认丢弃",
                                f"丢弃 {gear.item_line(it)}？不可恢复！") != QMessageBox.Yes:
            return
        self._list().remove(it)
        save.write_raw(self.data)
        self.refresh()
