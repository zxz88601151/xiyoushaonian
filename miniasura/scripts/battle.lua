-- MiniAsura §3/V2.1 数值脚本层 + V2.5 经验曲线 —— 策划的地盘
-- 引擎经 subprocess 传 argv（全数字，第 4 课编码铁律），这里只回一行 JSON
-- 用法1: lua battle.lua damage  <攻击力> <威力倍率> <暴击0或1> [暴伤加成] [浮动骰95-105] [特效倍率]
--         → {"dmg": N, "crit": b}   （暴击倍率 = CRIT_MULTIPLIER + 暴伤加成；浮动归引擎掷；特效倍率缺省 1.0）
-- 用法2: lua battle.lua levelup <现有经验> <本次获得> <当前等级> <等级上限> <曲线基数> <曲线指数x100> <距开局级数>
--         → {"level": N, "exp": N}  每级所需 = floor(基数 × 级数^(指数/100))，级数最小取 1，封顶后不再涨
-- 用法3: lua battle.lua attack  <基础攻击> <当前等级> <每级成长> → {"attack": N}
-- 用法4: lua battle.lua incoming <怪攻击> <防御> [减伤系数] → {"dmg": N}  （防御减伤；系数缺省 1.0 = 不减伤）
-- 用法5: lua battle.lua expneed <距开局级数> <曲线基数> <曲线指数x100> → {"need": N}

local CRIT_MULTIPLIER = 2                            -- 策划改这里，引擎不用重编

local cmd = arg[1]

local function need_of(steps, base, pow100)          -- V2.5 经验曲线（蓝图 §7）：60 × 级数^1.65
    if steps < 1 then steps = 1 end
    return math.floor(base * math.pow(steps, pow100 / 100))
end

if cmd == "damage" then
    local attack, power, crit = tonumber(arg[2]), tonumber(arg[3]), arg[4] == "1"
    local critdmg = tonumber(arg[5]) or 0            -- 词条暴伤加成（0.10~0.25 一类；白骨剑 +0.15 也走这里）
    local rand = tonumber(arg[6]) or 100             -- 引擎掷的浮动骰 95~105，缺省=无浮动
    local effect = tonumber(arg[7]) or 1.0           -- V2.7 武器谱特效倍率（定水枪/降魔杖/芭蕉扇）
    local mult = 1
    if crit then
        mult = CRIT_MULTIPLIER + critdmg
    end
    local dmg = math.floor(math.max(1, attack * power * mult * rand / 100 * effect))
    print(string.format('{"dmg": %d, "crit": %s}', dmg, tostring(crit)))

elseif cmd == "levelup" then
    local exp, gain, level, cap, base, pow100, steps =
        tonumber(arg[2]), tonumber(arg[3]), tonumber(arg[4]), tonumber(arg[5]),
        tonumber(arg[6]), tonumber(arg[7]), tonumber(arg[8])
    exp = exp + gain
    while level < cap do                             -- 经验溢出可连升；到 cap 封顶不再涨
        local need = need_of(steps, base, pow100)
        if exp < need then break end
        exp = exp - need
        level = level + 1
        steps = steps + 1                            -- 级数随等级一起走，下一级更贵
    end
    print(string.format('{"level": %d, "exp": %d}', level, exp))

elseif cmd == "attack" then
    local base, level, per = tonumber(arg[2]), tonumber(arg[3]), tonumber(arg[4])
    print(string.format('{"attack": %d}', base + (level - 1) * per))

elseif cmd == "expneed" then
    local steps, base, pow100 = tonumber(arg[2]), tonumber(arg[3]), tonumber(arg[4])
    print(string.format('{"need": %d}', need_of(steps, base, pow100)))

elseif cmd == "incoming" then
    local atk, def = tonumber(arg[2]), tonumber(arg[3])
    local mitigate = tonumber(arg[4]) or 1.0         -- V2.7 不坏金身减伤系数（缺省 1.0 = 不减伤）
    print(string.format('{"dmg": %d}', math.floor(math.max(1, atk - def * 0.6) * mitigate)))

else
    print('{"error": "unknown command"}')
end
