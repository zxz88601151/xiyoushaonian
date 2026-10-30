# V2.9-B 出口验收 · 七门禁（DESIGN_V2_9_B §5）
# 爬塔战报 / 稀有 fled 推进 / 不误伤 / dead 优先 / escaped 不变 / 回归 / 行数与 validate。
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.chdir(HERE)
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

import shutil as _sh0
for _f in ("save.json", "session.json", "accounts.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh0.rmtree("saves", ignore_errors=True)

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name, flush=True)


import combat
import encounter
import engine
import gear
import save
import skills
import tower

CFG = tower.load_cfg()
SKILLS = skills.load_skills()


class Io:
    def __init__(self, actions=None):
        self.said = []
        self.actions = list(actions or [])

    def say(self, m=""):
        self.said.append(m)

    def ask(self, p=""):
        return self.actions.pop(0) if self.actions else "1"


def base_player(attack=200, hp=1000):
    return {"level": 25, "exp": 0, "hp": hp, "mp": 100, "max_hp": hp, "attack": attack,
            "def": 0.0, "dodge": 0, "hit": 0, "mitigate": 1.0, "crit_rate": 0,
            "critdmg": 0.0, "leech": 0.0, "exp_bonus": 0.0, "gold": 0, "protect": 0,
            "inventory": [], "equipment": gear.empty_equipment(),
            "potions": {"hp": 0, "mp": 0}, "total_damage": 0, "staff_pity": 0,
            "tower_layer": 0, "tower_best": 0}


def rare_mon(**kw):
    mon = {"key": "huoyao", "name": "金色·火妖", "intro": "！", "tribe": "火抗",
           "hp": 99999, "atk": 10, "exp": 10, "gold": 20, "rare": True}
    mon.update(kw)
    return mon


def week3_save():
    return {"schema": save.SCHEMA, "user": "", "level": 25, "exp": 0, "hp": 1000, "mp": 100,
            "attack": 90, "next": 5, "week": 3, "playtime": 0, "gold": 123, "difficulty": 0,
            "protect": 0, "inventory": [], "equipment": gear.empty_equipment(), "quest_flags": {},
            "kills": {}, "maps_cleared": 6, "potions": {"hp": 0, "mp": 0}, "storage": [],
            "tower_best": 0, "tower_layer": 0, "achievements": [], "codex_weapons": [],
            "total_damage": 0, "staff_pity": 0}


# ── 门禁1：B1 爬塔战报 win/dead 打印，escaped 不打印 ──
io_win, io_dead, io_esc = Io(), Io(), Io(["3"])
r_win = tower.run_one(CFG, SKILLS, base_player(attack=9999), [], io_win)
r_dead = tower.run_one(CFG, SKILLS, base_player(attack=0, hp=1), [], io_dead)
r_esc = tower.run_one(CFG, SKILLS, base_player(attack=0), [], io_esc)
check("1 爬塔战报：win/dead 打印、escaped 不打印",
      r_win == "win" and r_dead == "dead" and r_esc == "escaped"
      and any(s.startswith("战报：") for s in io_win.said)
      and any(s.startswith("战报：") for s in io_dead.said)
      and not any(s.startswith("战报：") for s in io_esc.said))

# ── 门禁2：真实 combat 三回合 fled + week3 引擎推进，无奖励/击杀/任务 ──
io_fled = Io()
p_fled = base_player(attack=0)
res_fled = combat.battle(CFG, SKILLS, rare_mon(), p_fled, io_fled, {})
direct_ok = (res_fled == "fled"
             and any("看起来要溜走了" in s for s in io_fled.said)
             and any("金色·火妖溜走了！紫装机会没了。" in s for s in io_fled.said)
             and not any("倒下了" in s for s in io_fled.said))


class StopAfterMap7(Exception):
    pass


class FledGameIo(Io):
    def __init__(self):
        super().__init__()
        self.fled_seen = False
        self.after_fled = None

    def say(self, m=""):
        super().say(m)
        if "金色·火妖溜走了！紫装机会没了。" in m:
            self.fled_seen = True
            combat.random.randint = ORIGINAL_RANDINT   # 后续怪恢复正常随机，避免全 MISS 无限战斗
        if self.fled_seen and self.after_fled is None and "出现！" in m:
            self.after_fled = json.load(open("save.json", encoding="utf-8"))
        if self.fled_seen and "第 8 图" in m:
            raise StopAfterMap7


save.set_path(os.path.join(HERE, "save.json"))
save.write_raw(week3_save())
ORIGINAL_RANDINT = combat.random.randint
combat.random.randint = lambda a, b: 100   # 必 MISS：确定性让 fi5 稀有拖满三回合
io_game = FledGameIo()
try:
    try:
        engine.run_game(io_game)
    except StopAfterMap7:
        pass
finally:
    combat.random.randint = ORIGINAL_RANDINT
after_map7 = json.load(open("save.json", encoding="utf-8"))
af = io_game.after_fled or {}
engine_src = open("engine.py", encoding="utf-8").read()
fled_branch = engine_src.split('if result == "fled":', 1)[1].split('if result == "win":', 1)[0]
engine_ok = (af.get("next") == 6 and af.get("maps_cleared") == 6 and af.get("gold") == 123
             and af.get("kills") == {}
             and af.get("quest_flags") == {"m1": "active", "h1": "active", "h2": "active"}  # 仅初始化/对话，无 win 完成
             and af.get("inventory") == [] and af.get("storage") == []
             and after_map7.get("next") == 7 and after_map7.get("maps_cleared") == 7
             and not any(k.startswith("lose:") for k in after_map7.get("kills", {}))
             and all(x not in fled_branch for x in ("grant_win", "on_event", "print_report")))
