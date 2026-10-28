# 第 5 课脚本：PE 文件透视镜 —— 列出一个 exe/dll 的导入表（服务清单）
# 用法: python pe_inspect.py <文件路径>

import pefile
import sys

path = sys.argv[1]                                 # 命令行参数 = 要透视的文件
pe = pefile.PE(path)                               # 解析 PE 结构（只读，不改文件）

print(f"文件: {path}")
print(f"类型: {'EXE 程序' if pe.is_exe() else 'DLL 库'}")
print(f"编译时间戳: {pe.FILE_HEADER.TimeDateStamp}（1970 年起的秒数，可用在线工具转日期）")
print("-" * 50)

total = 0                                          # 统计一共导入多少个函数
print("导入表（它需要的每一个 DLL 和函数）：")
for entry in pe.DIRECTORY_ENTRY_IMPORT:            # 逐个 DLL 遍历
    dll = entry.dll.decode()                       # DLL 名是字节串，转成文字
    funcs = entry.imports                          # 这个 DLL 里它要用的函数列表
    total += len(funcs)
    print(f"  {dll:30s} {len(funcs):3d} 个函数")
    for imp in funcs[:3]:                          # 每个只展示前 3 个函数名，意思一下
        name = imp.name.decode() if imp.name else "(按序号导入)"
        print(f"      · {name}")
    if len(funcs) > 3:
        print(f"      ... 还有 {len(funcs) - 3} 个")

print("-" * 50)
print(f"合计从 {len(pe.DIRECTORY_ENTRY_IMPORT)} 个 DLL 导入 {total} 个函数")
