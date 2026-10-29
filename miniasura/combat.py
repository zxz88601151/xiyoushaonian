# V2.2 战斗流程模块（自 engine.py 拆出）—— 流程在这里，数值公式仍在 scripts/battle.lua：引擎只掷骰。
# V2.7：技能菜单/CD/连击/吸血住 skills.py；命中/闪避掷骰在这里（概率归引擎，公式蓝图 §1.3）。
import json
import os
import random
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LUA = os.path.join(HERE, "..", "tools", "lua-5.1.5", "lua.exe")
BATTLE_LUA = os.path.join(HERE, "scripts", "battle.lua")

import skills as sk


def lua(*args):
    # 引擎与脚本只传一行 JSON；argv 全数字（编码铁律），stdout 里只取含 { 的那行
    out = subprocess.run([LUA, BATTLE_LUA] + [str(a) for a in args],
                         capture_output=True, text=True, encoding="utf-8").stdout
    line = next(l for l in out.splitlines() if "{" in l).strip()
    return json.loads(line)


def roll_damage(player, power, effect=1.0):
    # 两颗骰都归引擎（暴击率/浮动来自概率），倍率/暴伤/公式归 Lua；effect = 武器谱特效倍率
    crit = random.randint(1, 100) <= player["crit_rate"]
    rand = random.randint(95, 105)
    res = lua("damage", player["attack"], power, 1 if crit else 0,
              f"{player['critdmg']:.4f}", rand, f"{effect:.2f}")
    return res["dmg"], res["crit"]


def grant_exp(cfg, player, io, amount):
    amount = int(amount * (1 + player.get("exp_bonus", 0)))   # 经验加成词条（V2.1）
    g = cfg["growth"]   # V2.5：每级所需 = exp_base × 距开局级数^曲线（公式住 battle.lua）
    res = lua("levelup", player["exp"], amount, player["level"], g.getint("level_cap"),
              g.getint("exp_base"), g.getint("exp_pow_x100"),
              player["level"] - cfg.getint("player", "level") + 1)
    old = player["level"]
    player["level"], player["exp"] = res["level"], res["exp"]
    if player["level"] > old:
        from engine import apply_gear; apply_gear(cfg, player)   # 升级重算全属性（F1 回归）
        player["hp"] = player["max_hp"]   # V2.6：升级回满血——否则十图磨血必死于终幕
        io.say(f"  ★ 升级！现在 Lv.{player['level']}，攻击力 {player['attack']}，HP 回满")


def use_potion(cfg, player, io):
    """战斗内用药（V2.2 商店闭环的验证端）。用了=True → 怪物照样反击（回合照过）。"""
    pot = player.get("potions") or {}
    io.say(f"  1 血瓶 x{pot.get('hp', 0)}（回{cfg.getint('potion', 'hp_pct')}%上限）"
           f"   2 蓝瓶 x{pot.get('mp', 0)}（回{cfg.getint('potion', 'mp_flat')}蓝）")
    pick = io.ask("用什么 > ").strip()
    if pick == "1" and pot.get("hp", 0) > 0:
        pot["hp"] -= 1
        heal = round(player["max_hp"] * cfg.getint("potion", "hp_pct") / 100)
        player["hp"] = min(player["max_hp"], player["hp"] + heal)
        io.say(f"  咬下一口仙桃，回血 {heal}！")
        return True
    if pick == "2" and pot.get("mp", 0) > 0:
        pot["mp"] -= 1
        mana = cfg.getint("potion", "mp_flat")
        player["mp"] = min(cfg.getint("player", "mp"), player["mp"] + mana)
        io.say(f"  抿一口玉液，回蓝 {mana}！")
        return True
    io.say("  （没有可用的药——重新选择行动）")
    return False


def battle(cfg, skills, mon, player, io):
    """skills = skills.load_skills() 技能表（V2.7）；契约不变：返回 win/dead/escaped。"""
    name, m_hp, m_atk, m_exp = mon["name"], mon["hp"], mon["atk"], mon["exp"]
    io.say(f"\n═══ {name} 出现！「{mon['intro']}」")
    cds, buff = sk.Cooldowns(), 0.0          # 战斗内 state：CD 表 + 筋斗云闪避 buff（仅下回合，D5 加法叠加）
    effect = sk.weapon_effect(player, mon)   # 武器谱 vs_tribe 特效倍率（无特效 1.0，整场固定）
    while m_hp > 0:
        io.say(f"\n[{name} HP {m_hp}]  你 HP {player['hp']}/{player['max_hp']}  MP {player['mp']}"
               f"  攻击力 {player['attack']}  防御 {player['def']:.1f}  闪避 {player.get('dodge', 0):.0f}%")
        act = io.ask("1 普攻 / 2 技能 / 3 逃跑 / 4 物品 > ").strip()
        power = hits = heal_pct = None
        if act == "3":
            if mon.get("key") == "boss":
                io.say("夫人的骨刺封死了场地——逃跑失败！")
                continue
            io.say("你脚底抹油，溜了（无经验）。")
            return "escaped"
        elif act == "4":
            if use_potion(cfg, player, io):
                pass                      # 用药花回合：怪物照样出手
            else:
                continue
        elif act == "1":
            power, hits = cfg.getfloat("fight", "normal_power"), 1
        elif act == "2":
            pick = sk.choose(skills, player, io, cds)     # 菜单/解锁/CD/MP 校验全在 skills.py
            if not pick:
                continue
            power, hits, heal_pct, buff_add = pick
            buff += buff_add or 0.0
        else:
            io.say("看不懂的指令。")
            continue
        if power is not None:
            for _ in range(hits):              # 连击：每段独立命中判定；MISS 不触发暴击/吸血/连击后续段
                # 命中率 = 95% + 命中 − 目标闪避，下限 60%（蓝图 §1.3，概率掷骰归引擎）
                if random.randint(1, 100) > max(60, 95 + player.get("hit", 0) - mon.get("dodge", 0)):
                    io.say("MISS！")
                    break
                dmg, crit = roll_damage(player, power, effect)
                m_hp -= dmg; player["total_damage"] = player.get("total_damage", 0) + dmg
                io.say(f"你打出 {dmg} 点伤害{'，暴击！' if crit else ''}")
                sk.leech_heal(player, dmg, io)
            if heal_pct:                       # 如意神通：倍率 5.0 之外回复 20% HP
                h = round(player["max_hp"] * heal_pct)
                player["hp"] = min(player["max_hp"], player["hp"] + h)
                io.say(f"  神通运转，回复 {h} 点血")
        if m_hp <= 0:
            break
        if random.randint(1, 100) <= player.get("dodge", 0) + buff:   # 怪物攻击：闪避判定（buff 加法叠加）
            io.say(f"你身形一晃，闪开了 {name} 的攻击！")
        else:
            taken = lua("incoming", m_atk, f"{player['def']:.2f}", f"{player.get('mitigate', 1):.2f}")["dmg"]
            player["hp"] -= taken
            block = f"（防御格挡 {m_atk - taken}）" if taken < m_atk else ""
            io.say(f"{name} 反击，你损失 {taken} 点血{block}")
        buff = 0.0                       # 闪避 buff 仅下回合，回合结束清除
        cds.tick()
        if player["hp"] <= 0:
            return "dead"
    io.say(f"{name} 倒下了！获得 {m_exp} 点经验。")
    grant_exp(cfg, player, io, m_exp)
    return "win"
