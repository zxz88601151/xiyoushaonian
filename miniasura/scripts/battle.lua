-- MiniAsura §3/V2.1 数值脚本层 —— 策划的地盘
-- 引擎经 subprocess 传 argv（全数字，第 4 课编码铁律），这里只回一行 JSON
-- 用法1: lua battle.lua damage  <攻击力> <威力倍率> <暴击0或1> [暴伤加成] [浮动骰95-105]
--         → {"dmg": N, "crit": b}   （暴击倍率 = CRIT_MULTIPLIER + 暴伤加成；浮动归引擎掷）
-- 用法2: lua battle.lua levelup <现有经验> <本次获得> <每级所需> <当前等级> → {"level": N, "exp": N}
-- 用法3: lua battle.lua attack  <基础攻击> <当前等级> <每级成长> → {"attack": N}
-- 用法4: lua battle.lua incoming <怪攻击> <防御> → {"dmg": N}  （V2.1 防御减伤）

local CRIT_MULTIPLIER = 2                            -- 策划改这里，引擎不用重编

local cmd = arg[1]

if cmd == "damage" then
    local attack, power, crit = tonumber(arg[2]), tonumber(arg[3]), arg[4] == "1"
    local critdmg = tonumber(arg[5]) or 0            -- 词条暴伤加成（0.10~0.25 一类）
    local rand = tonumber(arg[6]) or 100             -- 引擎掷的浮动骰 95~105，缺省=无浮动
    local mult = 1
    if crit then
        mult = CRIT_MULTIPLIER + critdmg
    end
    local dmg = math.floor(math.max(1, attack * power * mult * rand / 100))
    print(string.format('{"dmg": %d, "crit": %s}', dmg, tostring(crit)))

elseif cmd == "levelup" then
    local exp, gain, need, level =
        tonumber(arg[2]), tonumber(arg[3]), tonumber(arg[4]), tonumber(arg[5])
    exp = exp + gain
    while exp >= need do                             -- 经验溢出可连升
        exp = exp - need
        level = level + 1
    end
    print(string.format('{"level": %d, "exp": %d}', level, exp))

elseif cmd == "attack" then
    local base, level, per = tonumber(arg[2]), tonumber(arg[3]), tonumber(arg[4])
    print(string.format('{"attack": %d}', base + (level - 1) * per))

elseif cmd == "incoming" then
    local atk, def = tonumber(arg[2]), tonumber(arg[3])
    print(string.format('{"dmg": %d}', math.floor(math.max(1, atk - def * 0.6))))

else
    print('{"error": "unknown command"}')
end
