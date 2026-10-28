# V2.0 登录窗 —— 注册/登录；成功后写会话并切换（会话完整则直回大厅）。
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

import login


class LoginWindow(QWidget):
    def __init__(self, go_server, go_hub):
        super().__init__()
        self.go_server, self.go_hub = go_server, go_hub

        self.user = QLineEdit()
        self.user.setPlaceholderText("用户名")
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("密码")
        self.pwd.setEchoMode(QLineEdit.Password)
        btn_in = QPushButton("登录")
        btn_in.clicked.connect(self.do_login)
        btn_up = QPushButton("注册")
        btn_up.clicked.connect(self.do_register)
        self.msg = QLabel("（上次登录的账号会自动填到会话里）")

        lay = QVBoxLayout()
        lay.addWidget(QLabel("花果山小妖 —— 登录"))
        lay.addWidget(self.user)
        lay.addWidget(self.pwd)
        lay.addWidget(btn_in)
        lay.addWidget(btn_up)
        lay.addWidget(self.msg)
        self.setLayout(lay)

    def do_register(self):
        err = login.register(self.user.text().strip(), self.pwd.text())
        self.msg.setText(err or "注册成功，请登录")

    def do_login(self):
        err = login.login(self.user.text().strip(), self.pwd.text())
        if err:
            self.msg.setText(err)
            return
        sess = login.get_session() or {}
        login.start_session(self.user.text().strip(),
                            sess.get("server", ""), sess.get("slot", 0))
        sess = login.get_session()
        if sess.get("server") and sess.get("slot"):
            self.go_hub()
        else:
            self.go_server()
