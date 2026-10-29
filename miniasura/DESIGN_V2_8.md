# MiniAsura V2.8 设计（施工版）

> 地位：**施工版**。授权来源：业主 2026-10-29 12:18 原话“二选一方案待你拍板，现在授权开始做”
> ——二选一由 Kit 拍板（见 §1），实现即刻开工。git 照老规矩仍由业主亲手：
> 本补丁包只放 workspace，不推库；业主一句话可推翻 §1 的选择，推翻零成本。
> 蓝本依据：DESIGN_V2.md §6（成就 P2 / 统计 P2）、DESIGN_V2_SUPPLEMENT §1.6（图鉴窗）、
> PATCH-V27 §1 D4 分期（V2.8 = 图鉴 / 成就 / 统计）+ V2.7 收尾提醒（水族 / 火抗实怪）。

## 0. 现状核对（线上 HEAD d47dc4e 实测）

| 项 | 现状 | V2.8 落点 |
|---|---|---|
| 存档 | schema 7；已有 playtime / kills{}（怪→数，lose: 怪→败北数）/ maps_cleared / tower_best / gold / week | schema 升 8；新增 achievements[] / codex_weapons[] / total_damage |
| 总伤害 | 无任何累计 | combat 命中段同行追加（0 新增行），tower 同理 |
| 图鉴/成就/统计 | 无模块，大厅无入口 | 新模块 progress.py + 新窗 gui_codex.py，大厅 1 个新按钮 |
| 怪物表 | 仅 4 行：xiaoyao1/2/3（tribe=无）+ boss（妖）；maps.txt 图4 用 xiaoyao2/3、图7 用 xiaoyao3×2 | +3 行实怪（见 §4），maps 图4/图7 换怪 |
| 行数纪律 | engine 220 / combat 130 / tower 100 / validate 150（均顶格） | engine/combat/tower 0 新增行（同行追加）；validate 显式修订 150→160（见 §6） |

## 1. 二选一裁决（Kit 按授权拍板）

### 选一：图鉴 / 成就 / 统计的窗口落法

- **A. 合一窗（拍板选 A）**：大厅 1 个新按钮“图鉴 / 成就 / 统计”，一窗四页
  （武器谱 / 怪物图鉴 / 成就 / 统计），四页读同一存档快照。
- B. 分立两窗：大厅 2 个新按钮，“图鉴”（武器谱 + 怪物）与“统计”（统计 + 成就）。

选 A 的理由：补全提案 §1.6 本来就说“结算页扩展并入图鉴窗”；大厅已有 7 个按钮，
再加 2 个更挤；四页同源，统计口径与图鉴点亮不可能漂移。

### 选二：tribe 实怪的数值定法

- **A. 同档替换（拍板选 A）**：新怪基础数值 = 被替怪同档（虾兵 = xiaoyao2 档，
  蟹将 / 火妖 = xiaoyao3 档），掉落池照抄同档怪。
- B. 独立重定：按东海龙宫 / 八卦炉主题给新怪独立数值，重跑 V2.6 全通基线。

选 A 的理由：地图倍率（图4 ×1.3、图7 ×1.6）一乘后与原来完全一致，
V2.6 的“通关 ~Lv.25 / 金币 798”校准零位移；B 的收益只是数字不同，
代价是全通基线重定，V2.8 不值得。

## 2. 成就系统（蓝图 §6 P2：纯 flag，不给奖励）

条件住 `assets/achievements.txt`（id|名|描述|条件|阈值），判断只 progress.evaluate 一处：

| id | 名 | 条件 |
|---|---|---|
| first_blood | 初露锋芒 | 总击杀 ≥1 |
| clear_all | 西行功成 | maps_cleared ≥10，或 week ≥1（周目重开后 maps_cleared 归零，week 兜底） |
| max_level | 齐天大圣 | level ≥30 |
| full_arsenal | 武器谱集齐 | codex_weapons 含全部 10 把 |
| tower30 | 无底洞三十层 | tower_best ≥30 |
| enhance10 | 登峰造极 | 任一装备 enh ≥10（扫描背包 + 仓库 + 已穿戴） |

