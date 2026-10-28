# V2.0 登录外围 —— 账号 + 会话。教学级盐哈希（真实生产用 bcrypt/argon2 慢哈希）。
# 契约：engine.py 不 import 本模块；登录层只决定 save 路径，不碰游戏逻辑。
import hashlib
import json
import os
import secrets

HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = os.path.join(HERE, "accounts.json")
SESSION = os.path.join(HERE, "session.json")


def _hash(salt, password):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _read(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def register(user, password):
    """成功返回 None，失败返回原因字符串（fail-closed：不抛异常静默通过）。"""
    if not user.strip() or not password:
        return "用户名和密码不能为空"
    accounts = _read(ACCOUNTS, [])
    if any(a["user"] == user for a in accounts):
        return "用户名已存在"
    salt = secrets.token_hex(16)
    accounts.append({"user": user, "salt": salt, "hash": _hash(salt, password)})
    _write(ACCOUNTS, accounts)
    return None


def login(user, password):
    for a in _read(ACCOUNTS, []):
        if a["user"] == user:
            return None if a["hash"] == _hash(a["salt"], password) else "密码错误"
    return "用户不存在"


def start_session(user, server="", slot=0):
    _write(SESSION, {"user": user, "server": server, "slot": slot})


def get_session():
    return _read(SESSION, None)


def logout():
    if os.path.exists(SESSION):
        os.remove(SESSION)
