# MiniAsura V2.9-C 设计冻结（GUI 战报显眼化）

## 基线
`cf76c67`（V2.9-B 毕业：爬塔战报 + 稀有 fled）。**schema 9 不变**。
本期只补 GUI 表现层与 io 富通道，**不碰** combat 公式、数值、掉落、任务、schema、存档字段。
路线稿 `DESIGN_V3_0_ROADMAP_DRAFT.md` §1 对 C 期的定义：战斗窗独立战报区 / 常驻显示 / 多场合计。

## §0 现状审计（2026-10-30 实测，非推断）

| 项 | 实测值 |
|---|---|
| GUI 全通（offscreen + AUTO 自动答题） | 日志 **272 行 / 5941 字符 / 12 条战报** |
| 战报行位置（1-based） | 41 / 64 / 84 / 97 / 118 / 146 / 155 / 183 / 201 / 225 / 234 / **275** |
| 最后一战（白骨夫人） | 战报在第 275 行，其后还有结局、等级、任务、地图统计 5+ 行 |
| 战报呈现 | 与普通日志同字号、同色、无边框、无前缀分隔，滚动后无锚点 |
| 爬塔窗 | V2.9-B B1 已让 tower 打战报，同样只是一行日志；日志跨层累积，越打越淹没 |
| 通路现状 | `CliIo` 只有 `say/ask`（engine.py:25-30）；`print_report` 只有 `io.say` 单一通道（encounter.py:108-113） |

结论：**数据齐全（rep 五项）、通路存在（io.say），缺的是"显眼"与"可回看"**。C 期不动口径，只补表现。

## §1 裁决（建议冻结值）

| 编号 | 裁决 | 理由 |
|---|---|---|
| D1 | **`io.report(rep, line)` 富通道 + `hasattr` 回退**，不用字符串嗅探 | GUI 合计需结构化数字；嗅探 `"战报："` 前缀改文案即失效。与项目既有"引擎认接口不认实现"（gui.py:27）一致。CLI 无 `report` → 自动回退 `say`，**CLI 输出逐字节不变** |
| D2 | **日志上方常驻战报卡**（QLabel 富文本两行：本场 / 本局累计），**不做弹窗** | 弹窗会阻塞 AUTO 冒烟与 offscreen 测试，还要处理关闭态；常驻卡不阻断交互、随时可回看 |
| D3 | **日志仍保留战报行** | `GuiIo.report` 既 emit 富通道、也 `say(line)`。日志保持完整原文可复制可排查，卡片只负责显眼 |
| D4 | 合计 = **本窗口会话累计**（主线 `begin()` 清零），不写存档、不升 schema | 统计项：场数 / 回合 / 造成 / 承受 / 暴击 / MISS。跨会话合计属留存期，不在本期 |
| D5 | **爬塔窗同步接入**，共用同一卡片组件 | B1 已让爬塔打战报，只给主线不加塔是半成品；复用避免两份实现 |
| D6 | 样式**不用固定色值**，只用默认前景色 + 加粗 + 稍大字号 + 边框 | 项目无样式表，固定深色在深色系统主题下不可读 |
| D7 | 卡片标题写「**最近一场战报**」，不写「本次」 | escaped / fled 不打印战报（V2.9-A/B 定版语义），此时卡片保留上一场数字，标题必须如实 |
| D8 | 行数：encounter **保持 170**；gui.py 197→**≤210**；gui_tower.py 165→**≤200**（沿用既有上限）；新增 gui_report.py **≤60** | encounter 已顶格，`print_report` 内部改写不增行；两个 GUI 文件各约 +8 行 |

## §2 接口契约

### 2.1 `print_report` 单点分派（encounter.py，行数不变）
```python
def print_report(io, rep):
    """战报（DESIGN_V2_9_A §1.1）：只打印，不改数值；V2.9-C 起优先走 io.report 富通道。"""
    if not rep: return
    line = (f"战报：{rep.get('rounds', 0)}回合 / 造成{rep.get('dealt', 0)}伤害 / "
            f"承受{rep.get('taken', 0)}伤害 / 暴击{rep.get('crits', 0)}次 / MISS {rep.get('misses', 0)}次")
    io.report(rep, line) if hasattr(io, "report") else io.say(line)
```
- **文案一字不改**（全链 smoke_v29a/v29b 断言文本）。
- 6 行 → 6 行，encounter 仍 170。
- `hasattr` 必须对 `SimpleNamespace` / 测试桩安全：无 `report` 走 `say`，行为与今天完全一致。

