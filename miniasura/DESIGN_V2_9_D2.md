# MiniAsura V2.9-D2 设计冻结草案（日常 / 周常 / 签到）

## 基线
`f2ba091`（V2.9-D1 毕业）。**schema 10 → 11**。
范围取自路线稿 §1 D2：本地日期驱动的每日任务、周常、签到、睡前结算。**不做**服务器时间、不做断签惩罚、不做联网。

## §0 现状审计（2026-10-30 实测）

| 项 | 现状 | 缺口 |
|---|---|---|
| 日常/签到 | 全仓 `grep daily|checkin|签到|日常` = **0 命中** | 从零开始 |
| 写档入口 | `write_raw` 共 **12 处调用**：engine `save.write`、tower.persist、9 个 GUI 窗 | 天然唯一收口，适合挂"跨日滚动" |
| 可复用的累计量 | `kills{}`（分怪键）、`total_damage`、`tower_best`、`gold`、`playtime` | 没有"今日击杀/今日伤害"这类日粒度计数 |
| 存档 | schema 10，`_migrate` 全是 setdefault | 无 daily/weekly/checkin |
| 校验器 | 17 项，V31-01 管称号表 | 无日常配置校验 |
| 大厅 | 8 个按钮 + 称号标签 | 无日常入口 |
| 路由 | `app.py` 131 行，QStackedWidget 十个窗口 | 需加一个窗口 + 一条路由 |

关键判断：**不新增逐事件计数器**。所有任务进度用「当日/当周快照差值」算：写入时若日期变了就把当前累计量记成 base，进度 = 当前 − base。好处是零引擎钩子（engine/tower 一行不改），坏处是"跨日不写档"时进度会从当天第一次写档算起——单机游戏可接受，冻结稿写明。

## §1 裁决（建议冻结值，待业主确认）

| 编号 | 裁决 | 理由 |
|---|---|---|
| Q1 | 进度口径 = **快照差值**（`base` + 当前累计），不逐事件加计数 | 零引擎钩子；不需要给每次击杀/伤害插入计数代码；图鉴与统计口径完全不受影响 |
| Q2 | 跨日/跨周滚动**统一挂在 `save.write_raw`**，engine / tower / 各 GUI 窗一行不改 | 12 处写档天然收口；挂 `save.write` 会漏掉 tower.persist 与 GUI 直写 |
| Q3 | 日常 3 项：击杀 8 / 造成 8000 伤害 / 爬塔 1 层，各 **40 金币**；周常 3 项：击杀 40 / 造成 30000 伤害 / 爬塔 3 层，各 **150 金币** | 全部可用现有累计量算；不发装备/经验，避免冲击战力与全通基线 |
| Q4 | 签到 7 天循环：第 N 天 `30+(N-1)×20` 金币（30→150），**第 7 天额外 1 张保底符**；漏签只把连签重置为 1，**不清总次数** | 路线稿明确不做断签惩罚；保底符是稀缺资源，7 天一张不破坏强化经济 |
| Q5 | 日期源**单点**：`daily.today()` / `daily.this_week()`（本地时区，`date.today()` / ISO 周）；测试可替换这两个函数 | 单机本地时间，不做服务器校时；可确定性测试跨日/跨周 |
| Q6 | **schema 10→11**：新增 `daily` / `weekly` / `checkin` 三字段，`_migrate` 只补默认值 | 与 v9→v10 同纪律；旧档数值一字不动 |
| Q7 | 新窗 `gui_daily.py`：三页（日常 / 周常 / 签到），每项一行「进度 + 领取按钮」；大厅新增 **「日常 / 签到」** 按钮 | 与图鉴窗同构（QTabWidget），玩家不用记命令 |
| Q8 | 领取只改 `claimed` / `gold` / `protect`（签到第 7 天），其余字段原样 | 与称号佩戴同纪律：写档范围最小 |
| Q9 | 行数：`daily.py` 新建 ≤110、`gui_daily.py` 新建 ≤120、save 128→**140**、gui_hub 59→**65**、app 131→**140**、validate 170→**180**；engine/tower/combat/encounter 不动 | 新增两个模块，其余只加薄薄一层 |
| Q10 | 门禁 `smoke_v29d2` 八项（见 §5）；旧门禁同步 validate 十七→十八项、`validate≤170→180` | 机械重定基线，先例同 D1 |

## §2 数据落点

### 2.1 `game.ini` 新增三段（扁平参数，符合既有约束）
```ini
[daily]
kills_need = 8
damage_need = 8000
tower_need = 1
gold = 40

[weekly]
kills_need = 40
damage_need = 30000
tower_need = 3
gold = 150

[checkin]
gold_base = 30
gold_step = 20
staff_day = 7
```

