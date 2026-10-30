# V2.9-D2 日常/周常/签到 —— 快照差值口径（Q1），日期源单点可替换（Q5）。
# 只依赖传入的 state 字典：不 import save / configparser，滚动不读配置（§6）。
import datetime

TASKS = ("kills", "damage", "tower")


def today():
    return datetime.date.today().isoformat()


def this_week():
    y, w, _ = datetime.date.today().isocalendar()
    return "%04d-W%02d" % (y, w)


def _yesterday():
    return (datetime.date.fromisoformat(today()) - datetime.timedelta(days=1)).isoformat()


def snapshot(state):
    """当前累计量：总击杀（lose: 前缀不算）/ 总伤害 / 爬塔最高层。"""
    kills = sum(v for k, v in (state.get("kills") or {}).items() if not k.startswith("lose:"))
    return {"kills": kills, "damage": int(state.get("total_damage", 0) or 0),
            "tower": int(state.get("tower_best", 0) or 0)}


def _blank(scope, stamp, state):
    return {("date" if scope == "daily" else "week"): stamp, "base": snapshot(state), "claimed": []}


def touch(state):
    """写档前滚动：跨日/跨周只重置日期、base、claimed；不发奖励、不动其它字段（Q2/§6）。"""
    if (state.get("daily") or {}).get("date") != today():
        state["daily"] = _blank("daily", today(), state)
    if (state.get("weekly") or {}).get("week") != this_week():
        state["weekly"] = _blank("weekly", this_week(), state)
    state.setdefault("checkin", {"last": "", "streak": 0, "total": 0})
    return state


def view(state):
    """读态：日期对不上就按"今天刚开始"算，**不写档**（未写档也能正确显示 0 进度）。"""
    d, w = state.get("daily") or {}, state.get("weekly") or {}
    if d.get("date") != today():
        d = _blank("daily", today(), state)
    if w.get("week") != this_week():
        w = _blank("weekly", this_week(), state)
    return {"daily": d, "weekly": w,
            "checkin": state.get("checkin") or {"last": "", "streak": 0, "total": 0}}


def status(state, cfg):
    """三块进度行（界面唯一数据源）：daily/weekly 各三项 + checkin 摘要。"""
    v, snap, rows = view(state), snapshot(state), {}
    for scope in ("daily", "weekly"):
        rows[scope] = []
        for key in TASKS:
            need = cfg.getint(scope, key + "_need")
            cur = min(max(0, snap[key] - v[scope]["base"].get(key, 0)), need)   # 差值负数截断，上限截到 need
            rows[scope].append({"key": key, "cur": cur, "need": need,
                                "claimed": key in v[scope]["claimed"]})
    ck = v["checkin"]
    n = ck.get("streak", 0) % 7 + 1 if ck.get("last") == _yesterday() else 1
    rows["checkin"] = {"total": ck.get("total", 0), "streak": ck.get("streak", 0), "next_day": n,
                       "claimed_today": ck.get("last") == today(),
                       "gold": cfg.getint("checkin", "gold_base") + (n - 1) * cfg.getint("checkin", "gold_step"),
                       "staff": 1 if n == cfg.getint("checkin", "staff_day") else 0}
    return rows


def claim(state, cfg, scope, key):
    """领取：返回 (ok, 文案)；只改 claimed / gold / protect，其余字段原样（Q8）。"""
    v = view(state)
    if scope == "checkin":
        ck = v["checkin"]
        if ck.get("last") == today():
            return False, "今天已经签过了"
        n = ck.get("streak", 0) % 7 + 1 if ck.get("last") == _yesterday() else 1
        gold = cfg.getint("checkin", "gold_base") + (n - 1) * cfg.getint("checkin", "gold_step")
        staff = 1 if n == cfg.getint("checkin", "staff_day") else 0
        state["checkin"] = {"last": today(), "streak": n, "total": ck.get("total", 0) + 1}
        state["gold"] = state.get("gold", 0) + gold
        if staff:
            state["protect"] = state.get("protect", 0) + staff
        return True, "签到第 %d 天：金币 +%d%s" % (n, gold, "，保底符 +1" if staff else "")
    if scope not in ("daily", "weekly") or key not in TASKS:
        return False, "未知任务"
    if key in v[scope]["claimed"]:
        return False, "今天已经领过了"
    need, cur = cfg.getint(scope, key + "_need"), max(0, snapshot(state)[key] - v[scope]["base"].get(key, 0))
    if cur < need:
        return False, "还没完成（%d/%d）" % (cur, need)
    gold = cfg.getint(scope, "gold")
    state[scope] = {**v[scope], "claimed": v[scope]["claimed"] + [key]}
    state["gold"] = state.get("gold", 0) + gold
    return True, "领取成功：金币 +%d" % gold
