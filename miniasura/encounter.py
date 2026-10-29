# V2.9-A 遭遇层 —— BOSS 阈值变招 / 精英稀有判定 / 战报打印 / V29 校验。
# 引擎与战斗只调这里的入口，不在本文件外写 V2.9-A 规则；数据全在 game.ini，不动 mpak。
import hashlib


def _cfg_int(cfg, sec, key, default):
    try:
        return cfg.getint(sec, key)
    except Exception:
        return default


def _cfg_float(cfg, sec, key, default):
    try:
        return cfg.getfloat(sec, key)
    except Exception:
        return default


class BossPhase:
    """boss 阈值变招（DESIGN_V2_9_A §1.2）：变身/骨刺雨/狂暴，只对 key == 'boss' 生效。"""

    def __init__(self, mon, cfg):
        self.mon = mon
        self.max_hp = mon.get("hp", 1) or 1
        self.transformed = False
        self.enraged = False
        self.monster_turns = 0
        self.vuln = 1.0
        self.spike_every = _cfg_int(cfg, "boss_phase", "spike_every", 3)
        self.spike_pct = _cfg_int(cfg, "boss_phase", "spike_pct", 5)
        self.transform_pct = _cfg_int(cfg, "boss_phase", "transform_hp_pct", 50)
        self.enrage_pct = _cfg_int(cfg, "boss_phase", "enrage_hp_pct", 20)
        self.transform_mult = _cfg_float(cfg, "boss_phase", "transform_atk_mult", 1.2)
        self.enrage_mult = _cfg_float(cfg, "boss_phase", "enrage_atk_mult", 1.2)
        self.enrage_vuln = _cfg_float(cfg, "boss_phase", "enrage_vuln_mult", 1.2)

    def _boost_atk(self, mult):
        old = self.mon.get("atk", 0)
        self.mon["atk"] = max(old + 1, round(old * mult)) if old else old

    def check(self, m_hp, io):
        """每回合开打前按当前血量检查阈值；非 boss 怪不调用（combat 只对 boss 建 BossPhase）。"""
        if m_hp <= 0:
            return
        if not self.transformed and m_hp * 100 <= self.max_hp * self.transform_pct:
            self.transformed = True
            self._boost_atk(self.transform_mult)
            io.say(f"{self.mon.get('name', '白骨夫人')}现出白骨真身！攻击提升！")
        if self.transformed and not self.enraged and m_hp * 100 <= self.max_hp * self.enrage_pct:
            self.enraged = True
            self._boost_atk(self.enrage_mult)
            self.vuln = self.enrage_vuln
            io.say(f"{self.mon.get('name', '白骨夫人')}狂暴了！攻击提升，但破绽也更大了！")

    def spike(self, player, io, rep):
        """怪物回合结束时调用：变身后每 spike_every 个怪物回合放一次骨刺雨（固定伤害，不吃防御）。"""
        if not self.transformed:
            return
        self.monster_turns += 1
        if self.monster_turns % self.spike_every != 0:
            return
        dmg = max(5, round(player.get("max_hp", 0) * self.spike_pct / 100))
        player["hp"] -= dmg
        if rep is not None:
            rep["taken"] = rep.get("taken", 0) + dmg
        io.say(f"骨刺雨落下，你损失 {dmg} 点血（无视防御）！")


ELITE_AFFIXES = ("armor", "burn", "swift")  # 甲硬 / 灼烧 / 疾风


