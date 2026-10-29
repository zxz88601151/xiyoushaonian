# MiniAsura V2.9-B 设计冻结（爬塔战报接入 + 稀有怪 fled）

## 基线
3487ddb（V2.9-A Windows 真机毕业 + README 订正）。schema 9 不变（**本期不升 schema**，fled 不存档）。
本期做头脑风暴 §8 的 V2.9-B 两件事：① 爬塔战报接入（B1，零风险先做）；② 稀有怪 3 回合 fled 返回值（B2，高风险后做）。
GUI 战斗窗战报主线 V2.9-A 已接（引擎战报行经 `io.say` 进 GUI 日志），本期"显眼化"（独立面板/常驻显示/多场合计）明确不做，留待 V2.9-D。

## §0 已确认裁决（业主 2026-10-29 22:09 确认 C1–C6，含两条修订）

| 编号 | 裁决（冻结值） |
|---|---|
| C1 | fled = **推进**（fi+1，继续推图，不回大厅，不可重打）。回大厅则 3 回合机制失效，已否决。 |
| C2 | fled **算本场已处理**（图内 fights 全处理完才通图，否则图末稀有跑了→永久软锁）。 |
| C3 | fled **不打印战报**，只打印 1 行事件行（与 escaped 一致：没分胜负不打印战报）。 |
| C4 | **显式放宽** encounter 160→170、engine 220→222、validate 160→165；combat 130 / tower 100 不变（fled 调用与战报传递走分号合并，复用 V2.9-A house style）。先例：validate 150→160（V2.8）、engine 200→220（V2.7），均为显式修订非静默放宽。 |
| C5 | tower **本期不启用稀有**（不调 apply_encounter，fled 在塔不触发）；若意外触发，fail-closed：按 escaped 处理 + 打 WARN 日志，不静默吞。 |
| C6 | 施工顺序：**B1 爬塔战报先**（1 处改动零风险，独立 commit + smoke 验证），**B2 fled 后**（返回值契约扩展，独立 commit + smoke_v29b）。先收割低风险，高风险单独隔离。 |

## §1 子系统与冻结数值

### 1.1 爬塔战报接入（B1，零风险）
- `tower.run_one`（tower.py:47-65）调 `combat.battle` 时**补传 `rep={}`**：现 :53 `result = combat.battle(cfg, skills, mon, player, io)` → `rep={}; result = combat.battle(cfg, skills, mon, player, io, rep)`（分号合并，tower 仍 100 行）。
- win 与 dead 都调 `encounter.print_report(io, rep)`（与主线一致：dead :187 也打印，escaped/fled 不打印）：
  - win 分支（:58-65）：在 `io.say("  ▸ 已到第 %d 层...")` 前分号合并 `encounter.print_report(io, rep);`
  - 非 win 分支（:54-57）：`player["tower_layer"]=0` 后、return 前分号合并 `encounter.print_report(io, rep);`
- 爬塔 boss（守层妖王 key=boss）自动适用：BossPhase 在 combat 已建（combat.py:72），骨刺雨伤害已计入 `rep["taken"]`（encounter.py:65-66），战报接上后爬塔 boss 战报自动含骨刺雨，不用另改。
- `tower.persist` 不动：战报是单场数据不进存档（与主线一致）。
- 爬塔 escaped 仍**不打印**（与主线 escaped 一致），不要顺手把 escaped 也打印，否则"逃跑不打印"定版语义被悄悄改掉。

### 1.2 稀有怪 fled（B2，返回值契约 3 值 → 4 值）
`combat.battle` 契约从 `win/dead/escaped` 扩为 `win/dead/escaped/fled`。
- **触发条件（全满足）**：① `encounter.is_rare(mon)` 为真（稀有怪）；② 回合末 `rep["rounds"] >= flee_rounds`（默认 3）；③ 怪还活着（`m_hp > 0`）；④ 玩家未死（`player["hp"] > 0`，**dead 优先**，见 F1）。
- **触发点**：combat.py:124 回合末序列 `buff=0.0; rep["rounds"]+=1; phase.spike(...) if phase else None` 之后、`:126 if player["hp"]<=0: return "dead"` 之前，分号合并 `; encounter.fled_check(mon, rep, player, io)`。返回 `"fled"` 或 `None`（None=继续战斗）。
- **fled 时**：`io.say(f"{mon['name']}溜走了！紫装机会没了。")`（事件行，非战报），`return "fled"`，**不打印战报**（rep 扔掉，与 escaped 一致）。
- **不触发**：普通怪、精英怪（精英是"硬骨头"语义，玩家拖是被打不是主动；稀有是"限时肥羊"语义，限 3 回合抢——只有稀有 flee，见 F4）、boss（boss 逃跑失败的语义不变）。

