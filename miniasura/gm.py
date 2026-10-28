# V2.0/V2.1 GM 调试台（CLI）—— 上帝视角直连存档层，不经引擎主循环。
# 操作对象 = 当前会话指向的槽位；无会话/无存档 fail-closed 报错退出。
import os
import sys

import gear
import login
import quests
import save
import slots

USAGE = ("用法: gm.py setlevel <n> | next <k> | give <slot> [lv] [quality=2]"
         " | quest <key> | map <n> | potion <hp|mp> <n> | gold <n>"
         " | difficulty <0|1|2> | protect <n> | wipe")


def current_slot():
    sess = login.get_session()
    if not sess or not sess.get("user") or not sess.get("server") or not sess.get("slot"):
        print("无有效会话——先从 GUI 登录并选择槽位")
        sys.exit(1)
    return sess


def _int(s):
    try:
        v = int(s)
    except ValueError:
        print("数字参数不合法:", s)
        sys.exit(1)
    if v < 0:
        print("数字参数不能为负:", s)
        sys.exit(1)
    return v


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)
    cmd = sys.argv[1]
    sess = current_slot()
    path = slots.slot_path(sess["server"], sess["user"], sess["slot"])

    if cmd == "wipe":
        print("将删除 %s —— 确认请输入 yes" % path)
        if input().strip() == "yes":
            hit = slots.delete_slot(sess["server"], sess["user"], sess["slot"])
            print("已删除" if hit else "槽位本来就是空的")
        else:
            print("已取消")
        return

    if not os.path.exists(path):
        print("该槽位还没有存档")
        sys.exit(1)
    save.set_path(path, sess["user"])
    data = save.load()
    if cmd == "give" and 3 <= len(sys.argv) <= 5:
        slot = sys.argv[2]
        if slot.isdigit():
            slot = gear.SLOTS[int(slot) % len(gear.SLOTS)]
        if slot not in gear.SLOTS:
            print("部位必须是", "/".join(gear.SLOTS), "或 0-4")
            sys.exit(1)
        try:
            lv = int(sys.argv[3]) if len(sys.argv) >= 4 else data["level"]
            quality = int(sys.argv[4]) if len(sys.argv) == 5 else 2
        except ValueError:
            print("lv / quality 必须是整数")
            sys.exit(1)
        if len(data.get("inventory", [])) >= gear.capacity():
            print("背包已满（%d 件）——发不进去了" % gear.capacity())
            sys.exit(1)
        try:
            item = gear.generate(slot, lv, quality)
        except ValueError as e:
            print("发放失败:", e)
            sys.exit(1)
        data.setdefault("inventory", []).append(item)
        print("已发放:", gear.item_line(item))
        print("词条:", "、".join(f"{a['name']}+{a['val']:.1f}" for a in item["affixes"]) or "无")
    elif cmd == "setlevel" and len(sys.argv) == 3:
        data["level"] = _int(sys.argv[2])
        print("等级 → %d（攻击力由引擎按等级重算，存档不存派生值）" % data["level"])
    elif cmd == "next" and len(sys.argv) == 3:
        data["next"] = _int(sys.argv[2])
        print("进度 → 第 %d 战" % (data["next"] + 1))
    elif cmd == "quest" and len(sys.argv) == 3:
        valid = {q["key"] for q in quests.load(quests.load_pack_text())}
        if sys.argv[2] not in valid:
            print("未知任务 key（合法值: %s）" % ", ".join(sorted(valid)))
            sys.exit(1)
        data.setdefault("quest_flags", {})[sys.argv[2]] = "done"
        print("任务 %s → done" % sys.argv[2])
    elif cmd == "map" and len(sys.argv) == 3:
        n = _int(sys.argv[2])
        if not 1 <= n <= 10:
            print("图号必须是 1-10")
            sys.exit(1)
        data["maps_cleared"] = n
        print("已通图数 → %d" % n)
    elif cmd == "potion" and len(sys.argv) == 4 and sys.argv[2] in ("hp", "mp"):
        data.setdefault("potions", {"hp": 0, "mp": 0})[sys.argv[2]] = _int(sys.argv[3])
        print("药水 %s → %d" % (sys.argv[2], int(sys.argv[3])))
    elif cmd == "gold" and len(sys.argv) == 3:
        data["gold"] = _int(sys.argv[2])
        print("金币 → %d" % data["gold"])
    elif cmd == "protect" and len(sys.argv) == 3:
        data["protect"] = _int(sys.argv[2])
        print("保底符 → %d" % data["protect"])
    elif cmd == "difficulty" and len(sys.argv) == 3:
        n = _int(sys.argv[2])
        if n not in (0, 1, 2):
            print("难度必须是 0普通/1精英/2噩梦")
            sys.exit(1)
        data["difficulty"] = n
        print("难度 → %d" % n)
    else:
        print(USAGE)
        sys.exit(1)
    save.write_raw(data)


if __name__ == "__main__":
    main()
