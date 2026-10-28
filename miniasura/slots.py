# V2.0 存档槽 —— 每账号每区服 3 槽（saves/<server>/<user>/slotN.json）。
# 纯数据层：GUI 与 gm.py 共用；不判断 schema（迁移在 save.load 里发生）。
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SAVES = os.path.join(HERE, "saves")
SLOT_COUNT = 3


def slot_path(server, user, slot):
    return os.path.join(SAVES, server, user, "slot%d.json" % slot)


def list_slots(server, user):
    rows = []
    for n in range(1, SLOT_COUNT + 1):
        p = slot_path(server, user, n)
        row = {"slot": n, "exists": os.path.exists(p)}
        if row["exists"]:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            row.update({"level": d.get("level"), "week": d.get("week", 0),
                        "next": d.get("next", 0), "playtime": d.get("playtime", 0)})
        rows.append(row)
    return rows


def delete_slot(server, user, slot):
    p = slot_path(server, user, slot)
    if os.path.exists(p):
        os.remove(p)
        return True
    return False
