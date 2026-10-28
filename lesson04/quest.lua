-- 第 4 课下半场：函数 + 条件判断（战斗脚本）

local function calcDamage(base, isCrit)
    if isCrit then
        return base * 2
    else
        return base
    end
end

local function levelUp(hero, exp)
    if exp >= 100 then
        hero.level = hero.level + 1
        return "升级！"
    else
        return "还差 " .. (100 - exp) .. " 点经验"
    end
end

-- ── 测试 1：伤害的两条路 ──
local hero = { name = "花果山小妖", level = 12 }
print(string.format("普通一击：%d 点伤害", calcDamage(50, false)))
print(string.format("暴击一击：%d 点伤害", calcDamage(50, true)))

-- ── 测试 2：升级的两条路（含刚好 100 的边界）──
print(levelUp(hero, 30))
print(string.format("  现在 Lv.%d", hero.level))
print(levelUp(hero, 100))
print(string.format("  现在 Lv.%d", hero.level))
print(levelUp(hero, 99))
print(levelUp(hero, 250))
print(string.format("  现在 Lv.%d", hero.level))