### 1.3 mon 标记与判定函数（B2，修断点4）
- `apply_encounter`（encounter.py:99-103）稀有分支补设 `mon["rare"] = True`（现只设 `fight["rare"]`，combat 收 mon 不收 fight 无法判）。
- 新增 `encounter.is_rare(mon)`：`return bool(mon.get("rare"))`（看字段不看名前缀，防改名/翻译/去前缀漂移）。
- 新增 `encounter.fled_check(mon, rep, player, io, flee_rounds=3)`：稀有 + rounds>=flee_rounds + 活着 + 玩家活着 → say + return "fled"；否则 return None。
- 精英不设 `mon["rare"]`，故 `is_rare` 对精英返回 False，fled 不误伤精英。

## §2 数据落点（全走 game.ini，不动 mpak）
- 新增段 `[rare_flee]`：`flee_rounds = 3`（不硬编码 3，与 boss_phase / encounter 同例；硬编码会让调参必改代码，违 V2.9-A 约束）。
- 不改 maps.txt / monsters.txt / skills.txt / dialogue.txt / quests.txt / assets.mpak。
- GUI 不动（fled 事件行经 `io.say` 自动进 GUI 日志，与战报同路径）。

## §3 模块分工与行数纪律（显式修订，非静默放宽）
| 模块 | 现行/上限 | 本期 | 修订后上限 |
|---|---|---|---|
| encounter.py | 154/160 | +`is_rare`(2行) +`fled_check`(8行) +`mon["rare"]`补设(1行) +V30校验(见下) | **160→170**（显式放宽，先例 validate/engine） |
| engine.py | 220/220 | +fled elif 分支(1行: `elif result=="fled": io.say(...)`)，插 escaped(:191-197) 与 win(:198) 之间；fled 不 return，自然落 :202 `fi+=1` + :203 `persist` | **220→222**（显式放宽） |
| combat.py | 130/130 | :124 末尾分号合并 `; encounter.fled_check(mon, rep, player, io)`；fled 时函数内 return | 130 不变（分号合并，house style） |
| tower.py | 100/100 | :53 分号合并 rep 传递；win/非win 分支分号合并 print_report | 100 不变（分号合并） |
| validate.py | 160/160 | +V30-01 校验函数(住 encounter.py，validate 只 import 拼接，2 行) | **160→165**（显式放宽） |
| loot.py | 78/100 | 不动 | 100 不变 |

行数纪律门禁同步更新：smoke_v25/v26/v27/v28/v29a 的行数断言由 encounter≤160/engine≤220/validate≤160 改为 ≤170/≤222/≤165（功能断言不变，只改计数，遵循 V2.8 时 validate 9→12 的基线显式重定先例）。

## §4 schema
**不升 schema。** fled 只影响当场 `fi`（fi 机制不变），不存档。不记"稀有逃跑次数"统计（若未来要记，记在 `total_damage` 同类统计里仍不升 schema，本期不做）。

## §5 出口验收（smoke_v29b，七门禁）
1. **爬塔战报（B1）**：构造 win 战斗，`tower.run_one` 后日志含"战报：X回合 / …"一行；构造 dead 战斗，dead 也打印战报；escaped 不打印。
2. **fled 触发**：构造 week3 save（`week=3`），run_game 到 fi5（图7火妖，确定性掷骰必为稀有，base 70×1.6=112→稀有 56 血/11 攻），3 回合内不打死 → fled，日志含"金色·火妖溜走了！紫装机会没了。"；无掉落（`loot.rare` 池不调）、无击杀（`kills` 不增）、无任务推进（`on_event("win")` 不调）；`fi` 前进到 6，继续推图不回大厅，图7仍通关（fled 算本场已处理）。
3. **fled 不误伤**：普通怪（fi0 图1小妖甲）拖 3 回合不 flee；精英怪（week0 fi0 精英·小妖甲）拖 3 回合不 flee；boss 不 flee。
4. **dead 优先（F1）**：构造 fled 回合玩家同时被打死（hp 归零）→ 返回 `"dead"` 不是 `"fled"`（dead 分支在 fled_check 之前判）。
5. **玩家逃跑仍是 escaped**：稀有战中玩家选 act 3 → `"escaped"`，回大厅、可重打、同一只稀有再出现（fi 不变，掷骰不变）。
6. **回归**：week0 全通基线不变（Lv.25 / 金币 798 / maps 10 / 战报出现）+ tower 无稀有断言（`tower.run_one` 不调 apply_encounter，塔怪 mon 无 `rare` 字段）+ smoke_v29a 19/19 回归绿。
7. **行数纪律**：encounter≤170、engine≤222、combat≤130、tower≤100、loot≤100、validate≤165 全过；validate 十六项全绿（15 + V30-01）。

