# 西游记文字版 —— 游戏客户端逆向学习实验室 + MiniAsura

**现址：`D:\西游记文字版`**（2026-10-28 由 `F:\WeGameApps\斗战神\learn-lab` 全量迁出，游戏本体仍在 F 盘原位、未动一字节）

这是我们的学习工作区。**游戏本体目录只读不改**，所有练习、脚本、笔记都放在这里。

## 铁律
1. 不修改、不删除、不移动本目录之外的任何游戏文件
2. 想实验某个游戏文件 → 先复制到本目录里再动手
3. 不做注入、不做外挂，只学原理

## 路径约定（搬迁后）
- 所有脚本以自身位置 `__file__` 为锚点解析 `../lesson03`、`../tools`，**与盘符无关**，整个目录可任意搬迁
- 唯一例外：`lesson02/scan_files.py`、`scan_sizes.py` 里的 `GAME_DIR = r"F:\WeGameApps\斗战神"` 是**故意指向游戏本体**（教学目标），不要改
- 直接调用解释器请用相对路径 `..\tools\lua-5.1.5\lua.exe`；终端里敲 `lua` 依赖用户 PATH，若失效见下方「环境」

## 学习路线（完成一项打勾）

- [x] 第 1 课：认识文件格式（INI / JSON / 节、键值、注释、数组）✅ 2026-10-28
- [x] 第 2 课：用 Python 拆配置文件（scan_files.py 个数统计 + scan_sizes.py 体积统计）✅ 2026-10-28，理解模块化与资源打包
- [x] 第 3 课：迷你 VFS 打包器 mypack.py（pack / unpack / get 按名取文件全通，含 fail-closed 报错路径）✅ 2026-10-28，理解魔数/索引区/数据区/seek 随机访问
- [x] 第 4 课：Lua 5.1 语言入门 ✅ 2026-10-28（语法五件套 + 函数/条件 quest.lua 全过；环境 lua-5.1.5 自编译于 tools/；踩坑收获：下标从 1 开始、越界返回 nil 不报错、漏 return 返回 nil）
- [x] 第 5 课：PE 文件与 DLL 依赖（只读查看）✅ 2026-10-28 毕业（导入表透视 + 身份鉴定：Asura.exe 是 ACE 加壳、VS2008 原始工具链、AsuraBase.dll 是现代工具链的壳引导员；脚本 pe_inspect.py / pe_fingerprint.py）
- [x] 第 6 课：架构复盘 ✅ 2026-10-28 终审通过，**全部六课毕业**（notes/lesson06_recap.md 三部分全过；新引用实物 chunkdata.vfs 5.48GB / data.vfs 54MB / Container_Login.tpf 均经抽查属实；核心结论："引擎冻结，功能流动——老代码不是被维护活下来的，是被隔离活下来的"）

## 目录结构
```
西游记文字版/           ← 现址 D:\西游记文字版
├── README.md        ← 本文件（路线图）
├── notes/           ← 学习笔记
├── lesson01/        ← 每课一个目录，放练习成果
├── lesson02/
├── lesson03/        ← mypack.py（被 miniasura 复用）
├── lesson04/  lesson05/
├── tools/           ← lua-5.1.5（自编译解释器）
└── miniasura/       ← 按斗战神图纸复刻的文字版游戏（V2.9-D2）
```

