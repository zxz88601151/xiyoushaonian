# V2.3 掉落引擎 + 难度换算 —— 数据驱动（game.ini [loot.*]），只管掷骰与落袋。
# 不认识任务、地图与战斗流程；掉落绝不自动穿戴（只进背包，满则进仓库）。
import random

import gear

DIFF_NAMES = ("普通", "精英", "噩梦")
DIFF_MULT = ((1.0, 1.0), (1.3, 1.5), (1.6, 2.0))  # (血攻, 经验金币)


def ask_difficulty(io):
    """新档/新周目问一次难度；非 1/2/3 一律按普通处理（fail-closed）。"""
    pick = io.ask("选择难度 1普通 / 2精英(+3级) / 3噩梦(+6级) > ").strip()
    return int(pick) - 1 if pick in ("1", "2", "3") else 0


def grant_win(cfg, fight, player, storage, io, difficulty):
    """胜利结算：金币入账 + 掉落掷骰（引擎主循环只调这一行）。V2.9-A：精英/稀有再掷一次额外池。"""
    gold = fight["mon"].get("gold", 0)
    if gold:
        player["gold"] = player.get("gold", 0) + gold
        io.say(f"  获得金币 {gold}！")
    roll(cfg, fight["key"], player, storage, io, difficulty=difficulty)
    if fight.get("elite"):
        roll(cfg, "elite", player, storage, io, difficulty=difficulty)
        player["shard"] = player.get("shard", 0) + cfg.getint("gem", "shard_per_elite", fallback=0)   # V3.0-A
    if fight.get("rare"):
        roll(cfg, "rare", player, storage, io, difficulty=difficulty)
        player["shard"] = player.get("shard", 0) + cfg.getint("gem", "shard_per_rare", fallback=0)     # V3.0-A


def load_table(cfg):
    """[loot.<怪>] pool='部位:品质:概率, ...' → {怪: [(部位, 品质, 概率)]}。"""
    table = {}
    for sec in cfg.sections():
        if not sec.startswith("loot."):
            continue
        rows = []
        for part in cfg[sec].get("pool", "").split(","):
            part = part.strip()
            if not part:
                continue
            slot, quality, chance = part.split(":")
            rows.append((slot.strip(), int(quality), int(chance)))
        table[sec[5:]] = rows
    return table


def roll(cfg, mon_key, player, storage, io, difficulty=0, rng=random):
    """胜利后掉落一次。返回掉落物品或 None；rng 可注入（测试用固定随机）。"""
    rows = load_table(cfg).get(mon_key, [])
    for slot, quality, chance in rows:
        if slot == "staff" and mon_key == "boss" and player.get("staff_pity", 0) >= 49 and not gear.has_staff(player, storage):
            chance = 100         # V2.9-A 保底：第 50 次 boss 必出无级别（pity≥49 时忽略随机数；已持有不强制）
        if rng.randint(1, 100) > chance:
            if slot == "staff" and mon_key == "boss" and not gear.has_staff(player, storage):
                player["staff_pity"] = player.get("staff_pity", 0) + 1
                io.say(f"  （无级别保底计数 {player['staff_pity']}/50）")
            continue
        if slot == "staff":      # 无级武器掉落：走 gear 唯一发放口
            got = gear.grant_staff(player, storage, io)
            if got is not None:
                player["staff_pity"] = 0  # V2.9-A：掷中清零
                return got
            continue             # 已持有 → 跳过，继续掷后面的普通掉落
        quality = min(2, quality + difficulty)
        try:
            item = gear.generate(slot, player["level"], quality)
        except ValueError as e:
            io.say(f"  （掉落失败：{e}）")
            return None
        bag = player.setdefault("inventory", [])
        if len(bag) < gear.capacity():
            bag.append(item)
            io.say(f"  🍂 掉落：{gear.item_line(item)}（已进背包）")
        else:
            storage.append(item)
            io.say(f"  🍂 掉落：{gear.item_line(item)}（背包已满，转入仓库）")
        return item
    return None
