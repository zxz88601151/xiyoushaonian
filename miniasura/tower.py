# V2.5 无底洞爬塔 —— 层数即怪物等级；数值住 game.ini [tower]，战斗复用 combat.battle。
# 只做调度与结算：CLI 与 GUI 共用 run_one；解锁=通关一次，死亡/撤离→本次清零、最高层保留。
import configparser, os, random, sys

import combat, engine, gear, loot, save   # engine 只用于 apply_gear/读资源，不反向依赖 tower

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cfg():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    return cfg


def unlocked(state):
    # OD-V25-03：通关一次后解锁（周目 ≥1 或已爬过塔）
    return bool(state) and (state.get("week", 0) >= 1 or state.get("tower_best", 0) > 0)


def layer_mon(cfg, n):
    # 第 N 层：层数即等级；每 boss_every 层是守层妖王（key=boss → 逃跑必失败）
    t = cfg["tower"]
    boss = n % t.getint("boss_every", 10) == 0
    return {"key": "boss" if boss else "tower",
            "name": "无底洞 %d 层·%s" % (n, "守层妖王" if boss else "游魂"), "intro": "越往下越暗，妖气浓得化不开。",
            "hp": round(t.getint("hp_base") + n * t.getfloat("hp_per_layer")),
            "atk": round(t.getint("atk_base") + n * t.getfloat("atk_per_layer")),
            "exp": round(t.getint("exp_base") * n ** (t.getint("exp_pow_x100", 165) / 100)),
            "gold": round(t.getint("gold_base") + n * t.getfloat("gold_per_layer"))}


def load_player(cfg, state):
    # 按存档重建玩家（与 engine 续档同一套字段）；爬塔不吃任务进度
    player = {"level": state["level"], "exp": state["exp"], "hp": state["hp"],
              "mp": state["mp"], "gold": state.get("gold", 0), "protect": state.get("protect", 0),
              "inventory": state.get("inventory", []),
              "equipment": state.get("equipment") or gear.empty_equipment(),
              "potions": state.get("potions") or {"hp": 0, "mp": 0},
              "tower_best": state.get("tower_best", 0),
              "tower_layer": state.get("tower_layer", 0)}
    engine.apply_gear(cfg, player)
    player["hp"] = min(player["hp"] or player["max_hp"], player["max_hp"])
    return player


def run_one(cfg, skills, player, storage, io, rng=random):
    # 爬一层：胜则金币/经验入账、推层号、逢 drop_every 掉一次。
    # 死亡或撤离 → 本次层数清零，tower_best 保留（续爬语义）
    n = player.get("tower_layer", 0) + 1
    mon = layer_mon(cfg, n)
    io.say("\n═══ 无底洞 第 %d 层（怪物等级 %d）═══" % (n, n))
    result = combat.battle(cfg, skills, mon, player, io)
    if result != "win":
        player["tower_layer"] = 0
        io.say("  本次止于第 %d 层（历史最高 %d 层）。" % (n - 1, player.get("tower_best", 0)))
        return result
    player["gold"] = player.get("gold", 0) + mon["gold"]
    io.say("  获得金币 %d！" % mon["gold"])
    combat.grant_exp(cfg, player, io, mon["exp"])
    player["tower_layer"], player["tower_best"] = n, max(player.get("tower_best", 0), n)
    if n % cfg["tower"].getint("drop_every", 5) == 0:
        loot.roll(cfg, "tower", player, storage, io, rng=rng)
    io.say("  ▸ 已到第 %d 层（历史最高 %d 层）" % (n, player["tower_best"]))
    return "win"


def persist(state, player, storage):
    # 写回存档：只动玩家字段与仓库，任务/图进度原样带回（不经引擎主循环）
    for k in ("level", "exp", "hp", "mp", "gold", "inventory", "equipment", "potions",
              "tower_best", "tower_layer"):
        state[k] = player[k]
    state["storage"] = storage
    save.write_raw(state)


def main():
    cfg = load_cfg()
    io = engine.CliIo()
    state = save.load()
    if not state:
        sys.exit("还没有存档——先跑一次 engine.py 创建角色。")
    if not unlocked(state):
        sys.exit("无底洞尚未解锁：通关一次（第 1 周目完结）后才会出现入口。")
    skills = engine.parse_kv(engine.load_texts()["skills.txt"])
    player, storage = load_player(cfg, state), state.get("storage", [])
    io.say("═══ 无底洞（历史最高 %d 层，本次从第 %d 层继续）═══" % (player["tower_best"], player["tower_layer"] + 1))
    try:
        while run_one(cfg, skills, player, storage, io) == "win":
            if io.ask("\n1 继续深入 / 2 撤离 > ").strip() == "2":
                io.say("你撤回洞口，本次层数清零（历史最高层保留）。")
                player["tower_layer"] = 0
                break
    except EOFError:      # 输入中断（Ctrl-D / 管道断流）：保住已爬进度，别让玩家白爬
        io.say("（输入中断，已保存当前进度）")
    persist(state, player, storage)


if __name__ == "__main__":
    main()
