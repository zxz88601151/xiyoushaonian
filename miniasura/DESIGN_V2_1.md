# MiniAsura V2.1 设计冻结 —— 背包 + 装备 + 词条（+ GM 发装备）

> 2026-10-28 业主授权开工。承接 DESIGN_V2.md §2（装备/词条蓝图）与 V2.0 依赖规则
> `gui_* → engine → save`（engine 永不 import Qt、不出现 user/server）。
> 铁律加一条：**装备数值公式只住 scripts/equip.lua，引擎永远不算装备数值**。

## 1. 契约（谁负责什么）

| 模块 | 只负责 | 明确不负责 |
|---|---|---|
| scripts/equip.lua（新） | 主属性公式（白装基准×品质倍率）、词条取值公式（区间/保底中位） | 选词条（选择=概率，归 Python 侧掷骰）、不读文件 |
| gear.py（新） | 从 mpak 读 affixes.txt、词条挑选（rng 注入可测）、调 equip.lua 生成物品、**聚合**穿戴加成 | 不懂战斗流程、不写存档 |
| assets/affixes.txt（新） | 词条池数据：key\|名称\|种类\|区间\|部位限制\|紫装限定 | 不写公式 |
| save.py（改） | schema 3：+inventory[]、+equipment{}；迁移链 v1/v2→3 | 不判断穿什么（那是 gui/gm 的事） |
| engine.py（改） | 战斗时**消费** gear 聚合结果（攻/防/暴击/暴伤/吸血/经验加成） | 不算任何装备数值 |
| gm.py（改） | `give <slot> <lv> [quality=2]`：生成→查容量→入包 | 不经引擎主循环（上帝视角不变） |
| gui_bag.py（新） | 背包/装备窗：穿、卸、丢、属性合计展示 | 不碰战斗逻辑；只经 save 层落盘 |

**簿记约定（唯一一处 Python 做的"算术"）**：百分比词条（攻击%/HP%）以
（主属性 + 平铺词条）为基数，聚合求和写在 gear.py——公式本体（区间、等级成长、
品质倍率、保底）全部在 equip.lua 生成时算死存进物品，聚合只是加法簿记。

## 2. 数据模型（schema 3）

```
item = {"slot": 0-4, "lv": int, "quality": 0白/1蓝/2紫,
        "main":  {"atk","hp","def","dodge"},          # equip.lua 生成时算死
        "affixes": [{"key","name","val"}, ...]}       # 生成时算死
save 新增: "inventory": [item...]（容量 20，满则拒绝获得）
           "equipment": {"weapon","helm","armor","belt","boots"} 各为 item 或 null
```

## 3. 公式（蓝本 §2.2/§2.3 原样落 equip.lua）

- 主属性（白装基准）：武器 ATK=5+lv×3 ｜ 头盔 HP=30+lv×8 ｜ 护甲 DEF=2+lv×1.5 ｜
  腰带 HP=15+lv×4 且 DEF=1+lv×0.5 ｜ 靴子 闪避%=3+lv×0.4；蓝/紫 ×1.4/×1.9（向下取整）
- 词条：flat 类 = lv×(lo+(hi−lo)×r/10000)；pct 类 = lo+(hi−lo)×r/10000；
  **紫装第 2 条词条保底 ≥ 区间中位**；同件词条不重复；部位限制见 affixes.txt；
  吸血仅紫武器（quality==2 且 weapon 才进候选）
- 战斗接入（battle.lua）：暴击倍率 = CRIT_MULTIPLIER + 暴伤加成；
  伤害浮动 = 引擎掷 rand(95~105) 传入（概率归引擎，公式归 Lua）；
  新命令 `incoming <怪攻> <防御>` → max(1, 怪攻 − DEF×0.6)；
  吸血/经验加成由引擎按流程施加（回血=伤害×吸血率，向下取整，不溢出上限）

## 4. 出口验收（门禁，全实测）

1. **公式抽查**：equip.lua 白武器 lv10 → ATK 35；紫 ×1.9 → 66；affix 区间端点与保底中位各实测
2. **词条规则**：30 个随机种子批跑——紫装恒 2 词条、第 2 条 ≥ 中位、无重复 key、吸血只出现在紫武器
3. **GM 一键发紫装**：gm give 入包、容量 20 满拒绝第 21 件
4. **穿戴实时生效**：穿紫武器后 engine 攻击力=基础+装备加成；incoming 防御减伤实测；战斗内吸血回复出现
5. **迁移**：v2 档（无 inventory）→ 自动升 3 且原字段不丢；schema3 档二次读不改写
6. **回归**：V2.0 冒烟 18/18 全绿；CLI 管道完整通关（伤害浮动与暴伤不破坏骰子稳胜）
