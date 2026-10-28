-- 第 4 课：人生第一个 Lua 脚本
-- 五个知识点：local 变量 / .. 连接 / string.format / table / for 循环

local hero = {
    name = "花果山小妖",              -- 字典写法：键 = 值
    level = 12,
    skills = { "定海神针", "筋斗云", "七十二变" },   -- 数组写法：下标从 1 开始
}

print("我是 " .. hero.name .. "，前来报到！")                    -- .. 把字符串接起来
print(string.format("%s 等级 %d，会 %d 个技能", hero.name, hero.level, #hero.skills))   -- # 取长度

for i = 1, #hero.skills do
    print(string.format("  第 %d 格技能：%s", i, hero.skills[i]))
end
