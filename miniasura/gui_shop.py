# V2.2 商店窗 —— 买药 + 白装回收 + 仓库入口。
# 货币临时用经验点（金币经济 V2.3 上线切换）；价目/回收参数全在数据层，本窗不做算术外的事。
import configparser
import os
import sys

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

import gear
import save


def load_shop():
    text = mypack.read(os.path.join(HERE, "assets.mpak"), "shop.txt").decode("utf-8")
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, name, price = line.split("|")
        rows.append({"key": key, "name": name, "price": int(price)})
    return rows


def recycle_value(item):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    base = cfg.getint("shop", "recycle_base")
    per = cfg.getint("shop", "recycle_per_lv")
    pct = cfg.getint("shop", "recycle_pct")
    return round((base + item["lv"] * per) * pct / 100)


class ShopWindow(QWidget):
    def __init__(self, back, go_storage):
        super().__init__()
        self.back = back
        self.go_storage = go_storage
        self.data = None
        self.whites = []                     # 与回收列表行号平行

        self.currency = QLabel()
        self.pot_lab = QLabel()
        buy_row = QHBoxLayout()
        for r in load_shop():
            btn = QPushButton(f"买 {r['name']}（{r['price']} 经验）")
            btn.clicked.connect(lambda _, k=r["key"]: self.buy(k))
            buy_row.addWidget(btn)

        self.recycle_list = QListWidget()
        btn_recycle = QPushButton("回收选中白装（折经验）")
        btn_recycle.clicked.connect(self.recycle)
        btn_storage = QPushButton("打开仓库")
        btn_storage.clicked.connect(self.go_storage)
        back = QPushButton("← 返回大厅")
        back.clicked.connect(self.back)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("商店（临时货币：经验点——金币经济 V2.3 上线）"))
        lay.addWidget(self.currency)
        lay.addWidget(self.pot_lab)
        lay.addLayout(buy_row)
        lay.addWidget(QLabel("回收：只收白装，折算经验 = (5 + Lv×3) × 30%"))
        lay.addWidget(self.recycle_list)
        lay.addWidget(btn_recycle)
        lay.addWidget(btn_storage)
        lay.addWidget(back)
        self.setLayout(lay)

    def refresh(self):
        self.data = save.load()
        if not self.data:
            self.currency.setText("（还没有存档——先进一场战斗创建角色）")
            self.recycle_list.clear()
            self.whites = []
            return
        exp = self.data.get("exp", 0)
        pot = self.data.get("potions", {})
        self.currency.setText(f"可用经验点：{exp}")
        self.pot_lab.setText(f"持有：血瓶 x{pot.get('hp', 0)}   蓝瓶 x{pot.get('mp', 0)}")
        self.whites = [it for it in self.data.get("inventory", [])
                       if it.get("quality") == 0]
        self.recycle_list.clear()
        for it in self.whites:
            QListWidgetItem(f"{gear.item_line(it)}  →  可回收 "
                            f"{recycle_value(it)} 经验", self.recycle_list)

    def buy(self, key):
        if not self.data:
            return
        row = next((r for r in load_shop() if r["key"] == key), None)
        if not row:
            QMessageBox.warning(self, "商店", "未知商品（shop.txt 与按钮脱节）")
            return
        if self.data.get("exp", 0) < row["price"]:
            QMessageBox.warning(self, "经验不足",
                                f"买 {row['name']} 需要 {row['price']} 经验点，"
                                f"你只有 {self.data.get('exp', 0)}")
            return
        field = key.replace("_potion", "")           # hp_potion → hp
        if field not in ("hp", "mp"):
            QMessageBox.warning(self, "商店", "商品不是药水——购买逻辑只支持药水")
            return
        self.data["exp"] -= row["price"]
        self.data.setdefault("potions", {"hp": 0, "mp": 0})[field] += 1
        save.write_raw(self.data)
        self.refresh()

    def recycle(self):
        row = self.recycle_list.currentRow()
        if not (0 <= row < len(self.whites)):
            return
        it = self.whites[row]
        self.data["inventory"].remove(it)
        self.data["exp"] = self.data.get("exp", 0) + recycle_value(it)
        save.write_raw(self.data)
        self.refresh()
