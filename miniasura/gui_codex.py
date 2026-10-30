# V2.8 图鉴窗 —— 一窗五页（武器谱 / 怪物图鉴 / 成就 / 称号 / 统计）。
# V2.9-D1：称号页可佩戴（唯一写档处，只写 title 一个键）；其余四页仍只读，统计口径仍走 progress 单一来源。
import os
import sys

from PySide6.QtWidgets import (QComboBox, QLabel, QPushButton, QTabWidget, QTextEdit,
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
        self.titles = self._title_page()   # V2.9-D1：第 5 页（唯一可写档的页）
        self.stats = self._page()

        tabs = QTabWidget()
        tabs.addTab(self.weapons, "武器谱")
        tabs.addTab(self.monsters, "怪物图鉴")
        tabs.addTab(self.achieve, "成就")
        tabs.addTab(self.titles, "称号")
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

    def _title_page(self):
        # V2.9-D1：称号页是本窗唯一写档处（佩戴），其余四页保持只读。
        box, self.title_now = QWidget(), QLabel()
        self.title_box, self.title_list = QComboBox(), QTextEdit(); self.title_list.setReadOnly(True)
        btn = QPushButton("佩戴所选称号")
        btn.clicked.connect(self.wear_title)
        lay = QVBoxLayout(box)
        for w in (self.title_now, self.title_box, btn, self.title_list):
            lay.addWidget(w)
        return box

    def wear_title(self):
        data = save.load() or {}
        data["title"] = self.title_box.currentData() or ""
        save.write_raw(data)          # 只改 title 一个键，其余字段原样带回
        self.refresh()

    def refresh(self):
        self.data = save.load() or {}
        self._fill_weapons()
        self._fill_monsters()
        self._fill_achievements()
        self._fill_titles()
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

    def _fill_titles(self):
        got, rows, cur = set(self.data.get("achievements", [])), progress.load_titles(), self.data.get("title", "")
        self.title_now.setText("当前称号：%s" % next((t["name"] for t in rows if t["id"] == cur), "无"))
        self.title_box.clear(); self.title_box.addItem("（不佩戴）", "")
        for t in rows:
            if t["ach"] in got:
                self.title_box.addItem(t["name"], t["id"])
        self.title_box.setCurrentIndex(max(0, self.title_box.findData(cur)))   # 预选当前佩戴
        lines = ["%s %s —— %s" % ("●" if t["ach"] in got else "○", t["name"], t["desc"]) for t in rows]
        lines.append("\n解锁进度：%d/%d" % (sum(1 for t in rows if t["ach"] in got), len(rows)))
        self.title_list.setPlainText("\n".join(lines))

    def _fill_stats(self):
        s, rec = progress.stats(self.data), (self.data.get("records") or {})
        rows = ["总击杀：%d" % s["kills"], "总伤害：%d" % s["damage"],
                "游玩时长：%s" % s["playtime"], "通关周目：%d" % s["week"],
                "爬塔最高：%d 层" % s["tower_best"], "当前等级：Lv.%d" % s["level"],
                "金币：%d" % s["gold"], "", "幻影榜（本地纪录）",
                "单场最高伤害：%d（%s）" % (rec.get("best_dealt", 0), rec.get("best_dealt_mon") or "—"),
                "单场最少回合：%s（%s）" % (("%d 回合" % rec["best_rounds"]) if rec.get("best_rounds") else "—", rec.get("best_rounds_mon") or "—"),
                "爬塔最高层：%d 层" % s["tower_best"]]
        self.stats.setPlainText("\n".join(rows))
