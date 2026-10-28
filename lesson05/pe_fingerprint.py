# 第 5 课彩蛋：PE 身份鉴定 —— 链接器版本 + 节区熵值 + Rich 头
# 用法: python pe_fingerprint.py <文件路径>   （只读，不改文件）

import datetime
import sys

import pefile

path = sys.argv[1]
pe = pefile.PE(path)

oh = pe.OPTIONAL_HEADER
ts = pe.FILE_HEADER.TimeDateStamp
print(f"文件: {path}")
print(f"链接器版本: {oh.MajorLinkerVersion}.{oh.MinorLinkerVersion:02d}")
print(f"时间戳: {ts} -> {datetime.datetime.fromtimestamp(ts, datetime.timezone.utc):%Y-%m-%d %H:%M:%S} UTC")
print("-" * 62)
print(f"{'节名':10s} {'大小(KB)':>9s} {'熵':>6s}  判读")
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode(errors="replace")
    ent = s.get_entropy()
    if ent > 7.4:
        tag = "加密/压缩特征!"
    elif ent > 6.8:
        tag = "偏高存疑"
    else:
        tag = "正常"
    print(f"{name:10s} {s.SizeOfRawData / 1024:9.0f} {ent:6.2f}  {tag}")
print("-" * 62)

rich = getattr(pe, "RICH_HEADER", None)
if not rich:
    print("Rich 头: 无（非 MSVC 工具链，或已被抹掉）")
else:
    vals = rich.values
    # vals[0]=校验和, vals[1]=DanS 标记, 之后是 (工具id<<16 | build, 出现次数) 成对排列
    print(f"Rich 头: 有，共 {(len(vals) - 2) // 2} 条工具记录")
    for i in range(2, len(vals) - 1, 2):
        prod = vals[i] >> 16
        build = vals[i] & 0xFFFF
        count = vals[i + 1]
        if prod == 0 and build == 0:
            continue
        vs = {21022: "VS2008 RTM", 30729: "VS2008 SP1"}.get(build, "")
        print(f"  工具 #{prod:#04x}  build={build}  {vs}  出现 {count} 次")
