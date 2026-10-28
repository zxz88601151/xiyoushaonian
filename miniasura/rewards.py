# V2.2 奖励发放 —— 自 engine.py 拆出（行数红线销账）。
# 只认识 gear/药水/经验三种奖励，不认识任务状态机（completed 列表由 quests.Tracker 产出）。
import gear
import quests
from combat import grant_exp


def apply_rewards(cfg, player, io, completed, storage):
    """任务奖励发放（exp/药水/装备）；背包满时装备转仓库；空部位奖励直接穿上。"""
    for q in completed:
        io.say(f"\n📜 任务完成【{q['name']}】")
        for kind, args in quests.parse_rewards(q["reward"]):
            if kind == "exp":
                grant_exp(cfg, player, io, int(args[0]))
            elif kind == "potion_hp":
                player["potions"]["hp"] += int(args[0])
                io.say(f"  获得血瓶 x{args[0]}")
            elif kind == "potion_mp":
                player["potions"]["mp"] += int(args[0])
                io.say(f"  获得蓝瓶 x{args[0]}")
            elif kind == "gear":
                slot, lv, qual = args
                it = gear.generate(slot, int(lv), int(qual))
                cur = player["equipment"].get(slot)
                if cur is None:               # 空位直接穿上（任务奖励即战力）
                    player["equipment"][slot] = it
                    from engine import apply_gear
                    apply_gear(cfg, player)
                    player["hp"] = min(player["hp"], player["max_hp"])
                    io.say(f"  获得装备并穿上：{gear.item_line(it)}")
                    continue
                bag = player.setdefault("inventory", [])
                if len(bag) < gear.capacity():
                    bag.append(it)
                    io.say(f"  获得装备：{gear.item_line(it)}")
                else:
                    storage.append(it)
                    io.say(f"  获得装备：{gear.item_line(it)}（背包已满，转入仓库）")
