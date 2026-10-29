# V2.8 图鉴窗 —— 一窗四页（武器谱 / 怪物图鉴 / 成就 / 统计），只读存档不写盘（DESIGN_V2_8 §3）。
# 四页读同一存档快照，统计口径与图鉴点亮共用 progress 一个来源，不可能漂移。
import os
import sys

from PySide6.QtWidgets import (QLabel, QPushButton, QTabWidget, QTextEdit,
                               QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))

import engine
import gear
import progress
import save


class CodexWindow(QWidget):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.data = {}
        self.weapons = self._page()
        self.monsters = self._page()
        self.achieve = self._page()
        self.stats = self._page()

        tabs = QTabWidget()
        tabs.addTab(self.weapons, "武器谱")
        tabs.addTab(self.monsters, "怪物图鉴")
        tabs.addTab(self.achieve, "成就")
        tabs.addTab(self.stats, "统计")
        back_btn = QPushButton("← 返回大厅")
        back_btn.clicked.connect(self.back)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("图鉴 / 成就 / 统计（只读）"))
        lay.addWidget(tabs)
        lay.addWidget(back_btn)
        self.setLayout(lay)

    def _page(self):
        box = QTextEdit()
        box.setReadOnly(True)
        return box

    def refresh(self):
        self.data = save.load() or {}
        self._fill_weapons()
        self._fill_monsters()
        self._fill_achievements()
        self._fill_stats()

    def _fill_weapons(self):
        # 武器谱 10 把全列：● 已获得（曾经拥有，卖出不灭灯）/ ○ 未获得 + x/10
        owned = set(self.data.get("codex_weapons", []))
        names = list(gear.WEAPON_NAMES)
        lines = ["%s %s" % ("●" if n in owned else "○", n) for n in names]
        lines.append("\n收集进度：%d/%d" % (len(set(names) & owned), len(names)))
        self.weapons.setPlainText("\n".join(lines))

    def _fill_monsters(self):
        # 怪物图鉴：全部怪物行，● 名 ×击杀数 / ○ 未遭遇（lose: 前缀不算击杀）
        mons = engine.parse_kv(engine.load_texts()["monsters.txt"])
        rows = progress.monster_codex(self.data, [(k, v[0]) for k, v in mons.items()])
        lines = ["%s %s%s" % ("●" if seen else "○", name,
                              (" ×%d" % n) if seen else "（未遭遇）") for _, name, n, seen in rows]
        lines.append("\n图鉴进度：%d/%d" % (sum(1 for r in rows if r[3]), len(rows)))
        self.monsters.setPlainText("\n".join(lines))

    def _fill_achievements(self):
        got = set(self.data.get("achievements", []))
        rows = progress.load_achievements()
        lines = ["%s %s —— %s" % ("●" if a["id"] in got else "○", a["name"], a["desc"])
                 for a in rows]
        lines.append("\n成就进度：%d/%d" % (len(got & {a["id"] for a in rows}), len(rows)))
        self.achieve.setPlainText("\n".join(lines))

    def _fill_stats(self):
        s = progress.stats(self.data)
        self.stats.setPlainText("\n".join([
            "总击杀：%d" % s["kills"], "总伤害：%d" % s["damage"],
            "游玩时长：%s" % s["playtime"], "通关周目：%d" % s["week"],
            "爬塔最高：%d 层" % s["tower_best"], "当前等级：Lv.%d" % s["level"],
            "金币：%d" % s["gold"]]))
