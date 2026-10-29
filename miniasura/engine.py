# MiniAsura V2.2 引擎 —— 推图 + 任务 + 对话编排；战斗流程住 combat.py，数值公式住 Lua。
# 契约：引擎只掷骰与调度；任务状态机住 quests.py；对话播放走 io 抽象（CLI/GUI 通用）。
import configparser
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack
import save; import encounter
import gear
import combat
import loot
import rewards
from combat import battle, grant_exp, roll_damage, lua   # 再导出：外部依赖 engine.grant_exp
import dialogue as dlg
import quests as qsys
import skills as skills_mod

ASSETS = ("intro.txt", "skills.txt", "monsters.txt",
          "dialogue.txt", "quests.txt", "maps.txt")


class CliIo:
    def say(self, msg=""):
        print(msg)

    def ask(self, prompt):
        return input(prompt)


def load_texts():
    pack = os.path.join(HERE, "assets.mpak")
    return {n: mypack.read(pack, n).decode("utf-8") for n in ASSETS}


def parse_kv(text):
    table = {}
    for line in text.splitlines():
        if line.strip() and not line.startswith("#"):   # monsters.txt V2.7 起有注释行
            parts = line.split("|")
            table[parts[0]] = tuple(parts[1:])          # 列数不限：skills 2 列 / monsters 3 列（名/intro/tribe）
    return table


def player_attack(cfg, level):
    # 公式住 battle.lua，参数仍来自 ini
    return lua("attack", cfg.getint("player", "base_attack"), level, cfg.getint("growth", "attack_per_level"))["attack"]


def apply_gear(cfg, player):
    # 装备加成只消费 gear.totals 的聚合结果（公式住 equip.lua）；V2.5 起 totals 要吃持有者等级
    tot = gear.totals(player.get("equipment") or gear.empty_equipment(), player["level"])
    pas = skills_mod.passive_totals(skills_mod.load_skills(), player["level"], tot)   # V2.7 被动唯一汇总处
    player["attack"] = round((player_attack(cfg, player["level"]) + tot["atk"]) * pas["atk_mult"])
    player["max_hp"] = round(cfg.getint("player", "hp") + (player["level"] - 1)
                             * cfg.getint("growth", "hp_per_level") + tot["hp"])
    player["def"], player["dodge"] = tot["def"], tot["dodge"]   # V2.7 闪避（靴子+词条+筋斗云 buff）
    player["hit"] = tot.get("hit", 0.0)                         # V2.7 命中（弥陀弓）
    player["mitigate"] = pas["mitigate"]                        # V2.7 不坏金身减伤
    player["crit_rate"] = min(100, cfg.getint("player", "crit_rate") + tot["crit"] + pas["crit"])
    player["critdmg"], player["leech"], player["exp_bonus"] = (tot["critdmg"] / 100,
                                                               tot["leech"] / 100, tot["exp"] / 100)


def build_maps(text, cfg, monsters, difficulty=0):
    # maps.txt: 序号|地图名|怪物key(-=无)|对话id|难度倍率 → 战斗按倍率缩放；V2.3 再乘难度倍率（金币/经验同乘奖励倍率）
    stat_mult, reward_mult = loot.DIFF_MULT[difficulty]
    maps = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        no, name, mons, did, scale = line.split("|")
        scale = float(scale)
        fights = []
        for key in ([] if mons == "-" else mons.split(",")):
            base = cfg["monster." + key]
            fights.append({"key": key, "mon": {
                # key 必须放进 mon：battle 靠 mon["key"]=="boss" 判定逃跑必失败（V2.4 补丁）
                "key": key, "name": monsters[key][0], "intro": monsters[key][1],
                "tribe": monsters[key][2] if len(monsters[key]) > 2 else "无",   # V2.7 vs_tribe 特效匹配
                "hp": round(int(base["hp"]) * scale * stat_mult),
                "atk": round(int(base["attack"]) * scale * stat_mult),
                "exp": round(int(base["exp"]) * scale * reward_mult),
                "gold": round(int(base.get("gold", 0)) * scale * reward_mult)}})
        maps.append({"no": int(no), "name": name, "fights": fights, "did": did})
    return maps


