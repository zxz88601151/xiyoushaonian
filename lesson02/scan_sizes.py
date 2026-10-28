# 第 2 课脚本 2：扫描游戏目录，统计各类文件的磁盘体积
# 核心变化：上次数"个数"，这次算"字节数"——1 MB = 1024 * 1024 字节

import os

GAME_DIR = r"F:\WeGameApps\斗战神"

sizes = {}                                     # 字典这次存 "扩展名: 总字节数"

for root, dirs, files in os.walk(GAME_DIR):
    for name in files:
        path = os.path.join(root, name)        # 拼出完整路径才能查体积
        ext = os.path.splitext(name)[1].lower()
        sizes[ext] = sizes.get(ext, 0) + os.path.getsize(path)  # getsize 返回字节数

print("体积排行（前 10 名）：")
for ext, size in sorted(sizes.items(), key=lambda x: -x[1])[:10]:
    mb = size / 1024 / 1024                    # 字节转 MB
    print(f"  {ext or '(无扩展名)'} : {mb:,.1f} MB")

total = sum(sizes.values())
print(f"\n游戏目录总计：{total / 1024 / 1024:,.0f} MB（约 {total / 1024 / 1024 / 1024:.1f} GB）")
