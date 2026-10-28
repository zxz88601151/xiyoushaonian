# 第 5 课彩蛋：PE 身份鉴定 —— 时间戳 + 链接器版本 + 节区熵值 + Rich 头
# 用法: python pe_forensics.py <文件路径>

import pefile
import sys
from datetime import datetime, timezone

path = sys.argv[1]
pe = pefile.PE(path)

print(f"=== 身份鉴定: {path} ===")

# ── 1. 编译时间戳 → 人类日期 ──
ts = pe.FILE_HEADER.TimeDateStamp
print(f"编译时间: {datetime.fromtimestamp(ts, tz=timezone.utc):%Y-%m-%d %H:%M} UTC")

# ── 2. CPU 架构 + 链接器版本（链接器版本号 = 工具链时代的指纹）──
machine = {0x14C: "x86 (32位)", 0x8664: "x64 (64位)"}.get(pe.FILE_HEADER.Machine, "未知")
oh = pe.OPTIONAL_HEADER
print(f"架构: {machine}    链接器: {oh.MajorLinkerVersion}.{oh.MinorLinkerVersion}")

# ── 3. 节区表 + 熵值 ──
# 熵 = 数据的"混乱度"（0~8）：普通代码 5~6.5；>7 基本就是加密/压缩 → 加壳铁证
print("-" * 56)
print(f"{'节名':10s} {'大小(KB)':>10s} {'熵':>6s}  判读")
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode(errors="replace") or "(无名)"
    size_kb = s.Misc_VirtualSize / 1024
    ent = s.get_entropy()
    verdict = "加密/压缩特征!" if ent > 7 else ("偏高，存疑" if ent > 6.6 else "正常数据")
    print(f"{name:10s} {size_kb:10,.0f} {ent:6.2f}  {verdict}")

# ── 4. Rich 头：MSVC 专属的"编译器身份证" ──
print("-" * 56)
try:
    rich = pe.parse_rich_header()
    if not rich or not rich.get("values"):
        print("Rich 头: 无（可能被抹除，或非 MSVC 工具链编译）")
    else:
        # Rich 头里的记录是 (产品ID, 版本号) 对，产品 ID 对应微软内部工具编号
        tools = {}
        vals = rich["values"]
        for v in vals:
            prod, build = v >> 16, v & 0xFFFF
            if prod and build:
                tools[(prod, build)] = tools.get((prod, build), 0) + 1
        known = {147: "C/C++ 编译器 cl.exe", 162: "链接器", 163: "链接器",
                 1: "导入库", 255: "调试器组件"}
        print(f"Rich 头: 有，{len(tools)} 种工具指纹")
        for (prod, build), n in sorted(tools.items()):
            print(f"  产品ID {prod:3d} ({known.get(prod, '?'):18s}) 版本 {build}  x{n}")
except Exception as e:
    print(f"Rich 头解析失败: {e}")