check("2 fled：week3 fi5 三回合逃跑；fi→6、图7通关；无奖励/击杀/任务/win/lose", direct_ok and engine_ok)
if not (direct_ok and engine_ok):
    print("  诊断:", {"direct": direct_ok, "engine": engine_ok, "after_fled": af,
                       "after_map7": {k: after_map7.get(k) for k in ("next", "maps_cleared", "gold", "kills")},
                       "fled_seen": io_game.fled_seen, "branch": fled_branch.strip()})
os.remove("save.json")

# ── 门禁3：普通/精英/boss 在三回合末均不 fled ──
non_rare = [rare_mon(rare=False, name="小妖甲"), rare_mon(rare=False, name="精英·小妖甲"),
            rare_mon(rare=False, key="boss", name="白骨夫人")]
ios = [Io() for _ in non_rare]
results = [encounter.fled_check(mon, {"rounds": 3}, base_player(), io, 3)
           for mon, io in zip(non_rare, ios)]
check("3 fled 不误伤：普通、精英、boss 均继续战斗", results == [None, None, None]
      and all(not io.said for io in ios))

# ── 门禁4：第三回合玩家同时死亡 → dead 优先，不出现逃跑事件 ──
taken = combat.lua("incoming", 10, "0.00", "1.00")["dmg"]
io_dead_first = Io()
res_dead_first = combat.battle(CFG, SKILLS, rare_mon(), base_player(attack=0, hp=taken * 2 + 1),
                               io_dead_first, {})
check("4 dead 优先：fled 回合 hp 归零返回 dead，且无稀有逃跑事件",
      res_dead_first == "dead" and not any("溜走了！紫装机会没了" in s for s in io_dead_first.said))

# ── 门禁5：玩家主动 escaped 不推进，重打仍是同一只稀有 ──
class AlwaysEscapeIo(Io):
    def ask(self, p=""):
        return "3"   # 战前对话也固定 3，避免唯一的逃跑输入被对话先消费


escape_logs = []
escape_states = []
for _ in range(2):
    if not os.path.exists("save.json"):
        save.write_raw(week3_save())
    io_escape = AlwaysEscapeIo()
    engine.run_game(io_escape)
    escape_logs.append("\n".join(io_escape.said))
    escape_states.append(json.load(open("save.json", encoding="utf-8")))
check("5 escaped：fi 不变、可重打、week3 fi5 同一只金色火妖",
      all(s["next"] == 5 and s["maps_cleared"] == 6 and s["kills"] == {} for s in escape_states)
      and all("金色·火妖 出现！" in text for text in escape_logs))
os.remove("save.json")

# ── 门禁6：week0 基线 + tower 无稀有与 fled fail-closed ──
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 500) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
baseline = json.load(open("save.json", encoding="utf-8"))
os.remove("save.json")
original_battle = tower.combat.battle
tower.combat.battle = lambda *args, **kwargs: "fled"
io_warn = Io()
p_warn = base_player()
try:
    tower_result = tower.run_one(CFG, SKILLS, p_warn, [], io_warn)
finally:
    tower.combat.battle = original_battle
tower_ok = (not encounter.is_rare(tower.layer_mon(CFG, 1)) and not encounter.is_rare(tower.layer_mon(CFG, 10))
            and tower_result == "escaped" and p_warn["tower_layer"] == 0
            and any("WARN" in s for s in io_warn.said)
            and not any(s.startswith("战报：") for s in io_warn.said))
check("6 回归：week0 Lv25/金币798/maps10；tower 无稀有且 fled→escaped+WARN",
      baseline["maps_cleared"] == 10 and baseline["level"] == 25 and baseline["gold"] == 798
      and "战报：" in r.stdout and tower_ok)

# ── 门禁7：行数 + validate 十九项 + smoke_v29a 全链 ──
limits = {"engine.py": 225, "combat.py": 130, "encounter.py": 170,
          "tower.py": 100, "loot.py": 100, "validate.py": 215}
bad_lines = [f"{f}={sum(1 for _ in open(f, encoding='utf-8'))}"
             for f, lim in limits.items() if sum(1 for _ in open(f, encoding="utf-8")) > lim]
rv = subprocess.run([WB, "validate.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
rr = subprocess.run([WB, "tests/smoke_v29a.py"], capture_output=True, text=True, encoding="utf-8", env=ENV)
check("7 行数纪律 + validate 十九项 + smoke_v29a 19/19 全链回归",
      not bad_lines and rv.returncode == 0 and rv.stdout.count("✓") == 19
      and rr.returncode == 0 and "全部通过" in rr.stdout and rr.stdout.count("✗") == 0)
if bad_lines:
    print("  超标:", bad_lines)
if rr.returncode or "失败" in rr.stdout:
    print(rr.stdout[-1200:])

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
for _f in ("accounts.json", "session.json", "save.json"):
    if os.path.exists(_f):
        os.remove(_f)
_sh0.rmtree("saves", ignore_errors=True)
print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