- **永不回归**：save.write 每次用“旧档已解锁 ∪ 本次算出”取并集写回；
  强化 +10 的装备被回收后成就仍保留（防回归是成就系统的底线）。
- 成就判断是纯函数（progress.evaluate），GUI 与存档共用同一口径，不许两处各写一份。

## 3. 图鉴窗与统计页（只读存档，不写盘）

- **武器谱**：10 把全列，`● 已获得 / ○ 未获得` + 计数 x/10；获得 = 曾经拥有过
  （codex_weapons，卖出 / 回收不灭灯）。
- **怪物图鉴**：monsters.txt 全部 7 行，`● 名 ×击杀数 / ○ 未遭遇`；击杀数读 kills{}，
  lose: 前缀不算击杀。
- **统计页**：总击杀（kills 非 lose: 求和）/ 总伤害（total_damage）/ 游玩时长
  （playtime 秒 → X小时Y分，不足 1 小时显示 X分钟）/ 通关周目 / 爬塔最高 / 当前等级 / 金币。
- **游玩时长**：沿用现有机制（engine persist 写 base_playtime + 本局耗时），V2.8 不改计时；
  GUI 战斗走 engine 同一路，时长自然累计。CLI 与 GUI 共用同一 playtime 字段。

## 4. tribe 实怪（水族 / 火抗）

实际地图与蓝图 §3 不一样（实装是花果山 / 水帘洞 / 斜月三星洞 / 东海龙宫 / 南天门 /
蟠桃园 / 八卦炉 / 五行山 / 流沙河 / 白骨洞，没有火焰山），所以火抗怪不放火焰山，
放八卦炉（炼丹炉，火地，主题贴合）：

| 新怪 | tribe | 基础数值（= 被替怪同档） | 掉落池（照抄同档） | 上图 |
|---|---|---|---|---|
| 虾兵 xiabing | 水族 | 55/11/2000/30（= xiaoyao2） | [loot.xiaoyao2] | 图4 东海龙宫 |
| 蟹将 xiejian | 水族 | 70/14/4000/40（= xiaoyao3） | [loot.xiaoyao3] | 图4 东海龙宫 |
| 火妖 huoyao | 火抗 | 70/14/4000/40（= xiaoyao3） | [loot.xiaoyao3] | 图7 八卦炉 |

- maps.txt：图4 `xiaoyao2,xiaoyao3` → `xiabing,xiejian`；图7 `xiaoyao3,xiaoyao3` → `huoyao,huoyao`。
- 倍率后强度：图4 虾兵 72/14、蟹将 91/18；图7 火妖 112/22——与被替怪逐项一致，V2.6 基线不动。
- 特效验证闭环：定水枪 ×1.15 打虾兵 / 蟹将、芭蕉扇 ×1.18 打火妖、降魔杖 ×1.12 打 boss（妖），
  三档 vs_tribe 都有实怪可打（V2.7 的遗留缺口本期补上）。

## 5. 存档 schema 8（迁移只补默认值，不改已有数值）

| 字段 | 含义 | 迁移 |
|---|---|---|
| achievements[] | 已解锁成就 id | 旧档补 []，下次 save.write 即按现状算出并集 |
| codex_weapons[] | 曾经拥有过的武器名 | 旧档补 []，下次 save.write 用旧档 ∪ 当前背包 / 仓库 / 已穿戴合并 |
| total_damage | 累计总伤害 | 旧档补 0；此后 combat / tower 同行追加 |

- save.write 读旧档（只读本文件，不触发迁移写）取 codex / achievements 做并集；
  tower persist（write_raw 路）不经过 save.write，所以 tower.persist 同行追加
  achievements 并集计算（见补丁 diff）。
