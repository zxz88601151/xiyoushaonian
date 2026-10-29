# V2.0 窗口路由 —— QStackedWidget 装配登录→选区→槽位→大厅→战斗的玩家旅程。
# 本文件只做路由和数据源装配，不碰战斗逻辑（依赖单向 gui_* → engine → save）。
import sys

from PySide6.QtWidgets import QApplication, QStackedWidget

import gui
import gui_bag
import gui_codex
import gui_enhance
import gui_quests
import gui_shop
import gui_tower
import login
import save
import slots
from gui_hub import HubWindow
from gui_login import LoginWindow
from gui_slots import ServerWindow, SlotsWindow


class App(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("花果山小妖 —— MiniAsura V2.5")
        self.resize(640, 560)

        self.login = LoginWindow(self.to_server, self.to_hub)
        self.server = ServerWindow(self.pick_server)
        self.slotsw = SlotsWindow(self.pick_slot, self.to_server)
        self.hub = HubWindow(self.to_battle, self.to_bag, self.logout,
                             go_quests=self.to_quests, go_shop=self.to_shop,
                             go_enhance=self.to_enhance, go_tower=self.to_tower,
                             go_codex=self.to_codex)
        self.battle = gui.BattleWidget()
        self.battle.back_to_hub.connect(self.to_hub)
        self.bag = gui_bag.BagWindow(self.to_hub)
        self.storage = gui_bag.BagWindow(self.to_hub, source="storage")
        self.shop = gui_shop.ShopWindow(self.to_hub, self.to_storage)
        self.questsw = gui_quests.QuestWindow(self.to_hub)
        self.enhancew = gui_enhance.EnhanceWindow(self.to_hub)
        self.towerw = gui_tower.TowerWindow(self.to_hub)
        self.codexw = gui_codex.CodexWindow(self.to_hub)
        for w in (self.login, self.server, self.slotsw, self.hub, self.battle,
                  self.bag, self.storage, self.shop, self.questsw, self.enhancew,
                  self.towerw, self.codexw):
            self.addWidget(w)

        sess = login.get_session()          # 会话恢复：记住上次登录
        if sess and sess.get("server") and sess.get("slot"):
            self.to_hub()
        elif sess:
            self.to_server()
        else:
            self.setCurrentWidget(self.login)

    def to_server(self):
        self.slotsw.refresh()
        self.setCurrentWidget(self.server)

    def pick_server(self, sid):
        sess = login.get_session()
        login.start_session(sess["user"], sid, sess.get("slot", 0))
        self.slotsw.refresh()
        self.setCurrentWidget(self.slotsw)

    def pick_slot(self, slot):
        sess = login.get_session()
        login.start_session(sess["user"], sess["server"], slot)
        self.to_hub()

    def to_hub(self):
        sess = login.get_session()
        if not sess:
            self.logout()
            return
        if sess.get("server") and sess.get("slot"):
            save.set_path(slots.slot_path(sess["server"], sess["user"],
                                          sess["slot"]), sess["user"])
        self.slotsw.refresh()
        self.hub.refresh()          # V2.5：进大厅时按存档刷新爬塔入口的显隐
        self.setCurrentWidget(self.hub)

    def to_tower(self):
        self.towerw.refresh()
        self.setCurrentWidget(self.towerw)

    def to_codex(self):
        self.codexw.refresh()
        self.setCurrentWidget(self.codexw)

    def to_battle(self):
        self.setCurrentWidget(self.battle)
        self.battle.begin()

    def to_bag(self):
        self.bag.refresh()
        self.setCurrentWidget(self.bag)

    def to_storage(self):
        self.storage.refresh()
        self.setCurrentWidget(self.storage)

    def to_shop(self):
        self.shop.refresh()
        self.setCurrentWidget(self.shop)

    def to_quests(self):
        self.questsw.refresh()
        self.setCurrentWidget(self.questsw)

    def to_enhance(self):
        self.enhancew.refresh()
        self.setCurrentWidget(self.enhancew)

    def logout(self):
        login.logout()
        self.setCurrentWidget(self.login)


def main():
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