### 2.2 存档新字段（schema 11）
```json
"daily":   {"date": "2026-10-30", "base": {"kills": 12, "damage": 3400, "tower": 3}, "claimed": []},
"weekly":  {"week": "2026-W44",  "base": {...}, "claimed": []},
"checkin": {"last": "2026-10-29", "streak": 2, "total": 5}
```
- 跨日/跨周只重置 `date/week` + `base` + `claimed`，**不动**金币/等级/成就等任何字段。
- `base` 三项固定：`kills`=总击杀（不含 `lose:`）、`damage`=total_damage、`tower`=tower_best。

## §3 代码落点与行数
| 模块 | 现行 | 改动 | 上限 |
|---|---|---|---|
| daily.py | 新建 | `today/this_week/snapshot/view/touch/status/claim` 七个纯函数（claim 改传入的 state） | **110** |
| save.py | 128 | `_migrate` +3 setdefault；`write_raw` 首行 `daily.touch(data)` | **140** |
| gui_daily.py | 新建 | 三页 + 7 个领取按钮 + 进度刷新 | **120** |
| gui_hub.py | 59 | 加「日常 / 签到」按钮与回调参数 | **65** |
| app.py | 131 | import + 建窗 + `to_daily` 路由 + 装配 | **140** |
| validate.py | 170 | `check_v32`（三段配置合法）→ 十八项 | **180** |
| engine/tower/combat/encounter/gui* | 225/100/130/170/… | **不动** | 不变 |

## §4 schema 与迁移
- `SCHEMA = 11`，迁移链注释补 `→ v11（日常/周常/签到）`。
- `_migrate` 三个 setdefault 用**字面量**（不用可变默认共享）。
- 实测：v10 档（含 title/records/elite_kills 非默认值）→ `save.load()` → 三字段就位、旧值逐个不变。

## §5 出口验收（smoke_v29d2，八门禁）
1. **跨日滚动**：把 `daily.today` 打到 D1 写档 → 进度按 base 算；改到 D2 再写 → `date` 变、`base` 取当前累计、`claimed` 清空。
2. **跨周滚动**：`this_week` 从 W44 → W45 同理；日界与周界互不干扰（同日跨周只滚周）。
3. **进度口径**：`kills/total_damage/tower_best` 增量正确；跨周目 `maps` 归零不影响；差值负数截断为 0。
4. **领取规则**：达阈值可领 → 金币精确 +N、`claimed` +1；未达拒绝、重复领取拒绝、未知任务拒绝；**除 gold/claimed 外其它字段零变化**。
5. **签到**：同日二次拒绝；连签 +1；隔天断签重置为 1（总次数仍 +1）；第 7 天额外 +1 保底符、金币按公式。
6. **UI**：offscreen 打开 `DailyWindow`，三页按钮文案含进度、未达阈值禁用；点领取后 `save.json` 的 gold 增加且按钮变"已领取"。
7. **迁移 + 校验**：v10→v11 三字段就位、旧值不动；`validate` 十八项全绿。
8. **行数 + 全链**：daily≤110 / gui_daily≤120 / save≤140 / gui_hub≤65 / app≤140 / validate≤180；`v20→…→v29d1` 全链回归绿。

## §6 风险与硬禁区
- **滚动只改日期与快照**：`touch` 绝不发奖励、不动金币；发奖励只能在 `claim`。
- **跨日不写档的边界**：进度从当天第一次写档起算（如 23:59 打完、00:01 存档，该场算次日）。这是快照口径的固有语义，写进文档不装作没有。
- **系统时间可篡改**：单机游戏不做校时，改本地时间可刷日常；明确接受，不做防作弊。
- **签到第 7 天保底符**：只加 `protect`，不直接强化、不动装备。
- **领取必须精确校验**：`need` 从 ini 读、`claimed` 去重、未知 scope/key 一律拒绝（fail-closed）。
- **不许在 `write_raw` 里读配置**：`touch` 只依赖 state 自身，避免 save ↔ configparser 耦合。

## §7 明确延期
- 睡前结算动画/弹窗。
- 连续签到 30 天里程碑、补签卡。
- 日常任务随机池 / 每日轮换（本期固定 3 项）。
- 服务器时间与跨设备同步（红线：不做联网）。

## §8 施工（单批，风险中等偏低）
1. `daily.py`（纯函数 + 可替换时钟）。
2. `save.py` schema 11 + write_raw 挂钩。
3. `game.ini` 三段 + `validate.check_v32`（十八项）。
4. `gui_daily.py` + `gui_hub` 按钮 + `app.py` 路由。
5. `tests/smoke_v29d2.py` 八门禁 + 旧门禁 baseline 重定 + README 同步。

> 本文件为冻结稿草案，**未提交、未施工**。业主确认 Q1–Q10 后入仓，再一句话开工。
