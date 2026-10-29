# V2.1 出口验收 · 自动化冒烟（DESIGN_V2_1.md §4 六门禁）
# 门禁1-5 直测；门禁6 回归以子进程跑 V2.0 冒烟 + CLI 通关
import json
import os
import random
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # miniasura/
sys.path.insert(0, HERE)
os.chdir(HERE)
WB = sys.executable
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

ok = []


def check(name, cond):
    ok.append((name, bool(cond)))
    print(("✓" if cond else "✗"), name)


def lua(*args):
    exe = os.path.join(HERE, "..", "tools", "lua-5.1.5", "lua.exe")
    r = subprocess.run([exe] + [str(a) for a in args], capture_output=True,
                       text=True, encoding="utf-8", env=ENV)
    return next(l for l in r.stdout.splitlines() if "{" in l).strip()


# ── 门禁1 公式抽查（蓝本 §2.2 原式）──
check("白武器 lv10 ATK=35", json.loads(lua("scripts/equip.lua", "main", 0, 10, 0))["atk"] == 35)
check("紫武器 lv10 ATK=66（35×1.9 取整）",
      json.loads(lua("scripts/equip.lua", "main", 0, 10, 2))["atk"] == 66)
check("词条区间下端", json.loads(lua("scripts/equip.lua", "affix", 0, 10, 0, 1.2, 1.8, 0))["val"] == 12.0)
check("词条区间上端", json.loads(lua("scripts/equip.lua", "affix", 0, 10, 10000, 1.2, 1.8, 0))["val"] == 18.0)
check("紫第2条保底≥中位", json.loads(lua("scripts/equip.lua", "affix", 0, 10, 0, 1.2, 1.8, 1))["val"] == 15.0)
check("防御减伤 max(1,怪攻-防×0.6)",
      json.loads(lua("scripts/battle.lua", "incoming", 20, 10))["dmg"] == 14)

# ── 门禁2 词条规则（30 种子批跑）──
import gear
rows = gear.load_affixes()
props = True
for seed in range(30):
    for slot in gear.SLOTS:
        it = gear.generate(slot, 10 + seed % 10, 2, rows, random.Random(seed))
        keys = [a["key"] for a in it["affixes"]]
        props &= len(keys) == 2 and len(set(keys)) == 2
        # 第 2 条 ≥ 中位：用蓝本区间反查
        for a in it["affixes"][1:]:
            row = next(r for r in rows if r["key"] == a["key"])
            mid = (row["lo"] + row["hi"]) / 2
            if row["kind"] == "flat":
                mid *= it["lv"]
            props &= a["val"] >= mid - 1e-6
        if "leech" in keys:
            props &= slot == "weapon"
for seed in range(10):
    it = gear.generate("weapon", 12, 0, rows, random.Random(seed))     # 白装
    props &= len(it["affixes"]) == 0
check("紫装恒2条/不重复/第2条≥中位/吸血仅紫武器/白装0条", props)

# ── 门禁3 GM 发紫装 + 容量（真会话 + 真 CLI 子进程）──
import login
import save
import slots
login.register("audit2", "pw")
login.start_session("audit2", "huaguoshan", 1)
path = slots.slot_path("huaguoshan", "audit2", 1)
base = {"schema": save.SCHEMA, "user": "audit2", "level": 14, "exp": 0, "hp": 150,
        "mp": 100, "attack": 57, "next": 0, "week": 0, "playtime": 0}
save.set_path(path, "audit2")
save.write_raw(dict(base))

