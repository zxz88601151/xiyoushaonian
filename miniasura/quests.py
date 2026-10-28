# V2.2 任务系统 —— 状态机单向推进：前置 done → 后继 active → done；hidden 由事件触发。
# 本模块只做状态机与计数，奖励发放归引擎（要动 gear/exp/potions）。
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

# 类型: clear(通关第N张图) / talk(看完对话id) / kill(击杀怪物:N) / hidden(lose:怪物:N)
# 行格式: key|名称|类型|目标|奖励|前置任务(-=无)|对话id(-=无)


def load_pack_text():
    return mypack.read(os.path.join(HERE, "assets.mpak"), "quests.txt").decode("utf-8")


def load(text):
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, name, qtype, target, reward, prev, did = line.split("|")
        rows.append({"key": key, "name": name, "type": qtype, "target": target,
                     "reward": reward, "prev": prev, "dialogue": did})
    return rows


def parse_rewards(text):
    """'exp:50,potion_hp:2,gear:weapon:15:1' → [(kind, args...)]"""
    out = []
    for part in filter(None, text.split(",")):
        bits = part.split(":")
        out.append((bits[0], bits[1:]))
    return out


class Tracker:
    def __init__(self, all_quests, flags=None, kills=None):
        self.qs = {q["key"]: q for q in all_quests}
        self.flags = dict(flags or {})       # key → active/done
        self.kills = dict(kills or {})       # 怪 → 数；"lose:怪" → 败北数
        for q in self.qs.values():
            if q["key"] in self.flags:
                continue
            if q["type"] == "hidden":
                self.flags[q["key"]] = "active"   # hidden 开局即挂监听（门禁 Bug A）
            elif q["prev"] == "-":
                self.flags[q["key"]] = "active"

    def state(self, key):
        return self.flags.get(key, "locked")

    def _activate_children(self, key):
        for q in self.qs.values():
            if q["prev"] == key and q["type"] != "hidden" \
                    and q["key"] not in self.flags:
                self.flags[q["key"]] = "active"

    def _finish(self, key, done):
        self.flags[key] = "done"
        done.append(self.qs[key])
        self._activate_children(key)

    def on_event(self, ev, arg):
        """ev ∈ win/lose/map/talk；返回本次新完成的任务列表。"""
        done = []
        if ev == "win":
            self.kills[arg] = self.kills.get(arg, 0) + 1
        elif ev == "lose":
            self.kills["lose:" + arg] = self.kills.get("lose:" + arg, 0) + 1
        for q in self.qs.values():
            if self.state(q["key"]) != "active":
                continue
            t = q["target"]
            if q["type"] == "clear" and ev == "map" and arg == int(t):
                self._finish(q["key"], done)
            elif q["type"] == "talk" and ev == "talk" and arg == t:
                self._finish(q["key"], done)
            elif q["type"] == "kill" and ev == "win":
                mon, need = t.split(":")
                if mon == arg and self.kills.get(mon, 0) >= int(need):
                    self._finish(q["key"], done)
            elif q["type"] == "hidden" and ev == "lose":
                _, mon, need = t.split(":")
                if mon == arg and self.kills.get("lose:" + mon, 0) >= int(need):
                    self._finish(q["key"], done)   # 触发即完成（彩蛋叙事）
        return done
