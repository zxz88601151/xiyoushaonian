# V2.9-D2 日常窗 —— 三页（日常 / 周常 / 签到），领取即写档（只改 claimed/gold/protect）。
# 进度口径全部来自 daily.status（唯一汇总处），界面不自己算增量。
import configparser

from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QTabWidget,
                               QVBoxLayout, QWidget)

import daily
import save

NAMES = {"kills": "击杀妖怪", "damage": "造成伤害", "tower": "爬塔层数"}


class DailyWindow(QWidget):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.data = {}
        self.cfg = configparser.ConfigParser()
        self.cfg.read("game.ini", encoding="utf-8")
        self.btns = {}
        tabs = QTabWidget()
        tabs.addTab(self._page("daily", "日常（每天 0 点刷新，进度按当日增量算）"), "日常")
        tabs.addTab(self._page("weekly", "周常（每周一刷新，进度按本周增量算）"), "周常")
        tabs.addTab(self._checkin(), "签到")
        self.msg = QLabel("……")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("日常 / 周常 / 签到（领取即写档）"))
        lay.addWidget(tabs)
        lay.addWidget(self.msg)
        btn = QPushButton("← 返回大厅")
        btn.clicked.connect(back)
        lay.addWidget(btn)

    def _page(self, scope, tip):
        box, lay = QWidget(), QVBoxLayout()
        lay.addWidget(QLabel(tip))
        for key in ("kills", "damage", "tower"):
            row = QHBoxLayout()
            row.addWidget(QLabel(NAMES[key]))
            b = QPushButton("…")
            b.clicked.connect(lambda _, s=scope, k=key: self.claim(s, k))
            self.btns[(scope, key)] = b
            row.addWidget(b)
            lay.addLayout(row)
        lay.addStretch()
        box.setLayout(lay)
        return box

    def _checkin(self):
        box, lay = QWidget(), QVBoxLayout()
        self.ck_info, self.ck_btn = QLabel("…"), QPushButton("签到")
        self.ck_btn.clicked.connect(lambda: self.claim("checkin", ""))
        lay.addWidget(self.ck_info)
        lay.addWidget(self.ck_btn)
        lay.addStretch()
        box.setLayout(lay)
        return box

    def refresh(self):
        self.data = save.load() or {}
        if not self.data:
            self.msg.setText("（还没有存档——先进一场战斗创建角色）")
            for b in list(self.btns.values()) + [self.ck_btn]:
                b.setText("—")
                b.setEnabled(False)
            return
        st = daily.status(self.data, self.cfg)
        for (scope, key), btn in self.btns.items():
            row = next(r for r in st[scope] if r["key"] == key)
            done, gold = row["cur"] >= row["need"], self.cfg.getint(scope, "gold")
            btn.setText("已领取" if row["claimed"] else
                        ("领取（+%d 金币）" % gold if done else "%d/%d" % (row["cur"], row["need"])))
            btn.setEnabled(not row["claimed"] and done)
        ck = st["checkin"]
        self.ck_info.setText("累计签到 %d 天 · 连签 %d 天 ｜ 今天第 %d 天：金币 %d%s"
                             % (ck["total"], ck["streak"], ck["next_day"], ck["gold"],
                                " + 保底符 1" if ck["staff"] else ""))
        self.ck_btn.setText("今天已签到" if ck["claimed_today"] else "签到（+%d 金币）" % ck["gold"])
        self.ck_btn.setEnabled(not ck["claimed_today"])

    def claim(self, scope, key):
        if not self.data:
            return
        ok, msg = daily.claim(self.data, self.cfg, scope, key)
        if ok:
            save.write_raw(self.data)
        self.msg.setText(msg)
        self.refresh()