### 2.2 `GuiIo.report`（gui.py / gui_tower.py 各一份）
```python
    def report(self, rep, line):
        self.bridge.reported.emit(rep, line)   # V2.9-C：显眼通道（战报卡）
        self.say(line)                          # 日志仍保留完整原文（D3），不丢记录
```

### 2.3 Bridge 信号
`Bridge` 增 `reported = Signal(dict, str)`（PySide6 实测可传 dict+str）；widget 侧 `bridge.reported.connect(self.card.show_report)`。

### 2.4 `ReportCard`（新模块 gui_report.py）
- `show_report(rep, line)`：保存"最近一场"，累加会话合计，刷新两行富文本。
- `reset()`：清空最近一场与合计（主线 `begin()` 调用；爬塔跨层累计，不重置）。
- 第一行：`最近一场战报 · 3 回合 · 造成 146 · 承受 21`
- 第二行：`暴击 0 · MISS 1 ｜ 本局累计：8 场 / 造成 1024 / 承受 189`
- 空态：`（还没有战报）`。
- 只用 `<b>` + `setPointSize` + `QFrame.StyledPanel`，不写 `setStyleSheet`（D6）。

## §3 模块分工与行数
| 模块 | 现行 | 本期改动 | 上限 |
|---|---|---|---|
| encounter.py | 170 | `print_report` 内部改单点分派 | **170 不变** |
| gui.py | 197 | import / 建卡 / 加布局 / 信号 / `GuiIo.report` / `begin` 清卡 ≈ +9 | **210** |
| gui_tower.py | 165 | 同构接入 ≈ +9 | **200**（既有） |
| gui_report.py | 新建 | ReportCard + 合计 | **60** |
| combat.py / engine.py / tower.py | 130 / 222 / 100 | **不动** | 不变 |

## §4 schema
**不升 schema。** 合计只活在窗口内存，关窗即失；不新增字段、不改 `save.py`。

## §5 出口验收（smoke_v29c，八门禁）
1. **CLI 不变（回退路径）**：只有 `say/ask` 的桩 io 调 `print_report` → 走 `say`，文本与旧格式完全一致。
2. **富通道（命中路径）**：带 `report()` 的桩 io → 收到 `(rep, line)` 各一次，`say` 不被调用。
3. **日志不丢（D3）**：`GuiIo.report` 后，`said` 仍收到同一行原文。
4. **卡片数字**：连喂两场（如 3 回合/146/21/0/1 与 1 回合/224/0/1/0），卡片文本含两场关键数字，累计 = 两场之和。
5. **reset**：`reset()` 后回空态，累计归零。
6. **两窗接入**：`BattleWidget` 与 `TowerWindow` 均有 `card`，且 `Bridge.reported` 已连到卡片。
7. **GUI 实跑**：offscreen 全通后，卡片累计场数 = 12、文本含「最近一场战报」，且日志中 `"战报："` 行数仍为 12（不重复打印）。
8. **行数 + 全链回归**：encounter≤170 / gui.py≤210 / gui_tower≤200 / gui_report≤60；`v20→…→v29b` 全链全绿。

## §6 风险与硬禁区
- **战报文案禁止改动**：v29a/v29b 断言文本；改文案=红线，只能改"呈现方式"。
- **`hasattr` 回退必须安全**：任何 io 桩（`ScriptIo` / `SimpleNamespace` / `CliIo`）都不能因缺 `report` 抛异常。
- **不许引入全局样式表**：只允许单控件字体/边框，避免污染其它窗口。
- **不许在后台线程直接碰控件**：沿用现有 `Signal` 机制（引擎线程 emit，主线程槽）。
- **escaped / fled 仍不打印战报**：卡片标题「最近一场」就是为这条语义兜底，不能改成「本次」。
- **合计不得写存档**：写档就要 schema bump，本期明确不做。

## §7 明确延期
- 战报历史列表 / 按场回看（要持久化，留到 D 期）。
- 跨会话累计与幻影榜（D1 纪录取向）。
- 战报动画、飘字、音效（红线）。
- 精英/稀有的战斗标签在卡片上着色（要 mon 上下文，rep 里没有，等 D 期扩 rep）。

## §8 施工（单批，风险低）
1. 新增 `gui_report.py`（ReportCard）。
2. `encounter.print_report` 改单点分派（6 行不变）。
3. `gui.py` 接入（信号 + 卡片 + reset）；`gui_tower.py` 同构接入。
4. 写 `tests/smoke_v29c.py`（八门禁），跑通 + 全链回归。
5. 独立 commit；文档同步（README 期数/门禁命令）。

> 本文件为冻结稿草案，**未提交、未施工**。业主确认 D1–D8 后入仓，再一句话开工。