## 进度记录
| 日期 | 内容 | 状态 |
|---|---|---|
| 2026-10-28 | 建立 learn-lab，第 1 课开始 | 进行中 |
| 2026-10-28 | 第 1 课通关（14 App / game_wiki 热更 / 数组符号）| ✅ 毕业 |
| 2026-10-28 | 第 2 课开始：第一个 Python 脚本 | 进行中 |
| 2026-10-28 | 第 3 课通关（mypack.py pack/unpack/get + seek 随机访问原理） | ✅ 毕业 |
| 2026-10-28 | 第 4 课通关（自编译 Lua 5.1.5 + player.lua + quest.lua，踩坑：下标 1 起 / 漏 return 返 0 个值） | ✅ 毕业 |
| 2026-10-28 | **整体搬迁** `F:\WeGameApps\斗战神\learn-lab` → `D:\西游记文字版`（77 文件/840KB，游戏本体未动）；搬迁后 build/Lua/mypack/装备公式 + smoke_v22 27 项 + V2.0/V2.1 回归全绿；顺手修复 smoke_v22 败北用例游标矛盾（maps_cleared 0→9） | ✅ 迁移过 |
| 2026-10-28 | 第 5 课第 1 步：PE 导入表透视（Asura.exe / VFS.dll / AsuraBase.dll / Lua51.dll） | 进行中 |
| 2026-10-28 | 第 5 课毕业：身份鉴定（节熵 / Rich 头 / 链接器三指纹互证，Asura.exe=ACE 壳 + VS2008 原始构建；时间戳=打壳日期非代码年龄） | ✅ 毕业 |
| 2026-10-28 | **MiniAsura 项目立项**（§0 设计冻结已授权，终端文字版） | 🚀 |
| 2026-10-28 | §1 通关：game.ini + 素材×3 + build.py（复用 mypack 打包，门禁取回验证通过） | ✅ 毕业 |
| 2026-10-28 | §2 进行中：engine.py 回合制主循环 | 进行中 |
| 2026-10-28 | §2 通关：150 行 engine.py，4 战 4 胜，升级跨级链正确（Lv.14→19） | ✅ 毕业 |
| 2026-10-28 | §3 通关：数值逻辑全迁 battle.lua（damage/levelup/attack 三命令，一行 JSON 通信）；验收 3/4 实测通过——改 ini boss 血 999 生效、改 Lua 暴击 ×3 生效（114→171），均零代码改动，恢复后双回归通过 | ✅ 毕业 |
| 2026-10-28 | MiniAsura v1 核心完工：DESIGN 四条验收全绿。§4 存档为可选项 | 🏁 |
| 2026-10-28 | 第 6 课收官笔记交稿：notes/lesson06_recap.md（启动链分层 / Cross 插件容器 / 全史结案），待终审 | 待终审 |
| 2026-10-28 | MiniAsura §0 设计冻结 v1.1（采纳 3 修正：argv 数字/ASCII 铁律、复用 mypack 不 fork、攻击力公式归 Lua） | ✅ 冻结 |
| 2026-10-28 | MiniAsura §1 通关：game.ini 全数值外置 + 纯文本素材 + build.py 一键打包，mypack get 取回三素材、逐字节回环一致 | ✅ 门禁过 |
| 2026-10-28 | MiniAsura §2 通关：mypack 新增 read() 库函数（get 回归一致）+ engine.py 150 行回合制主循环，完整通关含升级/暴击/逃跑路径 | ✅ 门禁过 |
| 2026-10-28 | MiniAsura §3 通关（灵魂课）：数值公式迁 battle.lua，引擎 subprocess 调 lua.exe 只传一行 JSON；验收 3/4 实测过——改 Lua 暴击 285→427、改 ini boss 220→999，均不改代码生效 | ✅ 验收过 |
| 2026-10-28 | MiniAsura v1.2 增补开工（业主授权"§4 存档 + PySide6 界面"）：save.py 外围模块 + engine.py Io 注入重构（CliIo/GuiIo 同接口） | 🚧 |
| 2026-10-28 | MiniAsura §4 通关：逐胜写档，通关存档 cleared=true 开新周目、中断后重开从第 2 战继续（等级/HP/MP 全还原）；DESIGN.md 升 v1.2 | ✅ 验收过 |
| 2026-10-28 | MiniAsura §5 通关：gui.py（PySide6 外壳，引擎零 Qt 依赖），自动输入冒烟全通关 + 截图 gui_smoke_20261028.png 为证，save.json cleared Lv.19 | ✅ 验收过 |
| 2026-10-28 | **V2.0 完工审计**（对照 DESIGN_V2_0.md 六门禁全实测）：冒烟 18/18 绿（全链路/迁移/fail-closed）、gm 三命令管道实测、engine 零 Qt 零 user/server、CLI 回归通关。审计揪出并修复 1 处蓝本偏差：新周目丢历史 playtime（复现 9999→0，修复后 9999 继承）；另记 3 条低危 backlog | ✅ 审计过 |
| 2026-10-28 | **MiniAsura V2.1 通关**（业主授权"背包+装备+词条+GM发装备"）：细案 DESIGN_V2_1.md 冻结 → 照图施工。装备公式全住 scripts/equip.lua（品质倍率/词条区间/紫装保底中位），affixes.txt 数据进包，gear.py 挑选+聚合，engine 只消费聚合结果。战斗接入：暴伤词条、95~105 浮动骰、防御减伤 max(1,怪攻−防×0.6)、吸血回复、经验加成。背包窗（穿/卸/丢/容量20）+ gm give。schema 3 迁移链。门禁 18/18 全实测 + 真窗截图 gui_bag_20261028.png + V2.0 冒烟/CLI 双回归绿 | ✅ 门禁过 |
| 2026-10-28 | §4+§5 独立复核审计：四门禁实测——A 存档落盘 cleared=true ✓ / B 已通关周目识别 ✓ / C 中途续档（手工构造 next=1，Lv.15 重算攻击 60，派生数据不信任存档值）✓ / D GUI 无人值守冒烟截图 gui_audit_20261028.png 全通关 ✓。测试存档已清理 | ✅ 审计过 |
| 2026-10-28 | V2 补全提案审计：登录链等主体采纳 + 三修订（GM 台先 CLI 不做 GUI、schema 2 只带实际字段后续逐期 bump、依赖单向 engine 永不 import Qt 白纸黑字）；修订稿插入 V2.0，其余期顺延 | ✅ 审计过 |
| 2026-10-28 | V2.0 设计冻结：DESIGN_V2_0.md（登录链/伪区服/3 存档槽/窗口路由/schema2 迁移/CLI GM 台），六条出口验收含 v1 存档不丢档与 engine 零 Qt 边界，待业主审后动工 | 🧊 冻结待授权 |
| 2026-10-28 | V2.0 动工并六门禁全过：login/save(注入+迁移)/slots/gm/app 路由 + gui 三窗 + gui.py 降级战斗窗 + engine 改 week/playtime。门禁实录——①offscreen 全链路 18 项含会话恢复 ✓ ②v1 迁移两形态（中断档数值不丢 / cleared→week1）✓ ③fail-closed（空/重名注册、错密码、无会话 gm、wipe 确认）✓ ④GM 三命令管道实测 ✓ ⑤engine.py grep Qt/user/server 零命中 ✓ ⑥CLI dev 模式回归通关 + schema2 落盘 ✓。门禁抓出并修复 3 bug（do_login 空会话 None、pick_server 回错窗、write_raw 不建目录链），测试产物已清理 | ✅ V2.0 毕业 |
| 2026-10-28 | V2.1（背包+装备+词条）用户侧完工 + 中哥驻场监督终审：公式全住 equip.lua（品质倍率/五部位/词条区间/紫装保底中位）、affixes.txt 进包、schema 3、gm give、gui_bag 穿卸丢。终审修复 7 处——F1 真 bug：升级 grant_exp 用基础攻击覆盖装备加成（改 apply_gear 重算）✱ / F2 _pick 候选空裸 IndexError → ValueError 明报 / F3 容量 20 硬编码 → game.ini [bag] / F4 totals 未知词条 key 显式报错（白名单对齐）/ F5 gm give 品质/部位/lv 校验 / F6 背包详情弹窗 → 内嵌标签 / F7 smoke_v21 并入主门禁。24/24 全绿（含 30 种子词条性质批跑、暴击 20%→25% 主门禁、吸血实战、v2→v3 迁移、V2.0 回归 18/18、CLI 通关）。已知偏差：engine.py 221 行超 200 纪律（V2.2 拆 battle 模块时解决） | ✅ V2.1 毕业 |
| 2026-10-28 | **V2.2 通关**（业主授权动工，DESIGN_V2_2.md 冻结 + §8 五条实测修订）：对话系统 dialogue.py（io 抽象播放/跳过/重看，CLI+GUI 通用）+ 任务系统 quests.py（单向状态机，主线6+支线3+隐藏1）+ combat.py 战斗拆分（engine 221→195 行销账）+ rewards.py 奖励发放 + 十图推图 maps.txt（难度倍率缩放）+ 商店 gui_shop（买药/白装回收30%/仓库入口，临时货币=经验点）+ gui_bag 仓库双模式 + gui_quests 重看防剧透 + schema 4（quest_flags/kills/maps_cleared/potions/storage，v1→v4 跨三级迁移实测）+ gm quest/map/potion 三命令。平衡探针立功：纯普攻第9图必死 → [growth] hp_per_level=6 + 任务奖励空部位自动穿戴。门禁抓出 2 真 bug：hidden 任务从未激活（监听者没上岗）+ 死亡不发 lose 事件（死亡改落盘，跨局败北计数可累积）。smoke_v22 共 27 项全绿（十任务全通/跳过不推进/隐藏任务真触发/商店闭环/任务窗重看/GM fail-closed/行数纪律/V2.0+V2.1 回归）。测试产物已清理 | ✅ V2.2 毕业 |
| 2026-10-29 | 中哥驻场审计修复 4 处：用药提示文案对齐行为 / 注册用户名拒绝路径非法字符（防目录崩溃与路径逃逸）/ gm 数字参数 _int() fail-closed / 隐藏任务未完成拒绝重看对话（防剧透绕过）；smoke_v22 27 项回归全绿 | ✅ 审计过 |
| 2026-10-29 | 逃跑语义修复：mon 补传 key（此前 boss 战也能逃跑）+ 逃跑不再推进（此前与 win 共用 fi+=1，一路逃跑也能通关），只落盘到本场开打前位置 | ✅ 修复 |
| 2026-10-29 | **V2.3 毕业**：金币经济（临时经验货币退役，金币掉落/消费/回收全链）+ 掉落引擎 loot.py（概率/品质/满包转仓库/难度倍率 DIFF_MULT）+ 副本三难度（普通/精英/噩梦，新周目重问、续档不重问）+ schema 5 + gm gold/difficulty | ✅ V2.3 毕业 |
| 2026-10-29 | **V2.4 毕业**：装备强化 enhance.py（+0~+10，主属性 atk/hp/def ×(1+0.05×enh)，闪避与词条不乘）+ 保底符（失败保级）+ 死亡惩罚（扣当前经验 10% 向下取整，不掉级，<10 不扣）+ 铁匠窗 gui_enhance + schema 6（gold/difficulty/protect/装备 enh，v1→v6 全链迁移实测）+ gm protect；门禁门 smoke_v23/v24 上线，开场清场加固保证可重复执行 | ✅ V2.4 毕业 |
| 2026-10-29 | **V2.5 毕业**（DESIGN_V2_5.md 冻结，四项业主决议：双轨获取/本期不做Lv.1开局/通关后解锁爬塔/validate入门禁）：无底洞爬塔 tower.py（层数即怪物等级，通关一次后解锁，死亡/撤离清零、最高层保留，续爬+EOF中断保护）+ 无级别武器「如意金箍棒·无级」（ATK=10+等级×6，scaling:"owner" 每次 apply_gear 重算，固定三词条满值，吃强化倍率；双轨：隐藏任务 h2「真假美猴王」通关必得 + boss 1% 掉率，共用同一发放口且幂等）+ 数值平衡（30 级封顶、经验曲线 100×级数^1.65 住 battle.lua，CLI 全通自然等级 Lv.32→Lv.17 显式重定基线）+ validate.py 七项数据校验（掉落/任务奖励/曲线单调/商店/词条限制/v1→v7 迁移/金币对账）+ gui_tower 爬塔窗 + schema 7（tower_best/tower_layer）+ gm tower/staff；smoke_v25 七门禁全绿 + v22/v23/v24 全链回归绿（含 v25 幂等双跑）。engine.py 仍 220 行顶格达标（结算块抽 finish_summary 腾位） | ✅ V2.5 毕业 |
| 2026-10-29 | **V2.6 毕业**（DESIGN_V2_6.md 冻结）：**Lv.1 开局**（蓝图 §1 终落地）+ 经验曲线恢复蓝图原值 60×lv^1.65（V2.5 的 100 基数是 Lv.14 开局临时对齐，本期被原值取代）+ 十图数值重钉（怪物 exp 800/2000/4000/55000 按通关 ~Lv.25 校准；boss 加强 220/20→600/40；图10 倍率 1.6→1.0）+ 两个实测倒逼的行为决策：**升级回满血**（否则十图磨血 226 点必死于终幕）与**任务奖励品质更高自动换装**（否则武器堵在首件白装，终幕战力不足）+ 任务奖励装备等级下调（15~18→2/5/8/12 随 Lv.1 进度）+ 爬塔经验改曲线 30×N^1.65（Lv.25 满配爬 30 层恰好顶到 30 级封顶，闭环验证）。基线显式重定：CLI 全通等级 17→25、金币 918→798（boss scale 1.0 所致），smoke_v21 升级判据改 grant 5000（语义不变），蓝图曲线表 16715 与公式 16419 不符处以公式为权威。smoke_v26 六门禁全绿 + v21→v25 全链回归绿 | ✅ V2.6 毕业 |
| 2026-10-29 | **V2.7 毕业**（PATCH-V27 补丁稿转正冻结为 DESIGN_V27.md，D1–D5 默认值全部采纳）：十技能补齐（主动 6 + 被动 3，解锁档 3/6/10/14/18/22/26/29/30 对齐蓝图表；技能菜单灰字显示 Lv.解锁/冷却中/MP 不足）+ 战斗 CD 表（棒扫六合 3 回合 / 如意神通 5，出战斗清零）+ 命中/闪避（蓝图 §1.3 公式：95%+命中−闪避下限 60%，MISS 不触发暴击/吸血/连击后续段，筋斗云 buff 仅下回合加法叠加）+ 武器谱特效（紫档武器取名挂 effect：定水枪 ×1.15 打水族 / 降魔杖 ×1.12 打妖 / 白骨剑暴伤 +15 / 缠丝爪吸血 +3% 与词条合计上限 10%）+ battle.lua damage/incoming 加可选参数（缺省=旧行为）+ monsters.txt 加 tribe 列 + validate 加 V27-01/02 九项。实现期修 3 真 bug：被动暴击重复计数词条、闪避 buff 单位错位（0.30 小数 vs 30 百分数）、连击 MISS 用 continue 未中断。基线显式重定：smoke_v21 crit 25→33（火眼金睛 +8）、smoke_v25 面板 ×1.10、CLI 全通输入 400→500（MISS 拉长战斗）。skills.py 141 行 / validate.py 150 行 / combat.py 129 行 / engine.py 220 行全部顶格达标；smoke_v27 六门禁全绿 + v21→v26 全链回归绿（v27 幂等双跑） | ✅ V2.7 毕业 |
| 2026-10-29 | **V2.8 毕业**（DESIGN_V2_8.md 施工版冻结，Kit 两处裁决：一窗四页 / 同档替换）：图鉴·成就·统计一窗四页（武器谱 10 把 ●/○+计数、怪物图鉴 7 行 ×击杀数、成就 6 项、统计 7 项含时长格式化）+ progress.py（成就判定纯函数 evaluate / 图鉴并集 merge_codex / 统计口径唯一汇总处）+ schema 8（achievements/codex_weapons/total_damage，v7→v8 旧值一字不动）+ total_damage 伤害累计（combat 同行追加、跨周目 dmg_carry 继承）+ tribe 实怪补齐（虾兵/蟹将=水族上图4、火妖=火抗上图7，数值同档替换使 V2.6 全通基线零位移）+ validate 加 V28-01/02/03 成十二项（**上限显式修订 150→160**）。成就永不回归：save.write 与 tower.persist 均取「旧档 ∪ 本次」并集。smoke_v28 六门禁全绿 + v21→v27 全链回归绿 | ✅ V2.8 毕业 |
| 2026-10-29 | **V2.9-A 毕业**（DESIGN_V2_9_A.md 冻结，schema 8→9，只做头脑风暴 §8 的 A 一行）：战斗结算战报（`combat.battle` 新增 report 字典 → rounds/dealt/taken/crits/misses，win/dead 后打印一行战报，逃跑不打印）+ BOSS 阈值变招（`[boss_phase]` 住 game.ini：50% 变身 atk×1.2 / 30% 狂暴再×1.2 且玩家伤害×1.2 / 变身后每 2 回合骨刺雨 max(5, max_hp×5%) 不吃防御；原稿"狂暴防御−20%"在现行无怪物防御项的公式里无效果，**诚实翻译**为"玩家对其伤害×1.2"）+ 精英/稀有怪（种子由 `(week, 地图, fi)` md5 稳定哈希，r<20 精英 hp×1.5/atk×1.2 + 三词缀甲硬/灼烧/疾风，20≤r<25 稀有 hp×0.5/atk×0.5，逃跑重打结果不变防刷；经验金币不变以保全通基线）+ 掉落保底（新字段 `staff_pity`，boss staff 掷失败 +1，pity≥49 第 50 次必中并清零，已持有则不变）+ 新模块 encounter.py 154 行（上限 160）+ validate 增 V29-01/02/03 成十五项。数值取舍：精英 atk 取 ×1.2 而非原稿 ×1.5（×1.5 会让 CLI 全通在双战斗图送命）。smoke_v29a 19 项全绿，v20→v28 全链回归绿 | ✅ V2.9-A 毕业 |
| 2026-10-29 | **门禁自证修复 + GUI 环境补齐**：审计发现 smoke_v29a 保底两项误判——测试每轮新传 `storage=[]`，而 boss 池 `weapon:2:100` 必掉紫装，49 轮填满 20 格背包后 staff 流入该临时列表，断言只查 `inventory` 故查无。修法：`store` 提到循环外共用（复刻引擎持久仓库），断言升级为 `gear.has_staff(pl, store)`（背包+仓库+已穿戴，比原口径更严）；**反证验证**——临时把保底判定 `>=49` 改 `>=999` 关掉，两条断言立刻变红，证明未削弱测试。同时给沙箱默认 Python 补齐 PySide6 6.12.0（此前 `smoke_v28 回归 ✗` 纯属缺 Qt 而非业务回归），装后 `pip check` 无损坏依赖、`QApplication` 可创建、offscreen 启动 app.py 无异常。整链 `v20→…→v29a` 19/19 全绿（3m55s）。提交 8eda792 | ✅ 修复过 |
| 2026-10-29 | **V2.9-B 毕业**（DESIGN_V2_9_B.md 冻结，B1 先 / B2 后，分批复验）：B1 爬塔战报接入（tower 补传 `rep`，win/dead 打印战报、escaped 不打印；实施后自审发现 escaped 曾被条件遗漏，已按 fail-closed 修正）。B2 稀有怪三回合逃跑：返回契约扩为 `win/dead/escaped/fled`，稀有标记改为随 `mon` 传递，`[rare_flee] flee_rounds=3` 入 game.ini；fled 推进不回大厅、算本场已处理、不发奖励/不记击杀/不发 win/lose；dead 优先；rounds≥2 有预警。tower 本期不启用稀有，若意外 fled 则 WARN 并按 escaped fail-closed。schema 9 不变。行数显式修订：engine 220→222、encounter 160→170、validate 160→165，combat 130/tower 100 不变；validate 增至十六项（V30-01）。smoke_v29b 七门禁 7/7 + v20→v29a 全链回归全绿（4m28s），week0 基线 Lv.25/金币798/maps10 不变 | ✅ V2.9-B 毕业 |
| 2026-10-30 | **V2.9-C 毕业**（DESIGN_V2_9_C.md 冻结，D1-D8）：GUI 战报"显眼化"——`print_report` 改为单点分派的富通道（`io.report(rep, line)` 有则调、无则回退 `say`，**CLI 输出逐字节不变**），日志上方新增常驻 `ReportCard`（gui_report.py 45 行）：第一行「最近一场战报 · X 回合 · 造成/承受」，第二行「暴击 · MISS ｜ 本局累计：N 场 / 造成 / 承受」；主线 `begin()` 清零、爬塔跨层累计，合计只活窗口内存**不写档不升 schema**。审计实测：全通日志 272 行 / 12 条战报，白骨夫人战报落在第 275 行且其后还有结局统计——这是"埋没"的直接证据。战斗窗与爬塔窗共用同一组件；样式只用加粗+边框不写死颜色（防深色系统主题不可读）；escaped/fled 不打印战报，故标题写「最近一场」而非「本次」。encounter 保持 170 行不变，gui.py 197→207、gui_tower 165→174。smoke_v29c 八门禁 10/10 + validate 十六项 + v20→v29b 全链回归全绿 | ✅ V2.9-C 毕业 |
| 2026-10-30 | **V2.9-D1 毕业**（DESIGN_V2_9_D1.md 冻结，R1-R10，分 D1a 数据层 / D1b 表现层两批）：**schema 9→10**。① 变体击杀独立计数 `elite_kills`/`rare_kills`——审计发现 `tracker.kills` 只按怪物 key 计数、精英稀有与普通同 key，故另开计数而**不污染 kills**（图鉴与总击杀口径不变），主线 win 时按 `fight["elite"]`/`fight["rare"]` 递增，爬塔不参与；② 新增成就 `elite_hunter`(精英 10)/`rare_hunter`(稀有 3)，条件类型扩到 8 种；③ 称号表 `assets/titles.txt` 8 条与成就 1:1，纯荣誉不加属性，`title` 字段落盘，图鉴窗新增第 5 页「称号」（**唯一写档页**，只写 title 一个键，未解锁不进下拉、重开预选当前佩戴），大厅顶部显示当前称号；④ 幻影榜：单场最高伤害 / 单场最少回合 / 爬塔最高层，只在 win 且更优时刷新（低伤害高回合不覆盖），并入统计页不新开页。v9→v10 只补默认值实测旧值一字未动。行数显式修订：engine 222→225、validate 165→170、progress 87→108、save 118→128、gui_codex 85→120、gui_hub 53→59；tower 保持 100。validate 增至十七项（V31-01 称号表合法）。smoke_v29d1 八门禁 9/9 + v20→v29c 全链回归全绿 | ✅ V2.9-D1 毕业 |
| 2026-10-30 | **V2.9-D2 毕业**（DESIGN_V2_9_D2.md 冻结，Q1-Q10）：**schema 10→11**。日常 / 周常 / 签到三块落地。① **快照差值口径**（Q1）：`base` 记滚动时刻的累计快照（总击杀 / 总伤害 / 爬塔最高层），进度 = 当前 − base，负数截断为 0、上限截到 need —— 因此"跨日那一刻已有 500 杀"不会把今天刷成已完成；`lose:` 前缀键不计入击杀（与图鉴口径一致）；② **单点滚动**（Q2/§6）：`daily.touch` 只挂在 `save.write_raw` 一处，所有写档路径自动收口，只重置 `date`/`base`/`claimed`，**不发奖励、不动其它字段**；读态走 `daily.view`（日期对不上按"今天刚开始"算、**不写档**），未写档也能正确显示 0 进度；③ **日期源可替换**（Q5）：`today()` / `this_week()`（isocalendar 周键）各自单函数，门禁直接替换函数注入 D1/D2/跨周，不碰系统时钟；④ **签到**：金币 `30+(N-1)×20`、第 7 天额外 +1 保底符、同日拒绝、断签只把 streak 重置为 1（`total` 累计不清零）；⑤ GUI `gui_daily.py` 三页（日常 / 周常 / 签到），进度与按钮状态**全部来自 `daily.status`**，界面不自算增量，领取即写档且只改 `claimed`/`gold`/`protect`；大厅加「日常 / 签到」入口。`daily` 不 import `save`/`configparser`（无循环依赖，滚动不读配置）。行数：daily 97 / gui_daily 89 / save 128→134 / validate 170→180 / app 137 / gui_hub 59→62。validate 增至十八项（V32-01 日常配置合法）。**基线随动修正**：`smoke_v29d1` 两处写死的 `schema == 10` 改引 `save.SCHEMA` 与迁移默认值断言（含 D2 三字段），避免以后每升一版期数都要再改测试。smoke_v29d2 九项全绿 + v20→v29d1 全链回归全绿 | ✅ V2.9-D2 毕业 |

