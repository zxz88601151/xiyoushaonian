# V3.0-A 成长窗 —— 宝石 / 套装 / 属性点三页；写档统一走 save.write_raw（只改宝石与加点相关字段）。
# 界面自己不算数值：宝石查 gem、套装查 sets、加点查 attrs，与战斗面板同一套汇总口径。
import configparser

from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                               QTabWidget, QVBoxLayout, QWidget)

import attrs
import gem
import gear
import save
import sets

SLOTS = ("weapon", "helm", "armor", "belt", "boots")
SLOT_NAMES = {"weapon": "武器", "helm": "头盔", "armor": "护甲", "belt": "腰带", "boots": "靴子"}


class GrowWindow(QWidget):
    def __init__(self, back):
        super().__init__()
        self.back = back
        self.data = {}
        self.cfg = configparser.ConfigParser()
        self.cfg.read("game.ini", encoding="utf-8")
        self.btns = {}
        tabs = QTabWidget()
        tabs.addTab(self._gem_page(), "宝石")
        tabs.addTab(self._set_page(), "套装")
        tabs.addTab(self._attr_page(), "属性点")
        self.msg = QLabel("……")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("成长（宝石 / 套装 / 属性点）"))
        lay.addWidget(tabs)
        lay.addWidget(self.msg)
        btn = QPushButton("← 返回大厅")
        btn.clicked.connect(back)
        lay.addWidget(btn)

    def _gem_page(self):
        """宝石页：碎片 / 装备孔位 / 宝石栏 + 四个操作按钮。"""
        box, lay = QWidget(), QVBoxLayout()
        self.shard_lbl, self.hold_lbl = QLabel("…"), QLabel("…")
        self.slot_box, self.gem_box = QComboBox(), QComboBox()
        act = (("open", "开出一颗（3 碎片）", lambda: self._done(*gem.open_shard(self.data, self.cfg))),
               ("socket", "镶嵌到空孔", self.do_socket),
               ("unsocket", "拆下第一颗", self.do_unsocket),
               ("merge", "合成三合一", self.do_merge))
        lay.addWidget(self.shard_lbl)
        lay.addWidget(QLabel("装备（只列已穿戴）"))
        lay.addWidget(self.slot_box)
        lay.addWidget(self.hold_lbl)
        lay.addWidget(QLabel("宝石栏（选中一颗再操作）"))
        lay.addWidget(self.gem_box)
        row = QHBoxLayout()
        for key, text, fn in act:
            b = QPushButton(text)
            b.clicked.connect(fn)
            self.btns[key] = b
            row.addWidget(b)
        lay.addLayout(row)
        lay.addStretch()
        box.setLayout(lay)
        return box

    def _set_page(self):
        box, lay = QWidget(), QVBoxLayout()
        self.set_lbl = QLabel("…")
        self.set_lbl.setWordWrap(True)
        lay.addWidget(self.set_lbl)
        lay.addStretch()
        box.setLayout(lay)
        return box

    def _attr_page(self):
        box, lay = QWidget(), QVBoxLayout()
        self.attr_lbl = QLabel("…")
        self.attr_lbl.setWordWrap(True)
        lay.addWidget(self.attr_lbl)
        for dim in attrs.DIMS:
            row = QHBoxLayout()
            row.addWidget(QLabel(attrs.NAMES[dim]))
            b = QPushButton("+1")
            b.clicked.connect(lambda _, d=dim: self._done(*attrs.add(self.data, d, 1, self.cfg)))
            self.btns[("attr", dim)] = b
            row.addWidget(b)
            lay.addLayout(row)
        self.reset_btn = QPushButton("洗点（免费，全额退回）")
        self.reset_btn.clicked.connect(lambda: self._done(*attrs.reset(self.data)))
        lay.addWidget(self.reset_btn)
        lay.addStretch()
        box.setLayout(lay)
        return box

    def refresh(self):
        self.data = save.load() or {}
        if not self.data:
            self.msg.setText("（还没有存档——先进一场战斗创建角色）")
            for b in list(self.btns.values()) + [self.reset_btn]:
                b.setEnabled(False)
            return
        eq = self.data.get("equipment") or {}
        self.slot_box.clear()
        for s in SLOTS:
            if eq.get(s):
                self.slot_box.addItem("%s：%s" % (SLOT_NAMES[s], gear.item_name(eq[s])), s)
        self.gem_box.clear()
        for i, g in enumerate(self.data.get("gems") or []):
            self.gem_box.addItem(gem.label(g), i)
        stash = self.cfg.getint("gem", "stash", fallback=20)
        self.shard_lbl.setText("碎片 %d ｜ 宝石栏 %d/%d（孔位按品质：白 0 / 蓝 1 / 紫 2）"
                               % (int(self.data.get("shard", 0)), len(self.data.get("gems") or []), stash))
        it = self._cur_item()
        self.hold_lbl.setText("（未穿戴，或这件装备没有孔位）" if not it or not gem.holes_of(it) else
                              "孔位 %d：%s" % (len(gem.slots_of(it)),
                                              " / ".join(gem.label(g) if g else "空" for g in gem.slots_of(it))))
        cnt = sets.active(eq)
        self.set_lbl.setText("\n".join(
            "%s（%d 件）：%s\n　2 件：%s ｜ 4 件：%s"
            % (r["name"], cnt.get(k, 0), "4 件已激活" if cnt.get(k, 0) >= 4 else
               ("2 件已激活" if cnt.get(k, 0) >= 2 else "未激活"),
               "、".join("%s+%g" % (a, b) for a, b in r["two"].items()) or "无",
               "、".join("%s+%g" % (a, b) for a, b in r["four"].items()) or "无")
            for k, r in sorted(sets.load().items())) or "（套装表为空）")
        total, left = attrs.total(self.data, self.cfg), attrs.free(self.data, self.cfg)
        sp = attrs.state(self.data)["spent"]
        self.attr_lbl.setText("累计 %d 点 ｜ 已用 %d ｜ 剩余 %d（Lv.2 起每级 3 点）\n"
                              "当前：攻击 %d / 生命 %d / 防御 %d / 暴击 %d"
                              % (total, total - left, left, sp["atk"], sp["hp"], sp["def"], sp["crit"]))
        for dim in attrs.DIMS:
            self.btns[("attr", dim)].setEnabled(left > 0)

    def _cur_item(self):
        s = self.slot_box.currentData()
        return (self.data.get("equipment") or {}).get(s) if s else None

    def _cur_gem(self):
        i = self.gem_box.currentData()
        return (self.data.get("gems") or [])[i] if i is not None else None

    def do_merge(self):
        g = self._cur_gem()
        self._done(*(gem.merge(self.data, g["key"], g["lv"]) if g else (False, "先选一颗宝石")))

    def do_socket(self):
        it, g = self._cur_item(), self._cur_gem()
        if not (it and g):
            self.msg.setText("先选装备与宝石")
            return
        idx = next((k for k, v in enumerate(gem.slots_of(it)) if not v), None)
        if idx is None:
            self.msg.setText("这件装备没有空孔")
            return
        ok, msg = gem.socket(it, idx, g)
        if ok:
            self.data["gems"].remove(g)          # 镶嵌成功才从宝石栏移走
        self._done(ok, msg)

    def do_unsocket(self):
        it = self._cur_item()
        idx = next((k for k, v in enumerate(gem.slots_of(it)) if v), None) if it else None
        back = gem.unsocket(it, idx) if idx is not None else None
        if back is None:
            self.msg.setText("这件装备没有已镶宝石")
            return
        if len(self.data.get("gems") or []) >= self.cfg.getint("gem", "stash", fallback=20):
            gem.socket(it, idx, back)            # 宝石栏满：原样装回，绝不吞宝石（G2 无损）
            self.msg.setText("宝石栏已满，先空出一格")
            return
        self.data.setdefault("gems", []).append(back)
        self._done(True, "已拆下 %s" % gem.label(back))

    def _done(self, ok, msg):
        if ok:
            save.write_raw(self.data)
        self.msg.setText(msg)
        self.refresh()
