# V2.4 强化核心 —— 只算费用、成功率与结果，不认识 GUI、存档与战斗。
# GUI 与 GM 都调 enhance()，不各写一套概率；rng 可注入（测试用固定随机）。
import random

MAX_ENH = 10
PROTECT_PRICE = 100
# 升一级成功率：+1~+6 100%，+7 80%，+8 70%，+9 60%，+10 50%（下标 = 当前 enh）
SUCCESS_RATE = [100, 100, 100, 100, 100, 100, 100, 80, 70, 60, 50]


def cost(item):
    """升一级费用 = 20 × (enh+1) + 装备 Lv × 2（金币）。"""
    return 20 * (item.get("enh", 0) + 1) + item["lv"] * 2


def success_rate(item):
    return SUCCESS_RATE[item.get("enh", 0)]


def enhance(item, gold, protect, use_protect, rng=random):
    """返回 (success, new_gold, new_protect, message)。
    金币不足或已 +10 时不扣钱、不改装备；失败时金币照扣。"""
    enh = item.get("enh", 0)
    if enh >= MAX_ENH:
        return False, gold, protect, "已经 +10，到顶了。"
    price = cost(item)
    if gold < price:
        return False, gold, protect, f"金币不足：需要 {price}，你只有 {gold}。"
    gold -= price
    if rng.randint(1, 100) > SUCCESS_RATE[enh]:
        if use_protect and protect > 0:
            return False, gold, protect - 1, f"强化失败！保底符抵挡了降级（+{enh} 不变，消耗 1 张）。"
        item["enh"] = enh - 1 if enh >= 7 else enh
        if enh >= 7:
            return False, gold, protect, f"强化失败！降级：+{enh} → +{enh - 1}。"
        return False, gold, protect, "强化失败（+6 以下本不该失败，见成功率表）。"
    item["enh"] = enh + 1
    return True, gold, protect, f"强化成功！+{enh} → +{enh + 1}。"
