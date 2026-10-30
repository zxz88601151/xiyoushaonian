# V2.0 大厅窗 → V2.2 主城 —— 公告 + 战斗 + 任务/商店/背包 + 退出登录。
import os

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

HERE = os.path.dirname(os.path.abspath(__file__))


class HubWindow(QWidget):
    def __init__(self, go_battle, go_bag, go_login, go_quests=None, go_shop=None,
                 go_enhance=None, go_tower=None, go_codex=None, go_daily=None):
        super().__init__()
        self.go_tower = go_tower or (lambda: None)
        self.tower_btn = QPushButton("无底洞（爬塔）")     # OD-V25-03：通关一次后才显示
        self.tower_btn.clicked.connect(self.go_tower)
        codex_btn = QPushButton("图鉴 / 成就 / 统计")     # V2.8：一窗四页
        codex_btn.clicked.connect(go_codex or (lambda: None))
        daily_btn = QPushButton("日常 / 周常 / 签到")     # V2.9-D2
        daily_btn.clicked.connect(go_daily or (lambda: None))
        news = QTextEdit()
        news.setReadOnly(True)
        with open(os.path.join(HERE, "news.txt"), encoding="utf-8") as f:
            news.setPlainText(f.read())
        self.title_lbl = QLabel("称号：无")     # V2.9-D1：当前称号（refresh 读档刷新）
        start = QPushButton("进入游戏（继续 / 开新周目）")
        start.clicked.connect(go_battle)
        bag = QPushButton("背包 / 装备")
        bag.clicked.connect(go_bag)
        quest = QPushButton("任务（看进度 / 重看对话）")
        quest.clicked.connect(go_quests or (lambda: None))
        shop = QPushButton("商店（买药 / 回收 / 仓库）")
        shop.clicked.connect(go_shop or (lambda: None))
        enhance_btn = QPushButton("铁匠（强化）")
        enhance_btn.clicked.connect(go_enhance or (lambda: None))
        out = QPushButton("退出登录")
        out.clicked.connect(go_login)

        lay = QVBoxLayout()
        lay.addWidget(QLabel("主城"))
        lay.addWidget(news)
        lay.addWidget(self.title_lbl)
        lay.addWidget(start)
        lay.addWidget(quest)
        lay.addWidget(shop)
        lay.addWidget(enhance_btn)
        lay.addWidget(self.tower_btn)
        lay.addWidget(codex_btn)
        lay.addWidget(daily_btn)
        lay.addWidget(bag)
        lay.addWidget(out)
        self.setLayout(lay)
        self.tower_btn.hide()          # 默认隐藏，refresh() 按存档解锁情况决定显隐

    def refresh(self):
        """V2.5：爬塔入口按通关情况显隐；V2.9-D1：显示当前佩戴称号。"""
        import progress
        import save
        import tower
        st = save.load() or {}
        name = next((t["name"] for t in progress.load_titles() if t["id"] == st.get("title")), "无")
        self.title_lbl.setText("称号：%s" % name)
        self.tower_btn.setVisible(tower.unlocked(st))
