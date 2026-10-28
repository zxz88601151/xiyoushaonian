# MiniAsura V2.4 设计冻结 —— 装备强化 + 死亡惩罚

> 承接 DESIGN_V2.md §6/§8（V2.4 期）+ DESIGN_V2_3.md。
> 蓝图只给了两句话，本期把缺的数值全部钉死（下面标“本期定”的都是新定数，
> 不是蓝图原话，别当成蓝图引用）。

## 0. 范围一句话

铁匠从占位变成真强化：装备 +1~+10，花金币，+7 起失败降级，保底符可保级；
死了不再满血白嫖：扣当前经验 10%（不掉级），再满血回城。

## 1. 强化（enhance.py 新模块，核心与 UI 分离）

| 项 | 规则 |
|---|---|
| 等级 | 装备字段 `enh`，0~+10；旧装备缺字段一律按 0 计（见 §3 迁移） |
| 加成 | 只加主属性 atk/hp/def，不加闪避、不加词条：主属性 × (1 + 0.05 × enh)，
  在 gear.totals() 聚合时算，engine.apply_gear 自动生效 |
| 显示 | item_line 末尾加 ` +N`（enh>0 时），背包/商店/掉落一行话都认 |
| 费用（本期定） | 升一级费用 = 20 × (enh+1) + 装备 Lv × 2 金币。
  例：Lv14 装备 +0→+1 = 48 金，+9→+10 = 228 金，+0 一路到 +10 合计 1380 金 |
| 成功率（本期定） | +1~+6 100%，+7 80%，+8 70%，+9 60%，+10 50%。
  蓝图只说了“+7 起失败降级”，没给成功率，上面这张表是本期定的 |
| 失败（蓝图） | 金币照扣；enh ≥7 时失败降 1 级（+7 失败 → +6，绝不归零）；
  enh ≤6 不会失败，所以不存在降级 |
| 保底符（蓝图道具，本期定落地方式） | 商店特价商品，100 金币一张（见 §2 为什么不在 shop.txt 里）；
  强化时勾选“使用保底符”且持有 ≥1 张：失败时消耗 1 张，等级不动；
  成功时不消耗。保底符只防降级，不提高成功率 |
| 掷骰 | 核心函数 enhance() 接受 rng 参数（测试可注入固定随机），
  GUI 与 GM 都调同一核心，不各写一套概率 |

## 2. 保底符为什么不在 shop.txt 里

shop.txt 的来源在 assets/，但 gui_shop.py 读的是 assets.mpak（二进制生成物），
改 shop.txt 源码不重跑 build.py 就不生效，而 mpak 二进制没法走文本补丁推送。
所以 V2.4 的保底符不在 shop.txt 里，gui_shop.py 里加一个专用按钮
“买保底符（100 金币）”，buy("protect") 走专用分支，不走药水分支。
将来在 Windows 上重跑 build.py 生成新 mpak 时，再把 protect 行补进 shop.txt，
并把 buy() 统一回数据驱动——那一步留给 mpak 重建时做，不在本期硬塞二进制。

## 3. 存档 schema 6（本期迁移，蓝图 V2.4 要求的“存档迁移”就是这一条）

- SCHEMA 5 → 6。
- _migrate：inventory / equipment / storage 里的每件装备补 `enh=0`（缺字段才补，
  已有 enh 不动）；顶层补 `protect=0`（保底符张数）；gold/difficulty 沿用 v5。
- save.write：写出 protect（从 player.get("protect", 0)），engine 的 persist
  不再把买好的保底符清零（见 §4 的 protect 携带）。
- 注意：smoke_v23 的迁移用例原来期望 schema 5，本期同步改成期望 6，
  并加 enh/protect 迁移断言；不是偷改测试，是 schema 本身升了。

## 4. 死亡惩罚（蓝图原话，落地方案）

- 蓝图：掉 10% 当前经验（不掉级），回城复活。
- 落地：engine 死亡分支，满血回城之前先扣
  `loss = int(player["exp"] * 0.10)`（向下取整；当前经验 <10 时 loss=0，不倒扣），
  player["exp"] -= loss，随后 persist 落盘（惩罚进存档，不是口头说说）。
- 提示文案写清扣了多少与“不掉级”，别让玩家以为掉级了。
- 败北任务事件（lose）与跨局败北计数不受影响，仍按 V2.2 规则走。
- 死亡惩罚计算住在 rewards.py 的 apply_death_penalty()（38 行的小模块，
  无行数门禁），engine 只调一行，不让 engine 再长——engine 仍 ≤220 行
  （把通关结算的击杀行合并成一行腾出位置，见 §5）。

## 5. 改动清单

| 文件 | 改动 |
|---|---|
| enhance.py（新） | cost()、success_rate()、enhance() 核心；rng 可注入 |
| gear.py | generate() 新装备带 enh=0；totals() 主属性乘 (1+0.05×enh)，
  闪避不乘；item_line() 加 ` +N` |
| rewards.py | 新增 apply_death_penalty(player, io) → loss |
| engine.py | 死亡分支调 apply_death_penalty；protect 金币式携带（新周目继承，
  与 gold 同理）；通关结算击杀行合并一行，engine 仍 ≤220 |
| save.py | SCHEMA 6；迁移补 enh/protect；write 写 protect |
| gui_enhance.py（新） | 铁匠窗：背包+已穿戴列表，选装、费用、成功率、保底符勾选、
  强化按钮、结果提示；只调 enhance 核心，不自己算概率 |
| gui_hub.py / app.py | 大厅加“铁匠（强化）”按钮，路由到铁匠窗 |
| gui_shop.py | 加保底符专用按钮（100 金币），buy("protect") 专用分支；
  货币仍是金币，药水逻辑不动 |
| gm.py | 新增 `protect <n>`（设当前档保底符张数），数字用 _int fail-closed |
| tests/smoke_v23.py | 迁移期望 schema 5→6，加 enh/protect 断言 |
| tests/smoke_v24.py（新） | V2.4 门禁：见 §6 |

## 6. 出口验收（六门禁）

1. **强化数值**：totals() 的 +N 加成实测对表（atk/hp/def ×(1+0.05N)，闪避不动）；
   item_line 显示 +N
2. **强化流程**：费用对表、金币不足拒强、+6 以下必成、+7 以上按表掷骰、
   失败降 1 级且金币照扣、保底符失败保级且只在失败时消耗
3. **死亡惩罚**：exp 50 死一次变 45、exp 9 死一次不变、等级不降、惩罚进存档
4. **存档迁移**：v5 档升 v6 后，旧装备 enh=0、protect=0、原字段不丢；
   新装备 generate 自带 enh=0
5. **UI 与 GM**：铁匠窗与商店保底符在 Windows offscreen 下可点；
   gm protect 设数与越界/非数字 fail-closed
6. **行数与回归**：engine ≤220、enhance ≤150、gui_enhance ≤200；
   smoke_v23（改后）+ smoke_v22 + CLI 全通（金币 918、难度 0）仍绿
   —— CLI 全通的金币仍是 918，因为强化与死亡惩罚都不在全通路径里
   （全通一路打赢不死、不强化）

## 7. 明确不做（留给 V2.5，别在本期硬塞）

- 爬塔、无级别武器、武器谱特效、图鉴窗、validate.py、技能 10 个、
  经验曲线 60×lv^1.65、Lv.1 开局：全部是 V2.5 或平衡期的范围。
- 强化不碰词条、不改品质、不改装备 Lv；+10 已是本期天花板，
  不做 +11 以上的“突破”系统。
- 保底符不提高成功率、不叠加使用（一次强化最多消耗 1 张）。
