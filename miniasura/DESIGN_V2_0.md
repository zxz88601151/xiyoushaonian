# MiniAsura V2.0 设计冻结 —— 登录链 + 多存档槽 + 窗口路由

> 承接 DESIGN_V2.md（冻结蓝图）+ V2 补全提案（2026-10-28，经审计采纳 + 三处修订）。
> 本文冻结 V2.0 范围。铁律不变：零联网；引擎管流程、数值住 Lua、配置外置；
> **新增第零规则：依赖单向 `gui_*.py → engine.py → save.py`，engine.py 永不 import Qt。**

## 0. 范围（做什么 / 明确不做什么）

**做**：注册/登录/会话、伪区服选择、每账号 3 存档槽、窗口路由（QStackedWidget）、
v1 存档迁移 schema 2、CLI GM 调试台。
**不做**：联网/真实服务器（伪区服=本地目录分组）、存档加密、GUI 调试面板（V2.3+ 再议）、
音效、内购抽卡。

## 1. 玩家旅程（V2.0 打通的链路）

```
启动 app.py
  └→ 登录窗（注册 / 登录 / 上次登录自动填充）
       └→ 选区窗（servers.txt 两行伪区服）
            └→ 存档槽窗（3 槽：等级/进度/周目 预览 + 删除带确认）
                 └→ 主城/大厅窗（公告 news.txt + 开始战斗）
                      └→ 战斗窗（现 gui.py 整体降级迁入）
                           └→ 结算 → 返回大厅窗
```

## 2. 模块与契约

| 文件 | 职责 | 行数上限 |
|---|---|---|
| `login.py`（新） | accounts.json 读写、盐哈希校验、session.json | 80 |
| `save.py`（改） | `set_path()` 注入 + schema 2 + `migrate_v1()`；引擎只调 load/write | 90 |
| `slots.py`（新） | 槽位列表/删除/预览（纯数据层，GUI 可测） | 70 |
| `gm.py`（新） | CLI 调试台：`setlevel/next/wipe`，管道可测 | 60 |
| `app.py`（新） | QStackedWidget 路由 + 各窗装配 | 100 |
| `gui_login.py / gui_hub.py / gui_slots.py`（新） | 各窗，只读自己的数据源 | 各 200 |
| `gui.py`（降级） | 仅战斗窗，`battle_widget()` 供路由调用 | 200 |
| `engine.py`（微改） | 接受 save 路径注入；**CLI 模式保留默认路径 = dev 快捷通道**（管道回归不受影响） | — |

- 账号：`accounts.json = [{"user", "salt", "hash"}]`，`hash = sha256(salt + password)`；
  salt 用 `secrets.token_hex(16)`；重名/空密码拒绝注册；**永不存明文**。
  （教学级写法；真实生产用 bcrypt/argon2 慢哈希，原理课提一句即可）
- 会话：`session.json = {"user", "server"}`，登出删除；GUI 重启读取实现"记住上次登录"。
- 伪区服：`servers.txt` 两行（`huaguoshan|电信一区·花果山` / `gaolaozhuang|网通二区·高老庄`），
  选区 = 选 `saves/<server>/<user>/` 目录前缀，纯本地。
- 存档路径注入：`save.set_path(abs_path)` 由外围（app.py / gm.py）在引擎启动前调用；
  **engine.py 内不得出现 user/server 字样**（契约检查项）。

## 3. 存档 schema 2（只带 V2.0 实际读写的字段）

| 字段 | 类型 | 说明 | 迁移来源 |
|---|---|---|---|
| schema | int | 恒为 2 | 新增 |
| user | str | 所属账号（外围写入，引擎只读） | 新增 |
| level / exp / hp / mp / attack | int | 角色数值 | v1 同名 |
| next | int | 下一战序号 | v1 同名 |
| week | int | 周目数：0=未通关，≥1=第 N 周目 | **v1 `cleared` 映射：true→1，false→0** |
| playtime | int | 累计游玩秒数（引擎每次写档时累加） | 新增（v1 无则 0） |

inventory / equipment / gold / quest_flags 等字段**不进 schema 2**——各自期（V2.1~V2.3）
落盘时 bump schema 并附迁移函数。`migrate_v1()` 规则：读 v1 save.json → 补默认值 →
cleared→week → 写回 schema 2；**v1 档升 2 级后 level/exp/hp/mp/next 不许丢**。

## 4. GM 调试台（CLI，修订项 1）

```
python gm.py setlevel <n>    # 当前会话存档等级设为 n（攻击力随之重算）
python gm.py next <k>        # 跳到第 k 场战斗（0 起）
python gm.py wipe            # 删除当前槽位存档（带确认回显）
```

操作对象 = session.json 指向的当前槽位；无会话时报错退出（fail-closed）。
命令行直连 save 层，不经过引擎主循环——调试台是"上帝视角"，这是它与玩家的本质区别。

## 5. 出口验收（门禁，全实测）

1. **全链路**：GUI 注册新账号 → 选区 → 建槽 → 进入战斗窗打一场 → 结算回大厅；
   中途杀进程重开 → 会话恢复 → 存档槽预览正确
2. **迁移**：把 v1 save.json 放入槽位 → 启动 → 自动升 schema 2 →
   level/exp/hp/mp/next 与 v1 档一致，week 映射正确（cleared 档 → week 1 开新周目）
3. **fail-closed**：错误密码登录被拒；gm.py 无会话时报错；重名注册被拒
4. **GM 台**：三条命令管道实测各一次，行为与定义一致
5. **边界**：`grep -n "Qt\|PySide" engine.py` 零命中；engine.py 全文无 user/server 字样
6. **回归**：`python engine.py`（CLI dev 模式）管道喂 `1` 仍能完整通关（v1 行为不破坏）