def roll_kind(week, map_no, fi):
    """确定性掷骰：md5(week:map:fi) → r ∈ [0, 99)，与进程随机种子无关，重打同一场结果相同。"""
    h = hashlib.md5(f"{week}:{map_no}:{fi}".encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % 100


def apply_encounter(fight, week, map_no, fi, cfg):
    """主线开打前包装一场战斗：boss 不动；非 boss 按 roll_kind 决定普通/精英/稀有。"""
    mon = fight.get("mon") or {}
    if mon.get("key") == "boss":
        return fight
    r = roll_kind(week, map_no, fi)
    elite = _cfg_int(cfg, "encounter", "elite_chance", 20)
    rare = _cfg_int(cfg, "encounter", "rare_chance", 5)
    if r < elite:
        affix = ELITE_AFFIXES[r % len(ELITE_AFFIXES)]
        mon["hp"] = round(mon["hp"] * _cfg_float(cfg, "encounter", "elite_hp_mult", 1.5))
        mon["atk"] = round(mon["atk"] * _cfg_float(cfg, "encounter", "elite_atk_mult", 1.2))
        if affix == "burn":
            mon["atk"] = round(mon["atk"] * 1.3)
        if affix == "armor":
            mon["dmg_mult"] = 0.85
        if affix == "swift":
            mon["dodge"] = 20
        mon["name"] = "精英·" + mon["name"]
        fight["elite"] = affix
    elif r < elite + rare:
        mon["hp"] = max(1, round(mon["hp"] * _cfg_float(cfg, "encounter", "rare_hp_mult", 0.5)))
        mon["atk"] = max(1, round(mon["atk"] * _cfg_float(cfg, "encounter", "rare_atk_mult", 0.5)))
        mon["name"] = "金色·" + mon["name"]
        mon["rare"] = True   # V2.9-B：combat 只收 mon，稀有标记必须随 mon 传递
        fight["rare"] = True
    return fight


def print_report(io, rep):
    """战报（DESIGN_V2_9_A §1.1）：只打印，不改数值；V2.9-C 起优先走 io.report 富通道。"""
    if not rep: return
    line = (f"战报：{rep.get('rounds', 0)}回合 / 造成{rep.get('dealt', 0)}伤害 / "
            f"承受{rep.get('taken', 0)}伤害 / 暴击{rep.get('crits', 0)}次 / MISS {rep.get('misses', 0)}次")
    io.report(rep, line) if hasattr(io, "report") else io.say(line)


def check_v29(cfg):
    """V29-01 boss_phase 阈值合法 / V29-02 encounter 概率与倍率合法 / V29-03 保底与额外掉落池合法。"""
    bad1 = []
    bp = cfg["boss_phase"] if cfg.has_section("boss_phase") else {}
    try:
        t, e = int(bp["transform_hp_pct"]), int(bp["enrage_hp_pct"])
        if not (0 < e < t < 100) or int(bp["spike_every"]) < 1 or int(bp["spike_pct"]) <= 0:
            bad1.append("boss_phase 阈值/骨刺参数非法")
        for k in ("transform_atk_mult", "enrage_atk_mult", "enrage_vuln_mult"):
            if float(bp[k]) <= 1.0:
                bad1.append(f"boss_phase {k} 必须 > 1")
    except Exception:
        bad1.append("boss_phase 缺字段")
    bad2 = []
    try:
        ec = cfg.getint("encounter", "elite_chance")
        rc = cfg.getint("encounter", "rare_chance")
        if not (0 <= ec <= 50 and 0 <= rc <= 50 and ec + rc <= 50):
            bad2.append("encounter 概率越界")
        for k in ("elite_hp_mult", "elite_atk_mult"):
            if cfg.getfloat("encounter", k) <= 1.0:
                bad2.append(f"encounter {k} 必须 > 1")
        for k in ("rare_hp_mult", "rare_atk_mult"):
            if not 0 < cfg.getfloat("encounter", k) < 1.0:
                bad2.append(f"encounter {k} 必须在 (0, 1)")
    except Exception:
        bad2.append("encounter 缺字段")
    bad3 = []
    try:
        if cfg.getint("pity", "staff_pity_max") != 50:
            bad3.append("pity staff_pity_max 必须 = 50")
        for sec, slot in (("loot.elite", "weapon"), ("loot.rare", "weapon")):
            pool = cfg.get(sec, "pool", fallback="")
            if not pool.startswith(slot + ":"):
                bad3.append(f"{sec} 池非法")
    except Exception:
        bad3.append("pity/loot.elite/loot.rare 缺字段")
    return [("13 BOSS 阈值合法（V29-01）", (not bad1, bad1)),
            ("14 精英稀有参数合法（V29-02）", (not bad2, bad2)),
            ("15 保底与额外掉落池合法（V29-03）", (not bad3, bad3))]

def is_rare(mon): return bool(mon.get("rare"))   # 看字段，不靠“金色·”名前缀

def fled_check(mon, rep, player, io, flee_rounds=3):
    if not is_rare(mon) or player.get("hp", 0) <= 0: return None   # combat 保证怪活着；玩家死亡则外层 dead 优先
    rounds = rep.get("rounds", 0)
    if rounds >= flee_rounds:
        io.say(f"{mon['name']}溜走了！紫装机会没了。"); return "fled"
    if rounds >= flee_rounds - 1: io.say(f"{mon['name']}看起来要溜走了！")
    return None

def check_v30(cfg):
    try: n = cfg.getint("rare_flee", "flee_rounds"); ok = n >= 2; detail = [] if ok else ["flee_rounds 必须 >= 2"]   # V30-01：至少留一个预警回合
    except Exception: ok, detail = False, ["[rare_flee] flee_rounds 缺失或不是整数"]
    return [("16 稀有逃跑回合合法（V30-01）", (ok, detail))]
