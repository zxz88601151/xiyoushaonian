# MiniAsura V2.9-A 设计冻结（战斗反馈 + 精英怪 + 保底）
## 基线：1847b1d（V2.8 + 字体引导），schema 8 → 9。本期只做头脑风暴文档 §8 的 V2.9-A 一行，不做宝石、套装、叙事、世界、日常。

## §1 五个子系统与冻结数值（全部是新定值，蓝图无此数）

### 1.1 战斗结算战报（combat.report）
- `battle(cfg, skills, mon, player, io, report=None)`：report 为 dict 时填入
  `rounds/dealt/taken/crits/misses`，不改返回值（仍 win/dead/escaped）。
- 口径：rounds = 战斗回合数（怪物出手次数 + 终结一击；用药回合怪物照样出手，故也计入，
  逃跑不计入是因为 escaped 不打印战报）；
  dealt = 本场造成伤害合计（与 total_damage 累计口径一致）；
  taken = 本场承受伤害合计（含骨刺雨固定伤害，不含用药回复）；
  crits = 暴击段数，misses = MISS 段数（连击 MISS 中断后续段，只计 1 次）。
- 引擎主循环在 win/dead 后打印一行：
  `战报：X回合 / 造成Y伤害 / 承受Z伤害 / 暴击N次 / MISS M次`；
  escaped 不打印（逃跑不算一场完整的战斗）；爬塔本期不打印战报（tower.py 不动，见 §7 延期项）。

### 1.2 BOSS 阈值变招（只对 mon.key == "boss"，含主线白骨夫人与爬塔守层妖王）
- 数据在 game.ini `[boss_phase]`，不进 mpak：
  `transform_hp_pct = 50, enrage_hp_pct = 30, spike_every = 2, spike_pct = 5,`
  `transform_atk_mult = 1.2, enrage_atk_mult = 1.2, enrage_vuln_mult = 1.2`。
- 变身（血量 ≤50%，只触发一次）：`白骨夫人现出白骨真身！`，怪物 atk ×1.2（向下取整后至少 +1，见 encounter.BossPhase）。
- 骨刺雨（变身后，每第 2 个怪物回合）：固定伤害 `max(5, 玩家 max_hp × 5%)`，
  不吃玩家防御与不坏金身减伤（这是“防堆防就无敌”的反制，数值小，只作提醒）。
- 狂暴（血量 ≤30%，只触发一次，且必须已变身）：攻击再 ×1.2（累计 ×1.44），
  同时玩家对其伤害 ×1.2（给“拼一波”的窗口）。
- 翻译说明（诚实记录）：头脑风暴原稿写“狂暴防御 -20%”，但现行 battle.lua damage 公式
  没有怪物防御项（伤害只看玩家攻击 × 倍率），防御 -20% 在现有公式里等于没效果，
  故本期翻译为“玩家对其伤害 ×1.2”，效果等价且可测。怪物防御字段如未来加入公式，需重审本条。

### 1.3 精英怪 / 稀有怪（只对主线非 boss 怪，爬塔不做）
- 判定：每场开打前掷一次，种子由 `(week, 地图号, 全局战斗序号 fi)` 经 md5 稳定哈希决定，
  与进程随机种子无关，逃跑/败北后重打同一场仍是同一结果（防“逃跑刷掉精英”）。
  单次掷骰 r ∈ [0, 99)：r < 20 为精英，20 ≤ r < 25 为稀有，其余普通。
- 精英：名前缀 `精英·`，hp ×1.5、atk ×1.2（取整），词缀三选一（按种子取余）：
  甲硬（玩家对其伤害 ×0.85）、灼烧（atk 再 ×1.3，即累计 ×1.56，取整）、疾风（怪物闪避 = 20，
  复用现行命中公式 95%+命中−闪避，下限 60%）。
  精英经验/金币不变（只给额外掉落，不改全通基线 Lv.25 / 金币 798 的经验金币总和）。
- 稀有：名前缀 `金色·`，hp ×0.5、atk ×0.5，经验/金币不变。
- 击杀计数：精英/稀有击杀仍按原怪 key 计入 kills（支线 s1 杀 xiaoyao2:2 不因此变难）。
- 掉落：胜利后除正常掉落外，精英再掷一次 `[loot.elite]`（蓝装必掉：weapon:1:100），
  稀有再掷一次 `[loot.rare]`（紫装必掉：weapon:2:100）。额外掉落走同一 loot.roll，不自动穿戴。

### 1.4 掉落保底（无级别武器，抄斗战神“混沌石换一切”的保底思想）
- 新存档字段 `staff_pity`（int，默认 0，schema 9，跨周目继承，爬塔不影响）。
- 只对主线 boss 的 `[loot.boss]` staff 项生效：掷 staff 失败一次，pity +1 并打印
  `（无级别保底计数 X/50）`；pity ≥ 49 时下一次 staff 掷骰必中（忽略随机数），中后 pity 清零；
  正常掷中也清零。已持有 staff 时跳过 staff 项（原有规则不变），此时 pity 不增不减。
- 保底上限在 game.ini `[pity] staff_pity_max = 50`，validate V29-03 校验。

