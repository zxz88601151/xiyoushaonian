# MiniAsura V2.9-D1 设计冻结草案（称号 + 精英/稀有成就 + 幻影榜）

## 基线
`4ef8d2a`（V2.9-C 毕业）。**schema 9 → 10**（本期第一次真正加持久化字段，必须实测迁移）。
范围取自路线稿 §1：称号、精英/稀有相关成就、幻影榜本地最高纪录。**不做**属性称号、不做联网排行。

## §0 现状审计（2026-10-30 实测）

| 项 | 现状 | 缺口 |
|---|---|---|
| 成就表 | `assets/achievements.txt` 6 条，条件类型 6 种（kills/maps/level/arsenal/tower/enhance） | 无精英/稀有维度 |
| 击杀统计 | `tracker.kills` 只按怪物 key 计数（实测 `{'huoyao': 1}`） | 精英/稀有与普通共用同一 key，**无法区分** |
| 精英/稀有标记 | `apply_encounter` 把 `fight["elite"]=词缀`、`fight["rare"]=True` 挂在 **fight** 上；`mon["rare"]` 也设了 | 战斗结束就丢，从不落盘 |
| 存档 | schema 9，迁移链 v1→…→v9 全在 `save._migrate` 的 setdefault 里 | 无 title / records / 变体击杀计数 |
| 图鉴窗 | `gui_codex.py` 85 行，一窗四页（武器谱/怪物/成就/统计），**全程只读不写盘** | 无称号页；统计页无纪录 |
| 大厅 | `gui_hub.py` 53 行，公告 + 8 个按钮 | 不显示称号 |
| 爬塔持久化 | `tower.persist` 只回写 11 个玩家字段白名单 | 新字段若不加白名单，爬塔一轮会丢 |
| 校验器 | 16 项，`check_migrate` 硬编码字段清单，V28-01 legal 集合 6 种 | 新字段/新条件类型不登记就漏检 |
| 资源打包 | `build.py` 打 `assets/` → `assets.mpak`，validate 用 `data_rows()` 读 | 加 `titles.txt` 要重打包 |

关键结论：**精英/稀有击杀必须新增计数**（现有 kills 无法区分），因此 schema 必然升 10；称号与纪录同批加字段，一次迁移做完，避免连升两版。

## §1 裁决（建议冻结值，待业主确认）

| 编号 | 裁决 | 理由 |
|---|---|---|
| R1 | 新增 `elite_kills` / `rare_kills` 两个整数计数；**主线 win 时**按 `f.get("elite")` / `f.get("rare")` 递增；**爬塔不参与** | 塔不调 `apply_encounter`，本来就没有精英/稀有；且塔无限层会刷计数 |
| R2 | 不把变体塞进 `kills`（如 `"elite:huoyao"`） | `kills` 同时喂怪物图鉴与 `kills_total`，加前缀会污染图鉴显示与总击杀口径（V2.8 才刚修过 `lose:` 前缀的同款坑） |
| R3 | 称号表 `assets/titles.txt`（`id|名称|成就id|描述`），**8 条，与 8 个成就 1:1**；解锁 = 对应成就已解锁 | 不引入新条件类型；validate 可交叉校验引用；纯荣誉不加属性（路线稿 D10） |
| R4 | 存档新字段 `title`（存称号 id，空串=不佩戴）；**图鉴窗新增第 5 页「称号」可佩戴**——这是唯一写档的页 | 玩家主动选择必须落盘；其余四页维持只读，冻结稿明示该例外 |
| R5 | 大厅顶部显示「称号：X」（无则「无」） | 称号要有可见性，否则等于没做 |
| R6 | 幻影榜只做三项本地纪录：**单场最高伤害**（数值+怪名）、**单场最少回合**（仅 win，数值+怪名）、**爬塔最高层**（复用 `tower_best`） | 周目竞速要新增"本周目起始时间"字段且会被读档/暂停污染，收益低，本期不做 |
| R7 | 幻影榜**并入统计页**（追加 3 行），不新开第 6 页 | 四页结构刚在 V2.8 定版，加页会让窗口变重 |
| R8 | 新增 2 条成就：`elite_hunter`（精英 10 只）、`rare_hunter`（稀有 3 只）；`legal` 集合扩到 8 种 | 精英/稀有是本季新内容，需要对应的长期目标 |
| R9 | **schema 10**：新字段 `elite_kills` / `rare_kills` / `title` / `records`；v9→v10 只补默认值，**旧数值一字不动** | 迁移纪律与 v7→v8、v8→v9 一致 |
| R10 | 施工分两批：**D1a 数据层先行**（schema/计数/成就/校验），**D1b 表现层后做**（称号页/大厅/纪录展示） | 数据层高风险（迁移），UI 低风险，先隔离 |

## §2 数据落点

### 2.1 新表 `assets/titles.txt`（新增文件，需 `python build.py` 重打 mpak）
```
# id|名称|成就id|描述
first_blood|初出茅庐|first_blood|初次出手便见血
clear_all|西行者|clear_all|十图走尽
max_level|齐天大圣|max_level|修到封顶
full_arsenal|兵器谱主|full_arsenal|十器尽收
tower30|登塔人|tower30|三十层之上
enhance10|炉火纯青|enhance10|一件装备强化到 +10
elite_hunter|猎妖人|elite_hunter|十只精英伏诛
rare_hunter|捕金者|rare_hunter|三只稀有落袋
```

### 2.2 `achievements.txt` 追加 2 行
```
elite_hunter|猎妖人|累计击杀 10 只精英怪|elite_kills|10
rare_hunter|捕金者|累计击杀 3 只稀有怪|rare_kills|3
```

