# V2.7 技能系统 —— 技能表 + 被动汇总 + CD 表 + 菜单选择（DESIGN_V27 §3）。
# combat.py 只调本模块接口（已 130 行顶格，不许再往里塞技能逻辑）。
import configparser
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

ASSETS = os.path.join(HERE, "assets.mpak")


def load_skills():
    """合并 skills.txt（名/描述）+ game.ini（数值），返回 {id: skill}；主动/被动同表。"""
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "game.ini"), encoding="utf-8")
    text = mypack.read(ASSETS, "skills.txt").decode("utf-8")
    table = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        sid, name, desc = line.split("|")
        sec = "skill." + sid
        if not cfg.has_section(sec):
            raise ValueError(f"skills.txt 的 {sid} 在 game.ini 无 [{sec}] 段")
        s = {"id": sid, "name": name, "desc": desc,
             "kind": cfg.get(sec, "kind", fallback="active"),
             "unlock_lv": cfg.getint(sec, "unlock_lv", fallback=1),
             "power": cfg.getfloat(sec, "power", fallback=None),
             "mp_cost": cfg.getint(sec, "mp_cost", fallback=0),
             "cd": cfg.getint(sec, "cd", fallback=0),
             "hits": cfg.getint(sec, "hits", fallback=1),
             "heal_pct": cfg.getfloat(sec, "heal_pct", fallback=0.0),
             "dodge_buff": cfg.getfloat(sec, "dodge_buff", fallback=0.0) * 100,  # ini 0.30=30%，与 dodge 单位一致
             "crit_bonus": cfg.getfloat(sec, "crit_bonus", fallback=0.0),
             "atk_mult": cfg.getfloat(sec, "atk_mult", fallback=1.0),
             "mitigate": cfg.getfloat(sec, "mitigate", fallback=1.0)}
        if s["kind"] == "passive" and s["power"] is not None:
            raise ValueError(f"被动技能 {sid} 不得有 power（主动/被动串位）")
        table[sid] = s
    return table


def actives(skills):
    """主动技能列表（菜单固定顺序，与 skills.txt 行序一致）。"""
    return [s for s in skills.values() if s["kind"] == "active"]


def unlocked_skills(skills, level):
    """返回（已解锁主动，已解锁被动）两个列表；解锁按等级算，不进存档。"""
    acts = [s for s in actives(skills) if level >= s["unlock_lv"]]
    pas = [s for s in skills.values() if s["kind"] == "passive" and level >= s["unlock_lv"]]
    return acts, pas


def passive_totals(skills, level, totals):
    """被动汇总：返回 {"crit": 加成%, "atk_mult": 乘数, "mitigate": 乘数}；未解锁不计。
    汇总只此一处——engine.apply_gear 消费，combat.py 不许自己算。"""
    out = {"crit": 0.0, "atk_mult": 1.0, "mitigate": 1.0}   # 只算被动贡献；词条部分归 gear.totals
    for s in skills.values():
        if s["kind"] != "passive" or level < s["unlock_lv"]:
            continue
        out["crit"] += s["crit_bonus"] * 100
        out["atk_mult"] *= s["atk_mult"]
        out["mitigate"] *= s["mitigate"]
    return out


class Cooldowns:
    """战斗内 CD 表（不进存档）：use 置剩余回合，tick 回合结束递减，reset 出战斗清零。"""

    def __init__(self):
        self.left = {}                       # skill_id → 剩余回合

    def usable(self, sid):
        return self.left.get(sid, 0) <= 0

    def remain(self, sid):
        return self.left.get(sid, 0)

    def use(self, sid, cd):
        if cd > 0:
            self.left[sid] = cd

    def tick(self):
        self.left = {k: v - 1 for k, v in self.left.items() if v > 1}

    def reset(self):
        self.left.clear()


def choose(skills, player, io, cds):
    """技能菜单：列全部主动技能（未解锁/CD/MP 不足均灰字不可选）。
    返回 (power, hits, heal_pct, dodge_buff)；取消或非法输入返回 None（不耗回合）。"""
    acts = actives(skills)
    for i, s in enumerate(acts, 1):
        if player["level"] < s["unlock_lv"]:
            tag = f"（Lv.{s['unlock_lv']} 解锁）"
        elif not cds.usable(s["id"]):
            tag = f"（冷却中，剩 {cds.remain(s['id'])} 回合）"
        elif player["mp"] < s["mp_cost"]:
            tag = "（MP 不足）"
        else:
            tag = ""
        io.say(f"  {i} {s['name']}（威力 x{s['power']}，耗蓝 {s['mp_cost']}）{s['desc']}{tag}")
    pick = io.ask("选技能 > ").strip()
    if not pick.isdigit() or not 1 <= int(pick) <= len(acts):
        io.say("没有这个技能。")
        return None
    s = acts[int(pick) - 1]
    if player["level"] < s["unlock_lv"]:
        io.say(f"{s['name']} 要 Lv.{s['unlock_lv']} 才解锁。")
        return None
    if not cds.usable(s["id"]):
        io.say(f"{s['name']} 冷却中。")
        return None
    if player["mp"] < s["mp_cost"]:
        io.say("蓝不够了！")
        return None
    player["mp"] -= s["mp_cost"]
    cds.use(s["id"], s["cd"])
    return s["power"], s["hits"], s["heal_pct"], s["dodge_buff"]


def leech_heal(player, dmg, io):
    """吸血（leech 已在 gear.totals 收口 10% 上限，这里只做按伤害回血）。"""
    heal = int(dmg * player["leech"])
    if heal > 0 and player["hp"] < player["max_hp"]:
        player["hp"] = min(player["max_hp"], player["hp"] + heal)
        io.say(f"  血脉倒卷，吸血回复 {heal} 点血")


def weapon_effect(player, mon):
    """武器谱 vs_tribe 特效：紫档武器 effect 匹配怪物 tribe 时返回倍率，否则 1.0。"""
    w = (player.get("equipment") or {}).get("weapon") or {}
    eff = w.get("effect") or {}
    kind = eff.get("kind", "")
    if kind.startswith("vs_tribe:") and mon.get("tribe") == kind.split(":", 1)[1]:
        return float(eff.get("param", 1))
    return 1.0