r = subprocess.run([WB, "gm.py", "give", "weapon", "15"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
d = json.load(open(path, encoding="utf-8"))
check("gm give 入包", r.returncode == 0 and len(d["inventory"]) == 1
      and d["inventory"][0]["quality"] == 2 and d["inventory"][0]["lv"] == 15)

for i in range(gear.capacity() - 1):
    d["inventory"].append({"slot": 0, "lv": 1, "quality": 0, "main": {}, "affixes": []})
save.write_raw(d)
r = subprocess.run([WB, "gm.py", "give", "helm", "5"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("容量20满拒绝第21件", r.returncode == 1 and "背包已满" in r.stdout)
d = json.load(open(path, encoding="utf-8"))
d["inventory"] = d["inventory"][:1]
save.write_raw(d)

# ── 门禁4 穿戴实时生效（engine 消费端 + 战斗内吸血实拍）──
import configparser
cfg = configparser.ConfigParser()
cfg.read("game.ini", encoding="utf-8")
import engine
eq = gear.empty_equipment()
eq["weapon"] = gear.generate("weapon", 15, 2, rows, random.Random(7))
p = {"level": 14, "equipment": eq}
engine.apply_gear(cfg, p)
p0 = {"level": 14, "equipment": gear.empty_equipment()}
engine.apply_gear(cfg, p0)
check("穿紫武器攻击力=基础+装备",
      p["attack"] == p0["attack"] + eq["weapon"]["main"]["atk"])

# 找一个带吸血词条的种子，实拍战斗内"吸血回复"
seed = next(s for s in range(50)
            if "leech" in [a["key"] for a in gear.generate("weapon", 15, 2, rows, random.Random(s))["affixes"]])
leech_item = gear.generate("weapon", 15, 2, rows, random.Random(seed))
d = json.load(open(path, encoding="utf-8"))
d.update({"next": 3, "equipment": {**gear.empty_equipment(), "weapon": leech_item}})
save.write_raw(d)
shutil.copy(path, "save.json")   # engine 子进程走 CLI 默认路径，档要放到它读的位置
r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 120) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
check("战斗内出现吸血回复", "吸血回复" in r.stdout)
check("战斗状态行显示防御", "防御" in r.stdout)
check("攻击力含装备加成进战斗",
      str(p0["attack"] + leech_item["main"]["atk"]) in r.stdout)
after = json.load(open("save.json", encoding="utf-8"))
check("通关写回背包与装备", after.get("equipment", {}).get("weapon") is not None
      and after.get("week") == 1)
os.remove("save.json")

# ── 门禁4B 终审并入：主门禁 + F1 回归 + fail-closed ──
crit_item = {"slot": 0, "lv": 14, "quality": 1,             # 蓝装武器
             "main": {"atk": 30, "hp": 0, "def": 0, "dodge": 0},
             "affixes": [{"key": "crit", "name": "暴击率%", "val": 5.0}]}
p = {"level": 14, "exp": 0, "hp": 150, "mp": 100,
     "inventory": [], "equipment": dict(gear.empty_equipment(), weapon=crit_item)}
engine.apply_gear(cfg, p)
check("★主门禁：穿暴击+5%蓝装 → 面板 20%→25% 零代码生效",
      p["crit_rate"] == 25 and p["attack"] == 57 + 30)

io_stub = type("S", (), {"say": lambda self, *a: None})()
# V2.6 曲线（60×lv^1.65）下 Lv.14→15 需 4668 经验，给 5000 保证升级——判据语义不变：升级后装备加成不丢
engine.grant_exp(cfg, p, io_stub, 5000)                     # 升到 15
check("★F1 回归：升级重算 apply_gear，装备攻击不丢",
      p["level"] == 15 and p["attack"] == 60 + 30 and p["crit_rate"] == 25)

for bad_args, name in ((("weapon", 10, 3), "品质越界"), (("ring", 10, 1), "未知部位")):
    try:
        gear.generate(*bad_args)
        check(f"{name} fail-closed", False)
    except ValueError:
        check(f"{name} fail-closed", True)
try:
    gear.totals({"weapon": dict(crit_item,
                                affixes=[{"key": "haha", "name": "x", "val": 1}])})
    check("未知词条 key fail-closed（白名单对齐）", False)
except ValueError:
    check("未知词条 key fail-closed（白名单对齐）", True)

r = subprocess.run([WB, "gm.py", "give", "weapon", "10", "9"], capture_output=True,
                   text=True, encoding="utf-8", env=ENV)
check("gm give 品质越界被拒", r.returncode == 1 and "发放失败" in r.stdout)

# ── 门禁5 迁移 v2→v3 ──
v2 = {"schema": 2, "user": "audit2", "level": 16, "exp": 45, "hp": 100, "mp": 70,
      "attack": 63, "next": 2, "week": 0, "playtime": 33}
save.write_raw(v2)
m = save.load()
check("v2→v4 补默认不丢值", m["schema"] == save.SCHEMA and m["level"] == 16
      and m["next"] == 2 and m["playtime"] == 33 and m["inventory"] == []
      and m["equipment"]["weapon"] is None)
m["inventory"] = [leech_item]
save.write_raw(m)
m2 = save.load()
check("schema 档幂等", m2["schema"] == save.SCHEMA
      and m2["inventory"][0] == leech_item)

# ── 门禁6 回归（清现场后子进程跑 V2.0 冒烟 + CLI 通关）──
save.set_path(os.path.join(HERE, "save.json"))
for pth in (path, os.path.join(HERE, "save.json")):
    if os.path.exists(pth):
        os.remove(pth)
login.logout()
for f in ("accounts.json", "session.json"):
    if os.path.exists(f):
        os.remove(f)
shutil.rmtree("saves", ignore_errors=True)
shutil.rmtree(os.path.join(HERE, "__pycache__"), ignore_errors=True)

r = subprocess.run([WB, "tests/smoke_v20.py"], capture_output=True, text=True,
                   encoding="utf-8", env=ENV)
check("V2.0 冒烟回归 18/18", "全部通过" in r.stdout)

r = subprocess.run([WB, "engine.py"], input="\n".join(["1"] * 400) + "\n",
                   capture_output=True, text=True, encoding="utf-8", env=ENV)
check("CLI 管道完整通关", "通关结算" in r.stdout)
if os.path.exists("save.json"):
    os.remove("save.json")

print("\n=== 汇总 ===")
bad = [n for n, c in ok if not c]
print("全部通过 ✅" if not bad else "失败: %s" % bad)
sys.exit(1 if bad else 0)
