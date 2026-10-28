-- hello.lua — Lua 5.1 语法速览
-- Lua 的注释用两个减号开头（不是 Python 的 #）

print("你好，斗战神")                    -- 打印，和 Python 的 print 一样

-- 1. 变量：不需要声明类型，直接赋值
local player = "灵猴"                   -- local = 局部变量（不加 local 会变成全局变量，大忌）
local level = 45
local hp = 1234.5

-- 2. 字符串连接用 .. （两个点）
print("角色: " .. player .. "，等级: " .. level)

-- 3. string.format：像 C 语言一样排版
print(string.format("血量: %.1f，血量翻倍: %d", hp, hp * 2))

-- 4. table = Lua 唯一的数据结构，既当数组又当字典
local skills = { "七十二斩", "分身", "隐身" }        -- 当数组用（下标从 1 开始！不是 0）
print("第 1 个技能: " .. skills[1])

local boss = { name = "白骨夫人", hp = 999999 }     -- 当字典用
print(boss.name .. " 有 " .. boss.hp .. " 点血")

-- 5. for 循环：从 1 数到 #skills（# 号 = 取数组长度）
for i = 1, #skills do
    print("技能栏第 " .. i .. " 格: " .. skills[i])
end