## §6 数值风险与取舍（先写下来）
- **fled 不发奖励是硬禁区**：fled 分支**绝不调** `loot.grant_win`、**绝不调** `tracker.on_event("win")`、**绝不调** `on_event("lose")`（fled 不是败北）。否则"稀有跑了"变成"稀有白送"或"跑了算败北扣经验"，比不做还糟。门禁 7 静态断言 engine fled 分支无此三调用。
- **week0 全通今天不红是"碰巧"不是"机制安全"**：week0 稀有 0 只（实测），week3 稀有 fi5 火妖 56 血 1 击即死（3 回合内必死，不 fled）。但任何 encounter 概率/种子/地图顺序/难度/用药/MISS/技能 CD 拖回合的改动，都可能让稀有在全通里 fled；一旦 fled 且复用 escaped（fi 不加+return），`maps_cleared<10` 全通红，红的原因是"语义错"不是"数值错"，排查会误导到数值上。**fled 推进语义（C1）正是消除这个风险**——fled 推进不 return，全通不卡。
- **用药/MISS 加速 fled 是机制本意**：V2.9-A rounds 口径=怪物回合+终结一击（用药回合怪物照样出手故计入，MISS 也算怪物回合）。所以"3 回合 fled"=3 次玩家行动（普攻/技能/用药都算，MISS 也算）。用药会加速 fled——这是"喝药就拖时间"的本意，但战斗提示必须写出"金色·X 看起来要溜走了！"（fled_check 在 rounds>=2 时预警），否则玩家觉得"喝个药它就跑了"是 bug。
- **fled 后本周目后续可能再出稀有**：fi 前进只保证"本场这只稀有没了"，不保证"本周目不再有稀有"（后续 fi 的掷骰独立）。这是合理的——fled 是"失去本次机会"不是"净化全图"。

## §7 明确延期（本期不做，不算缺口遗漏）
- GUI 战斗窗战报"显眼化"（独立面板 / 常驻显示 / 多场合计），留待 V2.9-D（本期 GUI 战报已通，差的只是 UI）。
- 精英怪 flee（精英 hp×1.5 是硬骨头语义，本期只稀有 flee）。
- tower 启用稀有（须先改 `tower.run_one` 的 `result!="win"` 分支，否则 fled 被误当 dead 清零层数；本期 tower 无稀有故不触发，fail-closed 兜底）。
- 稀有怪 3 回合逃跑的"逃跑动画/音效"（红线，不做）。
- 稀有/精英专属称号与成就（成就表不动，留待 V2.9-D 留存期）。

## §8 施工分批（C6：B1 先，B2 后）
- **批 B1（爬塔战报，零风险）**：改 tower.py 1 处（rep 传递 + print_report 分号合并），跑 smoke_v29b 门禁 1 + smoke_v29a 回归，独立 commit。B1 完成验证后再动 B2。
- **批 B2（稀有 fled，高风险）**：改 encounter.py（is_rare+fled_check+mon["rare"]+V30-01）/ combat.py（:124 分号调 fled_check）/ engine.py（fled elif 分支）/ game.ini（[rare_flee]）/ validate.py（import V30）/ 行数门禁同步，跑 smoke_v29b 门禁 2-7 + smoke_v29a 回归 + week0 全通基线重定，独立 commit。
- 两批共一份冻结稿（本文件），施工按 B1→B2 顺序，不并行、不跨批。