- 周目重开：codex / achievements / total_damage 跨周目继承（与金币 / 保底符 / tower_best 同例）；
  total_damage 的周目继承走 dmg_carry（与 gold_carry 同行追加，0 新增行）。

## 6. 行数纪律（显式记录，不静默放宽）

| 文件 | 上限 | V2.8 处理 |
|---|---|---|
| engine.py | 220 | 0 新增行：全部同行分号追加（dmg_carry 初始化 / 提取 / 玩家字典键） |
| combat.py | 130 | 0 新增行：`m_hp -= dmg` 同行追加 total_damage 累计 |
| tower.py | 100 | 0 新增行：load_player 字典行追加 total_damage 键；persist 元组行追加键；achievements 并集同行追加 |
| validate.py | **150→160（显式修订）** | 新增 V28-01/02/03 三项校验约 10 行，塞不进顶格；修订记录在此、README、smoke 门禁三处一致 |
| progress.py（新） | 150 | 新模块，实测行数见补丁说明 |
| gui_codex.py（新） | 不设上限（GUI 窗体与 gui_tower 同例不设限） | — |

## 7. 改动清单

| 文件 | 改动 |
|---|---|
| progress.py（新） | 成就表读取 + evaluate 纯函数 + 统计口径 + 图鉴行 + playtime 格式化 |
| gui_codex.py（新） | 四页图鉴窗（QTabWidget + 只读文本页，TowerWindow 同款结构） |
| assets/achievements.txt（新） | 6 行成就表 |
| save.py | SCHEMA 8 + 迁移 3 字段 + write() 并集合并 + 写 3 新字段 |
| engine.py | 0 新增行：dmg_carry + 玩家字典 total_damage 键 |
| combat.py | 0 新增行：伤害累计同行追加 |
| tower.py | 0 新增行：total_damage 键 + achievements 并集 |
| gui_hub.py | go_codex 参数 + “图鉴 / 成就 / 统计”按钮 |
| app.py | import + codexw 装配 + to_codex() |
| game.ini | +3 [monster.*] +3 [loot.*] |
| maps.txt | 图4 / 图7 换怪 |
| monsters.txt | +3 行（tribe 列） |
| validate.py | V28-01 成就条件合法 / V28-02 新怪 ini+loot 齐全 / V28-03 武器谱 10 把与 WEAPON_NAMES 一致 |
| tests/smoke_v28.py（新） | 六门禁（见 §8） |
| README.md | V2.8 行 + smoke_v28 启动命令 + validate 上限修订记录 |

## 8. 出口验收（smoke_v28 六门禁）

1. **成就**：6 项条件各有断言；强化 +10 后回收装备，成就仍保留（并集不回归）。
2. **图鉴**：武器谱 10/10 点亮逻辑（codex 含卖出过的武器仍亮）；怪物图鉴击杀数与 kills{} 一致，lose: 不计。
3. **统计**：总击杀 / 总伤害 / playtime 格式化（3661 秒 → “1小时1分”）口径断言。
4. **tribe 实怪**：build_maps 图4 出虾兵 / 蟹将、图7 出火妖；定水枪打虾兵 ×1.15、芭蕉扇打火妖 ×1.18。
5. **迁移**：v7 旧档升 schema 8，旧数值（等级 / 金币 / 击杀 / 爬塔）一字不动，新字段默认值齐全。
6. **回归**：smoke_v27 全绿；validate 十二项全绿（9 + V28-01/02/03）；行数纪律（§6 表）；
   CLI 全通基线不变（Lv.25 / 金币 798，V2.6 校准零位移）。

## 9. HARD STOP（施工版状态）

本文档是施工版（业主授权 + Kit 二选一裁决）。实现按补丁包落盘；
IMPLEMENTATION → COMMIT_READINESS_AUDIT → COMMIT_EXECUTION 三段隔离照旧，
推库仍由业主亲手。§1 的两处裁决业主一句话可推翻，推翻后按新裁决改补丁，不动已推库内容。
