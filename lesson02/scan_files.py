# 第 2 课脚本 1：扫描游戏目录，统计文件类型分布
# 运行方式：在终端里输入  python scan_files.py

import os                                      # 1. 导入 os 模块：Python 自带的"文件系统工具箱"

GAME_DIR = r"F:\WeGameApps\斗战神"              # 2. 要扫描的目录（r"" 表示原样字符串，反斜杠不转义）

stats = {}                                     # 3. 准备一个空字典，用来存 "扩展名: 数量"

for root, dirs, files in os.walk(GAME_DIR):    # 4. os.walk 递归走遍所有子目录
    for name in files:                         # 5. 每个目录里逐个看文件
        ext = os.path.splitext(name)[1].lower()  # 6. 取出扩展名（.dll、.pak...）并统一小写
        stats[ext] = stats.get(ext, 0) + 1     # 7. 计数 +1（get 的意思是：没有就默认 0）

print("文件类型统计（前 15 名）：")              # 8. 排序后打印，多的在前
for ext, count in sorted(stats.items(), key=lambda x: -x[1])[:5]:
    print(f"  {ext or '(无扩展名)'} : {count} 个")

total = sum(stats.values())
print(f"\n合计 {total} 个文件，{len(stats)} 种扩展名")