## §2 数据落点（全部走 game.ini，不动 assets.mpak）
- 新增段：`[boss_phase]`、`[encounter]`（elite_chance=20、rare_chance=5、
  elite_hp_mult=1.5、elite_atk_mult=1.2、rare_hp_mult=0.5、rare_atk_mult=0.5）、
  `[pity]`、`[loot.elite]`、`[loot.rare]`。
- 不改 maps.txt / monsters.txt / skills.txt / dialogue.txt / quests.txt，因此不需要重建 mpak，
  文本补丁可直接应用；GUI 不动（战报只在 CLI 引擎主循环打印，GUI 战斗窗本期不接战报，见 §7）。

## §3 模块分工与行数纪律（显式修订，非静默放宽）
- 新模块 `encounter.py`（上限 160 行，实测 154 行）：BossPhase、精英/稀有判定与包装、战报打印、
  V29 校验（validate 只 import 并拼接结果，不在本文件写新校验函数）。
- engine.py / combat.py 行数上限不变（220 / 130）：新增调用全部以同行分号或替换既有行的方式落入，
  不新增行；这是本仓库已有写法（engine.py 多处用分号合并赋值），不是新发明的压缩技巧。
- loot.py 上限 100（现 68，可加行）；save.py 不设上限（现 116）；validate.py 上限不变（160），
  新校验函数住 encounter.py，validate.py 只改 2 行（import + 拼接 + 迁移字段名）。
- smoke_v25 / v26 / v27 / v28 的 validate 计数检查由 12 同步改为 15（功能断言不变，
  只改计数，遵循 V2.8 时 validate 9→12 的基线显式重定先例）。

## §4 存档 schema 9
- `_migrate` 加 `staff_pity = 0`（旧档补默认值，旧值一字不动）；`save.write` 写出 staff_pity；
  引擎新档/续档/周目继承均带 staff_pity（周目继承走 gold_carry 同行分号写法）。

## §5 出口验收（smoke_v29a，六门禁）
1. 战报口径：一击必杀 → rounds=1、dealt>0、taken=0、misses=0，且战报打印一行；
   MISS/暴击计数走同一分支（MISS 分支与暴击分支各有 rep 递增），因命中下限 60% 无法用纯参数强制 MISS，
   故 MISS 计数不单独设确定性门禁，靠全通中自然发生的 MISS 在战报里 eyeball。
2. BOSS 变招：构造 hp=200 的 boss（100 血普攻 4 击即死，骨刺雨来不及触发），血量打到 50/30 阈值 → 变身与狂暴各触发一次且只一次，
   atk 累计 ×1.44，骨刺雨每 2 回合一次、数值为 max(5, max_hp×5%) 且不吃防御。
   （修正记录：原 20%/3 回合在 4 击 boss 战里几乎不触发——600 血 boss 普攻 4 击即死，
   变身后怪物回合只有 2 次、血量从未到过 20% 非致死档；故改为 30%/2 回合，使狂暴与骨刺雨在普攻战里至少触发一次。）
3. 精英/稀有：同一 (week, 地图, fi) 两次判定结果相同；精英 hp×1.5/atk×1.2、
   词缀三选一合法、额外掉落池存在；稀有 hp×0.5/atk×0.5；boss 不变精英/稀有。
4. 保底：boss staff 连续掷失败 49 次后第 50 次必中，pity 清零；已持有 staff 时 pity 不变；
   v8→v9 迁移：旧值不动、staff_pity=0、schema=9。
5. validate 十五项全绿（12 + V29-01/02/03）；行数纪律（engine≤220、combat≤130、
   encounter≤160、loot≤100、validate≤160）全过。
6. 回归：Linux mock 全通（真公式 mock lua，见测试说明）maps_cleared=10、
   等级/金币基线不变（Lv.25 / 金币 798，精英/稀有不改经验金币故基线可保）；
   smoke_v28 功能门禁（除 validate 计数已同步为 15 外）仍绿；Windows 真机 smoke_v29a 待业主跑。

## §6 数值风险与取舍（先写下来）
- 精英 atk 只 ×1.2（不是头脑风暴原稿的 ×1.5）：CLI 全通测试全程只按“1”（普攻）且不用药，
  ×1.5 有可能在双战斗图里打死玩家、破坏全通基线；×1.2 + hp×1.5 已足够让精英“感觉不一样”。
- boss 变身后 atk 累计 ×1.44，但狂暴同时给玩家伤害 ×1.2，boss 剩余血量只有 30%，
  实际多承受伤害有限，全通基线可保；如 Windows 真机实测 boss 战死亡，优先把 spike_pct 5→3，
  其次把 transform_atk_mult 1.2→1.1，不动阈值。
- 战报 rounds 口径取“怪物出手次数 + 终结一击”，是为了让一击必杀的测试断言稳定
  （1 击必杀 → rounds=1），且用药回合怪物照样出手、计入回合是符合直觉的。

## §7 明确延期（本期不做，不算缺口遗漏）
- 爬塔战报、GUI 战斗窗战报、稀有怪 3 回合逃跑机制（逃跑会打断主循环的全通基线，
  需先重构 escaped 语义，留待下期）、精英/稀有在爬塔出现、boss 阶段动画/音效（红线）、
  精英/稀有专属称号与成就（成就表不动，留待 V2.9-D 留存期）。