## 环境（搬迁后需注意）
| 项 | 值 |
|---|---|
| 项目根 | `D:/西游记文字版` |
| Python（CLI + GUI 通用） | `python`（系统 PATH 中，3.13.14）—— **2026-10-29 起已带 PySide6 6.12.0，GUI 与全套门禁可直接用它跑**（此前它无 Qt，只能跑纯逻辑） |
| Python（备用 GUI 解释器） | `D:/Software/Python313/python.exe`（同 3.13.14 + PySide6 6.12.0；两套 site-packages 互相独立，装包不共享） |
| PySide6 | **6.12.0 / Qt 6.12.0 —— 测试硬依赖，非可选**，见下节 |
| Lua 解释器 | `..\tools\lua-5.1.5\lua.exe`（脚本内部已用相对路径，无需 PATH） |
| 用户 PATH 旧条目 | `F:/WeGameApps/斗战神/learn-lab/tools/lua-5.1.5` 已失效 → 需改为 `D:/西游记文字版/tools/lua-5.1.5` 才能在终端直接敲 `lua` |

> **Agent/沙箱里跑门禁的坑（2026-10-30 实测）**：自动化环境里的 `python` 会被解析到 `C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.x/python`（WorkBuddy 自带解释器），**它没有 PySide6**，直接跑 `smoke_v29d2` 会在门禁 6 抛 `ModuleNotFoundError: No module named 'PySide6'`，而前 5 项逻辑门禁全绿——看起来像"业务只坏一半"。这不是代码问题。跑全套门禁用显式解释器：`D:/Software/Python313/python.exe -u tests/smoke_v29d2.py`。

