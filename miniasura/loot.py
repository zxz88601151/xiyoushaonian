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
    """胜利结算：金币入账 + 掉落掷骰（引擎主循环只调这一行）。"""
    gold = fight["mon"].get("gold", 0)
    if gold:
        player["gold"] = player.get("gold", 0) + gold
        io.say(f"  获得金币 {gold}！")
    roll(cfg, fight["key"], player, storage, io, difficulty=difficulty)


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
        if rng.randint(1, 100) > chance:
            continue
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