def total_fights():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    texts = load_texts()
    return sum(len(m["fights"]) for m in build_maps(
        texts["maps.txt"], cfg, parse_kv(texts["monsters.txt"])))


def finish_summary(io, player, tracker, cleared, total, week, monsters, difficulty):
    # 通关结算（自 run_game 抽出给 engine 腾行数）：等级/任务/图/金币/击杀明细
    io.say("\n══════ 通关结算 ══════\n白骨夫人倒下，水帘洞地契物归原主！")
    io.say(f"最终等级 Lv.{player['level']}   HP {player['hp']}   MP {player['mp']}"
           f"   金币 {player.get('gold', 0)}   难度 {loot.DIFF_NAMES[difficulty]}")
    io.say("任务：" + " ".join(f"{q['name']}[{tracker.state(q['key'])}]" for q in tracker.qs.values()))
    io.say(f"地图推进 {cleared}/{total}   第 {week} 周目   击杀：" + (" ".join(
        f"{monsters[k][0]}x{v}" for k, v in tracker.kills.items() if not k.startswith("lose:")) or "无")
        + "\n（通关一次后解锁「无底洞」：GUI 大厅进塔，或 CLI 跑 python tower.py）")


def run_game(io):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    texts = load_texts()
    skills = skills_mod.load_skills()      # V2.7：技能表（名+数值合并），combat 只消费
    monsters = parse_kv(texts["monsters.txt"])
    dialogues = dlg.load(texts["dialogue.txt"])
    io.say(texts["intro.txt"])

    state = save.load()
    week = base_playtime = maps_cleared = start = 0
    difficulty, tracker = None, None
    gold_carry = protect_carry = tower_carry = 0; dmg_carry = 0; pity_carry = 0
    storage = []
    if state and state.get("next", 0) >= total_fights():
        io.say(f"\n（检测到已通关的存档：第 {state.get('week', 0)} 周目已完结——开启第 {state.get('week', 0) + 1} 周目，从头再来！）")
        week = state.get("week", 0)
        base_playtime = state.get("playtime", 0)
        tracker = qsys.Tracker(qsys.load(texts["quests.txt"]),
                               state.get("quest_flags"), state.get("kills"))
        storage = state.get("storage", [])
        difficulty = loot.ask_difficulty(io)   # 新周目重问难度
        gold_carry, protect_carry = state.get("gold", 0), state.get("protect", 0); dmg_carry = state.get("total_damage", 0); pity_carry = state.get("staff_pity", 0)  # 金币/保底符/总伤害/保底计数跨周目继承
        tower_carry = state.get("tower_best", 0)      # V2.5：爬塔最高层跨周目继承
        state = None        # 周目重开：等级回起点；任务/仓库/金币继承
    elif state:
        io.say(f"\n（读取存档：Lv.{state['level']}，已推进至第 {state.get('maps_cleared', 0) + 1} 图）")
        week = state.get("week", 0)
        base_playtime = state.get("playtime", 0)
        maps_cleared = state.get("maps_cleared", 0)
        start = state["next"]
        difficulty = state.get("difficulty", 0)   # 续档不重问难度
        storage = state.get("storage", [])
        tracker = qsys.Tracker(qsys.load(texts["quests.txt"]),
                               state.get("quest_flags"), state.get("kills"))
        player = {"level": state["level"], "exp": state["exp"],
                  "hp": state["hp"], "mp": state["mp"], "gold": state.get("gold", 0), "protect": state.get("protect", 0),
                  "inventory": state.get("inventory", []),
                  "equipment": state.get("equipment") or gear.empty_equipment(),
                  "potions": state.get("potions") or {"hp": 0, "mp": 0},
                  "tower_best": state.get("tower_best", 0), "tower_layer": state.get("tower_layer", 0), "total_damage": state.get("total_damage", 0), "staff_pity": state.get("staff_pity", 0)}
        apply_gear(cfg, player)
        player["hp"] = min(player["hp"], player["max_hp"])
    if not state:
        player = {"level": cfg.getint("player", "level"), "exp": 0,
                  "mp": cfg.getint("player", "mp"), "gold": gold_carry, "protect": protect_carry,
                  "inventory": [], "equipment": gear.empty_equipment(),
                  "potions": {"hp": 0, "mp": 0}, "tower_best": tower_carry, "tower_layer": 0, "total_damage": dmg_carry, "staff_pity": pity_carry}
        tracker = tracker or qsys.Tracker(qsys.load(texts["quests.txt"]))
        apply_gear(cfg, player)
        player["hp"] = player["max_hp"]          # 新档满血进本
    difficulty = loot.ask_difficulty(io) if difficulty is None else difficulty
    maps = build_maps(texts["maps.txt"], cfg, monsters, difficulty)

    def persist(next_index, cleared):
        save.write(player, next_index, week, base_playtime + int(time.time() - t0), maps_cleared=cleared,
                   tracker=tracker, storage=storage, difficulty=difficulty)

    t0 = time.time()
    fi = 0
    for m in maps:
        if m["no"] <= maps_cleared:
            fi += len(m["fights"])
            continue
        io.say(f"\n───── 第 {m['no']} 图 · {m['name']} ─────")
        if dlg.play(io, dialogues, m["did"]):            # 看完才推进 talk 任务
            for q in tracker.on_event("talk", m["did"]):
                rewards.apply_rewards(cfg, player, io, [q], storage)
        for f in m["fights"]:
            if fi < start:
                fi += 1
                continue
            rep = {}; encounter.apply_encounter(f, week, m["no"], fi, cfg); result = battle(cfg, skills, f["mon"], player, io, rep)
            if result == "dead":
                for q in tracker.on_event("lose", f["key"]):   # 败北事件（门禁 Bug B）
                    rewards.apply_rewards(cfg, player, io, [q], storage)
                rewards.apply_death_penalty(player, io)
                player["hp"] = player["max_hp"]; encounter.print_report(io, rep)   # V2.4：先扣 10% 经验，再满血拖回水帘洞疗伤；V2.9-A：败北也打印战报
                persist(fi, maps_cleared)          # 落盘败局：跨局败北计数才可能累积
                io.say("\n你倒下了……老猴把你拖回水帘洞疗伤。存档已更新，练练再来。")
                return
            if result == "escaped":
                # 逃跑语义（2026-10-28 补丁定版）：不算推进、不发通图、
                # 不记击杀——只落盘到本场开打前的位置，回大厅后重打本场。
                # 之前这里与 win 共用 fi += 1，导致一路逃跑也能通关。
                persist(fi, maps_cleared)
                io.say("\n你溜出了战场。这一场不算打过，回大厅后可重打。")
                return
            if result == "win":
                for q in tracker.on_event("win", f["key"]):
                    rewards.apply_rewards(cfg, player, io, [q], storage)
                loot.grant_win(cfg, f, player, storage, io, difficulty); encounter.print_report(io, rep)
            fi += 1
            persist(fi, maps_cleared)
        for q in tracker.on_event("map", m["no"]):
            rewards.apply_rewards(cfg, player, io, [q], storage)
        maps_cleared = m["no"]
        persist(fi, maps_cleared)
        if m["no"] == len(maps):
            week += 1
            persist(fi, maps_cleared)

    finish_summary(io, player, tracker, maps_cleared, len(maps), week, monsters, difficulty)


def main():
    run_game(CliIo())


if __name__ == "__main__":
    main()
