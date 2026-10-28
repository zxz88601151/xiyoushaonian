-- MiniAsura V2.1 装备数值脚本 —— 策划的地盘（蓝本 §2.2/§2.3 公式原样落这里）
-- argv 全数字/ASCII（编码铁律），只回一行 JSON；引擎/gm 经 subprocess 调用
-- 用法1: equip.lua main  <部位0-4> <物品等级> <品质0白1蓝2紫>
--         → {"atk": N, "hp": N, "def": N, "dodge": N}   （白装基准 × 品质倍率）
-- 用法2: equip.lua affix <种类0成长/1区间> <物品等级> <随机数0-10000> <下限> <上限> <保底中位0/1>
--         → {"val": N}
local QUALITY_MULT = {1.0, 1.4, 1.9}                 -- 蓝×1.4 紫×1.9（蓝本 §2.1）

local cmd = arg[1]

if cmd == "main" then
    local slot, lv, q = tonumber(arg[2]), tonumber(arg[3]), tonumber(arg[4])
    local m = QUALITY_MULT[q + 1]
    local atk, hp, def, dodge = 0, 0, 0, 0
    if slot == 0 then
        atk = 5 + lv * 3                              -- 武器
    elseif slot == 1 then
        hp = 30 + lv * 8                              -- 头盔
    elseif slot == 2 then
        def = 2 + lv * 1.5                            -- 护甲
    elseif slot == 3 then
        hp = 15 + lv * 4                              -- 腰带（双属性）
        def = 1 + lv * 0.5
    elseif slot == 4 then
        dodge = 3 + lv * 0.4                          -- 靴子（闪避%，v2.2 启用）
    end
    print(string.format('{"atk": %d, "hp": %d, "def": %.2f, "dodge": %.2f}',
          math.floor(atk * m), math.floor(hp * m), def * m, dodge * m))

elseif cmd == "affix" then
    local kind, lv, r, lo, hi = tonumber(arg[2]), tonumber(arg[3]),
                                tonumber(arg[4]), tonumber(arg[5]), tonumber(arg[6])
    local mid = arg[7] == "1"                          -- 紫装第 2 条保底 ≥ 区间中位
    local t = r / 10000
    local val
    if kind == 0 then
        val = lv * (lo + (hi - lo) * t)                -- 等级成长类（攻击/防御）
    else
        val = lo + (hi - lo) * t                       -- 区间类（各种 %）
    end
    if mid then
        local floor_v = (kind == 0) and lv * (lo + hi) / 2 or (lo + hi) / 2
        if val < floor_v then
            val = floor_v
        end
    end
    print(string.format('{"val": %.4f}', val))

else
    print('{"error": "unknown command"}')
end
