# V2.9-C 战报卡 —— 常驻显示「最近一场战报」+ 本窗口会话合计。
# 只做呈现：不改数值、不写存档、不引入全局样式表（固定色值在深色系统主题下不可读）。
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

FIELDS = ("rounds", "dealt", "taken", "crits", "misses")


class ReportCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)   # D6：默认前景色 + 边框，不写死颜色
        self.last = None
        self.total = dict.fromkeys(("fights",) + FIELDS, 0)
        self.title, self.detail = QLabel(), QLabel()
        self.title.setWordWrap(True)
        self.detail.setWordWrap(True)
        f = self.title.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 2)        # 主数字放大，副行保持正文尺寸
        self.title.setFont(f)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.addWidget(self.title)
        lay.addWidget(self.detail)
        self.reset()

    def show_report(self, rep, line=""):
        # line 是日志原文：日志负责完整记录（D3），卡片只展示提炼后的数字，不重复贴原文。
        self.last = dict(rep or {})
        for k in FIELDS:
            self.total[k] += int(self.last.get(k, 0) or 0)
        self.total["fights"] += 1
        t, a = self.last, self.total
        self.title.setText("最近一场战报 · %d 回合 · 造成 %d · 承受 %d"
                           % (t.get("rounds", 0), t.get("dealt", 0), t.get("taken", 0)))
        self.detail.setText("暴击 %d · MISS %d ｜ 本局累计：%d 场 / 造成 %d / 承受 %d"
                            % (t.get("crits", 0), t.get("misses", 0),
                               a["fights"], a["dealt"], a["taken"]))

    def reset(self):
        self.last = None
        for k in self.total:
            self.total[k] = 0
        self.title.setText("（还没有战报）")
        self.detail.setText("打完一场战斗，这里显示最近一场与本局累计。")