### 2.3 存档新字段（schema 10）
| 字段 | 默认 | 语义 |
|---|---|---|
| `elite_kills` | 0 | 主线精英击杀累计（跨周目继承） |
| `rare_kills` | 0 | 主线稀有击杀累计 |
| `title` | `""` | 当前佩戴称号 id，空 = 无 |
| `records` | `{"best_dealt":0,"best_dealt_mon":"","best_rounds":0,"best_rounds_mon":""}` | 幻影榜（`best_rounds=0` 表示暂无） |

跨周目：四个字段全部**继承**（与 `tower_best` / `total_damage` 同例，新周目不清零）。
`records` 只在 **win** 时更新：`dealt` 更大才换、`rounds` 更小才换（同级不换，先到先得）。

## §3 代码落点与行数（显式修订）
| 模块 | 现行 | 改动 | 上限 |
|---|---|---|---|
| progress.py | 87 | `load_titles()`（约 10 行）+ `on_battle_win(player, fight, rep)`（约 10 行，管计数+纪录）+ `evaluate` 的 stat 加 2 键 | **110** |
| save.py | 118 | `_migrate` 加 4 个 setdefault + `write` 加 4 个字段 + norm 加 2 键 | **130** |
| engine.py | 222 | win 分支 1 行 `progress.on_battle_win(player, f, rep)`（分号合并进现有行或独立 1 行） | **225** |
| tower.py | 100 | `persist` 白名单加 3 个玩家字段（`elite_kills`/`rare_kills`/`records`；`title` 不在 player 上） | **100 不变**（分号合并） |
| validate.py | 160 | `check_migrate` 键表加 4 键 + 新增 `check_v31`（titles 合法 + 成就引用存在）→ 17 项 | **170** |
| gui_codex.py | 85 | 称号页（QComboBox + 佩戴按钮 + 当前称号标签）约 +25、统计页追加幻影榜 3 行 | **120** |
| gui_hub.py | 53 | 称号标签 + refresh 读档 | **65** |
| encounter/combat/gui/gui_tower | 170/130/207/174 | **不动** | 不变 |

行数门禁同步：v22–v29c 里 `engine≤222` → `≤225`、`validate≤165` → `≤170`（功能断言不动，只改计数；先例 V2.9-B）。

## §4 schema 与迁移
- `SCHEMA = 10`；迁移链注释补 `→ v10（称号/变体击杀/纪录）`。
- `_migrate` 只 `setdefault`，**不改任何已有数值**；`records` 用 `dict(...)` 深拷贝默认值，避免共享可变对象。
- 实测要求：造一份 v9 档（含 achievements/codex/total_damage/staff_pity 非默认值）→ `save.load()` → 断言四个新字段就位且旧值逐个不变。

## §5 出口验收（smoke_v29d1，八门禁）
1. **计数**：主线 win 一场精英 → `elite_kills` +1、`rare_kills` 不变；稀有同理；普通怪两者都不增。
2. **不污染图鉴**：跑完上述战斗后 `kills` 键仍是怪物 key（实跑键集合 ⊆ monsters.txt 的 key），无 `elite:` / `rare:` 前缀。
3. **成就**：`elite_kills=10` / `rare_kills=3` 达阈值解锁；未达不解锁；老 6 条不受影响（并集不回归）。
4. **称号表**：8 条加载成功、id 唯一、引用的成就 id 都存在；未解锁的称号不能佩戴（GUI 层拦截 + 数据层判定同源）。
5. **佩戴与显示**：佩戴写 `title` 后重读存档仍在；大厅显示「称号：X」；空串显示「无」。
6. **幻影榜**：更高伤害才刷新、更少回合才刷新、反向不覆盖；怪名随之记录；塔层复用 `tower_best`（不新增字段）。
7. **迁移**：v9 档 → v10 四字段就位、旧值不变；`validate` 十七项全绿。
8. **行数 + 全链**：progress≤110 / save≤130 / engine≤225 / validate≤170 / gui_codex≤120 / gui_hub≤65 / tower≤100；`v20→…→v29c` 全链回归绿。

## §6 风险与硬禁区
- **迁移不许丢值**：`_migrate` 只补默认，禁止顺手"修正"旧数值；`records` 默认值必须深拷贝。
- **计数只认 win**：dead/escaped/fled 一律不加；fled 是"怪跑了"，更不能算击杀（与 V2.9-B 语义一致）。
- **不得改 `kills` 键结构**：图鉴、总击杀、隐藏任务 `lose:` 判定都依赖它。
- **称号写档范围最小**：只写 `title` 一个字段，其余字段原样带回（`write_raw` 前先 `load()` 再改一个键）。
- **爬塔不记纪录**：塔无限层会刷榜；`tower.persist` 只做字段透传，不调 `on_battle_win`。
- **成就并集永不回归**：`save.write` 与 `tower.persist` 都取「旧档 ∪ 本次」，新成就不例外。

## §7 明确延期
- 属性称号（加数值），须单独立项重测叠加。
- 周目竞速榜（要周目起始时间字段）。
- 全服/联网排行（红线：不做联网）。
- 称号特效/图标（美术资源，本期纯文字）。

## §8 施工分批
- **批 D1a（数据层，高风险）**：titles.txt + achievements 追加 + `progress.on_battle_win`/`load_titles` + `save` schema 10 迁移与写入 + engine 1 行 + tower.persist 白名单 + validate V31-01/17 项 + smoke_v29d1 门禁 1/2/3/7/8。
- **批 D1b（表现层，低风险）**：gui_codex 称号页与幻影榜段 + gui_hub 称号显示 + 门禁 4/5/6。
- 两批独立 commit，D1a 全绿后再动 D1b。

> 本文件为冻结稿草案，**未提交、未施工**。业主确认 R1–R10 后入仓，再一句话开工 D1a。
