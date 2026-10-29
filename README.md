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
└── miniasura/       ← 按斗战神图纸复刻的文字版游戏（V2.6）
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

## 环境（搬迁后需注意）
| 项 | 值 |
|---|---|
| 项目根 | `D:/西游记文字版` |
| Python（纯逻辑/CLI） | `python`（系统 PATH 中，3.13.x） |
| Python（GUI 需 PySide6） | `D:/Software/Python313/python.exe`（沙箱默认 Python 无 Qt） |
| Lua 解释器 | `..\tools\lua-5.1.5\lua.exe`（脚本内部已用相对路径，无需 PATH） |
| 用户 PATH 旧条目 | `F:/WeGameApps/斗战神/learn-lab/tools/lua-5.1.5` 已失效 → 需改为 `D:/西游记文字版/tools/lua-5.1.5` 才能在终端直接敲 `lua` |

启动：
```
cd /d D:/西游记文字版/miniasura
D:/Software/Python313/python.exe app.py     :: GUI 全链路
python engine.py                            :: CLI 文字版
D:/Software/Python313/python.exe tests\smoke_v26.py   :: 全套门禁（v21→…→v26 回归链，可重复执行）
D:/Software/Python313/python.exe validate.py          :: V2.5 数据校验器（七项数据表编译检查）
python tower.py                                       :: V2.5 无底洞爬塔 CLI（通关一次后解锁）
```