### PySide6 是测试硬依赖（不是"想看图才装"）
门禁不是纯逻辑测试，Qt 缺了整条回归链会红：

- `smoke_v22` 起 GUI 用例直接 `from PySide6.QtWidgets import QApplication`，开真窗口断言控件
- `smoke_v28` 末尾「字体引导」门禁用 offscreen 平台加载系统中文字体（保证截图取证可读）
- `smoke_v29a` 串行回归 `v20→…→v29a`；`smoke_v29b` 再串至 `v29a`，`smoke_v29c` 再串至 `v29b`，`smoke_v29d1` 再串至 `v29c`，`smoke_v29d2` 再串至 `v29d1`（GUI 战报卡/称号/日常窗门禁要开真窗口），任一环 import 失败即全链报红

**缺件时的症状很坑**：链跑到 v28 末尾才抛 `ModuleNotFoundError`，v29a 汇总只显示一行
「`smoke_v28 回归 ✗`」，看起来像业务回归，实际是环境缺件。先自检：

```
python -c "import PySide6; print(PySide6.__version__)"
```

装法：

```
python -m pip install PySide6
```

> 受限环境若报 `SAFE_DELETE_BULK_GUARD`：那是 pip 覆盖旧文件时的 `unlink` 撞上了批量删除保护，
> wheel 往往已完整落地——先 `python -m pip check` 复查导入是否正常；确有问题就装进独立 venv
> 或改用 `--target` 目录，避开对既有文件的覆盖。

**跑测注意**：`smoke_v29d2` 全套回归链约 4 分钟，超出默认命令超时会被 SIGTERM 截断，且管道缓冲会吞掉全部输出
（表现为"无任何输出"）。务必加 `-u` 关缓冲，必要时后台运行：

```
python -u tests/smoke_v29d2.py
```

启动：
```
cd /d D:/西游记文字版/miniasura
python app.py                 :: GUI 全链路
python engine.py              :: CLI 文字版
python -u tests/smoke_v29d2.py :: 全套门禁（v20→…→v29d1 回归链 + V2.9-D2 日常/周常/签到八门禁，约 4 分钟）
python validate.py            :: 数据校验器（十八项：七项数据表 + V27 技能/特效 + V28 成就/新怪/地图 + V29 阈值/精英/保底 + V30 稀有逃跑 + V31 称号表 + V32 日常配置，上限 180）
python tower.py               :: V2.5 无底洞爬塔 CLI（通关一次后解锁）
```
