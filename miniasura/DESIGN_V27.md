# MiniAsura V2.7 设计冻结（战斗补齐：十技能 + CD + 命中闪避 + 武器谱特效）

> 由 PATCH-V27-设计补丁-DRAFT 转正冻结（2026-10-29，业主指示"按补丁设计稿继续做"，
> §1 默认值 D1–D5 全部采纳，未逐项修改）。依据：DESIGN_V2.md §5/§2.5/§1.3。
> 范围：只做 V2.7；V2.8（图鉴/成就/统计）不在本期。schema 不动（仍 7）。

## 1. 业主决议（补丁默认值全部采纳）

| 决议 | 结论 |
|---|---|
| **D1** 如意神通解锁 | 满 30 级自动解锁（h2 已绑定无级武器不复用；满级任务留 V2.8） |
| **D2** 怪物 tribe 映射 | 按蓝图 §3 怪物主题：虾兵蟹将=水族 / 猪妖佃户、沙妖水鬼=妖 / 火妖=火抗 / 其余=无 |
| **D3** 吸血叠加上限 | 上限 10%（紫词条 2–5% + 缠丝爪 3% 最高 8%，10% 宽松防失控） |
| **D4** 期切分 | V2.7 战斗、V2.8 图鉴/成就/统计；本期不动 schema |
| **D5** 筋斗云闪避 | 叠加（buff 加法；取高值会让靴子闪避在 buff 回合失效，不直观） |

## 2. P0 技能数据外置

- `assets/skills.txt` 加 7 行（huoyan/canshen/jinshen/bangsao/douxin/ruyi + jindou 描述补"下回合闪避 +30%"），
  现有 3 行不动；`game.ini` 加 7 段 `[skill.*]`（power/mp_cost/cd/kind/unlock_lv/特效字段），
  两处同 id；现有 3 段补 kind/unlock_lv（dinghai 3 / qishi 10）与 jindou 的 `dodge_buff = 0.30`。
- 落棒 = 普攻不进技能表（蓝图 §5 第 1 行即普攻，现有行为保留）。

## 3. P1 skills.py（≤150 行）——技能逻辑唯一住所

`load_skills()`（合并 skills.txt + game.ini）/ `unlocked_skills(level)` / `passive_totals(level, totals)`
（crit_bonus / atk_mult / mitigate 三项，未解锁不计，汇总只此一处）/ `Cooldowns`
（usable/use/tick/reset）/ `choose()`（技能菜单+选择+MP/CD/解锁校验，combat 只调接口）/
`leech_heal()` / `weapon_effect()`（vs_tribe 倍率查询）。combat.py 已 130 行顶格不许再塞。

## 4. P2 战斗状态化

- **命中/闪避**（蓝图 §1.3 原样）：命中率 = 95% + 命中 − 闪避，下限 60%；概率掷骰归引擎。
  玩家命中 = 词条 + 弥陀弓 +10%；玩家闪避 = 靴子 + 词条 + 筋斗云 buff（仅下回合，回合结束清除）。
  MISS → 伤害 0，不触发暴击/吸血/连击后续段。逃跑 50%−boss 0% 不动。
- **battle.lua**：`damage` 加第 7 参 effect_mult（缺省 1.0）、`incoming` 加第 3 参 mitigate（缺省 1.0），
  缺省 = 现有行为；白骨剑暴伤 +0.15 走现有第 5 参。
- **战斗内 state**：`{"cd": Cooldowns(), "dodge_buff": 0}`，combat.battle 局部变量不进存档；
  回合结束 cd.tick() + buff 清除；战斗结束 cd.reset()。

## 5. P3 武器谱特效（只紫档生效）

- 新增 `assets/weapon_effects.txt`（武器|effect|参数，9 行；桃木棍无特效不进表）。
- gear.py：构造紫档武器时填 `effect` 字段；汇总接入 totals 同一处——齐眉棍 HP×1.05、
  乾坤圈防御×1.08、混妖斧攻击×1.06、弥陀弓命中 +10%；吸血 = 词条 + 缠丝爪 3%，**上限 10%**（D3）。
- loot.py 掉落路径不变，仅构造紫装多一步查表；无级武器不走本表（V2.5 专属逻辑不动）。

## 6. P4 怪物 tribe（monsters.txt 加第 4 列）

`xiaoyao1/2/3 = 无`，`boss = 妖`（D2）；tribe 随怪物数据表走，不另开第二份表。

## 7. P5 GUI 战斗窗

技能菜单列全部主动技能：未解锁灰字"Lv.X 解锁"、CD 中灰字"冷却中（剩 X 回合）"、MP 不足灰字，
均不可选；被动不进菜单；MISS 文案"MISS！"与暴击同一行；大厅不新增按钮。

## 8. P6 validate.py 加两项（≤150 行顶格）

- **V27-01** skills.txt 每行 id 在 game.ini 必有 `[skill.*]` 且含 unlock_lv；主动必有 power，被动不得有 power。
- **V27-02** weapon_effects.txt 的 `vs_tribe:X` 之 X 必在 monsters.txt tribe 列出现过。
- 既有七项全保留；validate 全绿仍是门禁硬条件。

## 9. P7 smoke_v27 门禁

1. 技能解锁：Lv.3/6/10/14/18/22/26/29/30 档菜单与蓝图表一致，未解锁不可选
2. CD：棒扫六合 3 回合、如意神通 5 回合，回合结束递减，出战斗清零
3. 被动：Lv.14 暴击 +8% / Lv.22 受伤 ×0.85 / Lv.29 攻击 ×1.10 各有断言
4. 命中/闪避：下限 60%；MISS 不触发暴击/吸血/连击第二段；筋斗云 buff 仅下回合
5. 特效：定水枪 ×1.15 打水族 / 降魔杖 ×1.12 打妖 / 白骨剑暴伤 +0.15 / 蓝档无特效 / 吸血上限 10%
6. 回归：smoke_v21→v26 全绿；validate 全绿（含新增两项）；行数纪律 engine≤220、combat≤130、skills≤150、validate≤150

## 10. P8 README + 不动清单

- README 加 V2.7 行与 smoke_v27 启动命令。
- **不动**：schema 仍 7；怪物数值/经验曲线/爬塔/无级武器/逃跑/死亡惩罚/强化/掉落概率/商店价格全部不动。

## 11. HARD STOP

本细案已冻结（D1–D5 = 补丁默认值），业主已授权开工。实现按 IMPLEMENTATION →
COMMIT_READINESS_AUDIT → COMMIT_EXECUTION 三段隔离。
