# MiniAsura 设计冻结（v1.2）

> 2026-10-28 业主授权（采纳 3 处修正后冻结 v1.1）。
> **v1.2 增补（2026-10-28，业主授权"§4 存档、给 engine.py 套 PySide6 界面"）**：
> §4 存档（save.py 外围模块）+ §5 GUI（gui.py）。v1 "不做 GUI" 的 YAGNI 条款
> 就此由业主本人作废；冻结规则不变——后续再改仍须先改本文件。

## 1. 目录结构

```
learn-lab/miniasura/
├── DESIGN.md            ← 本文件（设计冻结）
├── game.ini             ← 全部数值参数（血量/攻击/威力/耗蓝/经验/暴击率…）
├── engine.py            ← 主程序：主循环 + 战斗流程 + 资源加载 + Lua 调用
├── assets/              ← 素材源文件夹（纯文本，一个数字都不放——数值全归 game.ini）
│   ├── skills.txt       ← 技能文本（key|名称|描述），威力/耗蓝在 game.ini [skill.*]
│   ├── monsters.txt     ← 怪物文本（key|名称|出场台词），血量/攻击/经验在 game.ini [monster.*]
│   └── intro.txt        ← 开场白
├── assets.mpak          ← 打包产物（复用 ../lesson03/mypack.py 生成，引擎只认它不认 assets/）
├── scripts/
│   └── battle.lua       ← 伤害计算 + 暴击 + 等级→攻击力公式 + 升级判断（全部数值逻辑住这里）
├── build.py             ← 一键构建：import mypack → pack assets/ → assets.mpak（不 fork 解包器代码）
├── save.py              ← §4 存档外围（load/write save.json；对应真游戏 TCLS 外围层，引擎不存档，只调用）
├── gui.py               ← §5 PySide6 界面外壳（只做显示/收输入，复用 engine 整套逻辑；engine 不 import Qt）
└── save.json            ← 存档数据（§4 起启用）
```

mpak 读取方式：engine.py 启动时 import mypack，把 assets.mpak **unpack 到临时目录**读文本，进程结束清理；不另写第二遍解包器。

## 2. 数据流（唯一一条主线）

```
game.ini ──┐
           ├──→ engine.py（读配置 + 从 assets.mpak 读素材）
assets.mpak ─┘         │
                       │ 战斗发生时
                       ▼
              调用 lua.exe scripts/battle.lua
              传入: 玩家攻击力 / 技能威力 / 是否暴击
              返回: 一行 JSON（伤害值 或 升级结果）
                       │
                       ▼
              engine.py 打印战斗过程，直到 boss 死亡 → 通关结算
```

## 3. 模块契约（谁负责什么，越界即违宪）

| 模块 | 只负责 | 明确不负责 |
|---|---|---|
| engine.py | 流程、读包、调 Lua、掷暴击骰（概率来自 ini）、调 save 存档 | **不算伤害、不管经验曲线和攻击力公式、不 import Qt** |
| battle.lua | 伤害数值、暴击倍率、**等级→攻击力公式**、升级判断 | 不打印、不读文件（纯函数，只收参数返回 JSON） |
| game.ini | 所有可调数值 | 不写逻辑 |
| assets.mpak | 文本素材 | 不存数值（数值归 ini 和 Lua） |
| save.py | 只读写 save.json 这一个文件 | 不懂游戏规则，不算任何数值 |
| gui.py | 显示战斗日志、收玩家指令（经 CliIo 同款 say/ask 接口注入引擎） | 不碰战斗逻辑、不读 ini/mpak |

调用 Lua 的方式：`subprocess` 起 `lua.exe scripts/battle.lua 参数...`，
battle.lua 末尾 `print(json)`——**引擎与脚本只靠一行 JSON 通信**，
这就是 AGE 与 Lua51.dll 边界的玩具版：跨语言 = 只传数据，不传控制。

**编码铁律（第 4 课实测教训）**：argv 只允许数字和 ASCII——Lua 5.1 在
Windows 上走 ANSI 命令行，UTF-8 中文传进去必乱码。技能名、台词等文本
永远留在引擎侧，Lua 只收发数字。Lua 5.1 无内置 JSON 库，返回的 JSON
用 `string.format` 手拼（纯数字场景无编码问题）。

## 4. 游戏内容（v1 范围）

- 玩家：花果山小妖，初始 Lv.14（接第 4 课存档梗），技能 3 个（定海神针/筋斗云/七十二变）
- 关卡：3 只小妖（小妖甲/乙/丙）→ 最终 boss 白骨夫人，纯回合制，无地图无移动
- 战斗动作：1 普攻 / 2 技能（列表选择）/ 3 逃跑（boss 战逃跑必失败，血泪设定）
- 胜负：玩家血 ≤0 失败；boss 血 ≤0 通关，打印战绩结算
- **v1 不做**：地图/移动、背包物品、多角色、音效、GUI——一律 YAGNI

## 5. 验收标准（§4 结束时逐条对照）

1. `python build.py` 能从 assets/ 产出 assets.mpak，且 mypack.py get 能取回任一素材
2. `python engine.py` 能完整打完一局并通关
3. **改 game.ini 里 boss 血量，不改任何代码，再开一局血量生效**
4. **改 battle.lua 的暴击倍率，不改任何代码，暴击伤害变化**
   （3、4 两条 = "配置与逻辑全外置"的验收，做不到就不许叫同构）
5. **§4**：通关一局 → save.json 记 cleared=true + 最终等级；**关游戏重开，存档等级还在**（通关存档开新周目，中途存档从下一战继续）
6. **§5**：`python gui.py` 出 PySide6 窗口，同一套战斗逻辑能从 GUI 完整打通关；engine.py 代码零 Qt 依赖
