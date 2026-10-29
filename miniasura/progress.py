# V2.8 进度口径 —— 成就判定 + 武器图鉴合并 + 统计口径（唯一汇总处，DESIGN_V2_8 §2/§3）。
# 只读数据表与传入的存档字典，不 import save/engine/gear（避免耦合与循环）；判断是纯函数。
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

COND_KINDS = ("kills", "maps", "level", "arsenal", "tower", "enhance")


def load_achievements():
    """achievements.txt（id|名称|描述|条件类型|阈值）→ 列表；加成就 = 加数据行，不改代码。"""
    text = mypack.read(os.path.join(HERE, "assets.mpak"), "achievements.txt").decode("utf-8")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        aid, name, desc, kind, need = line.split("|")
        rows.append({"id": aid, "name": name, "desc": desc, "kind": kind, "need": int(need)})
    return rows


def weapon_names(obj):
    """从装备槽位字典 / 背包列表 / 单件装备里收集武器名（V2.7 起紫档武器才有 name 字段）。"""
    if isinstance(obj, dict):
        items = list(obj.values()) if any(isinstance(v, dict) for v in obj.values()) else [obj]
    elif isinstance(obj, list):
        items = obj
    else:
        items = []
    return [i["name"] for i in items if isinstance(i, dict) and i.get("name")]


def merge_codex(prev, player, storage):
    """图鉴并集：旧档 codex ∪ 当前穿戴/背包/仓库的武器名——卖出 / 回收不灭灯。"""
    names = set(prev or [])
    names |= set(weapon_names((player or {}).get("equipment") or {}))
    names |= set(weapon_names((player or {}).get("inventory") or []))
    names |= set(weapon_names(storage or []))
    return sorted(names)


def kills_total(kills):
    """总击杀：kills 里的 "lose:怪" 是败北计数，不计入击杀（与引擎结算口径一致）。"""
    return sum(v for k, v in (kills or {}).items() if not k.startswith("lose:"))


def max_enh(norm):
    """单件最高强化等级（含穿戴/背包/仓库）——+10 装备被回收后靠成就并集保留。"""
    items = [i for i in ((norm.get("equipment") or {}).values()) if isinstance(i, dict)]
    items += [i for i in (norm.get("inventory") or []) if isinstance(i, dict)]
    items += [i for i in (norm.get("storage") or []) if isinstance(i, dict)]
    return max([i.get("enh", 0) for i in items] or [0])


def evaluate(norm):
    """按数据表判定本次达成的成就 id 集合；历史成就由调用方并集保留（永不回归）。
    norm 需含：level/kills/maps_cleared/week/tower_best/codex_weapons/inventory/storage/equipment。"""
    # clear_all 兜底（DESIGN_V2_8 §2）：周目重开后 maps_cleared 归零，week≥1 视为已通关十图
    maps = norm.get("maps_cleared", 0)
    if norm.get("week", 0) >= 1:
        maps = max(maps, 10)
    stat = {"kills": kills_total(norm.get("kills")), "maps": maps,
            "level": norm.get("level", 1), "arsenal": len(norm.get("codex_weapons") or []),
            "tower": norm.get("tower_best", 0), "enhance": max_enh(norm)}
    return {a["id"] for a in load_achievements() if stat.get(a["kind"], 0) >= a["need"]}


def stats(state):
    """统计页口径（DESIGN_V2_8 §3）：总击杀 / 总伤害 / 时长（<1 小时显示 X分钟）/ 周目 / 爬塔 / 等级 / 金币。"""
    sec = int(state.get("playtime", 0) or 0)
    return {"kills": kills_total(state.get("kills")),
            "damage": int(state.get("total_damage", 0) or 0),
            "playtime": "%d小时%d分" % (sec // 3600, sec % 3600 // 60) if sec >= 3600
                        else "%d分钟" % (sec // 60),
            "week": state.get("week", 0), "tower_best": state.get("tower_best", 0),
            "level": state.get("level", 1), "gold": state.get("gold", 0)}


def monster_codex(state, monster_keys):
    """怪物图鉴行：[(key, 名, 击杀数, 是否遭遇)]；击杀数取 kills{}，lose: 前缀不算击杀。"""
    kills = state.get("kills") or {}
    return [(key, name, kills.get(key, 0), kills.get(key, 0) > 0)
            for key, name in monster_keys]
