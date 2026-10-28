# 第 3 课：迷你资源包 MPAK —— 打包器 + 解包器
# 用法:  python mypack.py pack   <文件夹>           → 生成 <文件夹>.mpak
#        python mypack.py unpack <文件.mpak> <目标文件夹>  → 还原所有文件

import os
import struct          # struct = Python 自带的"二进制打包工具"，能把数字变字节、字节变数字
import sys

MAGIC = b"MPAK"        # 魔数：咱们的格式身份证，模仿真 VFS 的 "vfs "

def pack(folder):
    files = []         # 先收集文件夹里所有文件的信息（名字 + 体积）
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            files.append((name, os.path.getsize(path)))

    out_path = folder.rstrip("/\\") + ".mpak"
    with open(out_path, "wb") as f:                # wb = 以二进制写模式打开
        # ── 1. 文件头：魔数 + 版本 + 文件数 ──
        f.write(MAGIC)
        f.write(struct.pack("<I", 1))              # <I = 小端序 32 位无符号整数
        f.write(struct.pack("<I", len(files)))

        # ── 2. 索引区：先算好每个文件数据在包里的位置(offset)，再写索引 ──
        header_size = 4 + 4 + 4                    # 魔数+版本+数量
        index_size = sum(2 + len(n.encode()) + 8 + 4 for n, _ in files)  # 名长+名+偏移+大小
        data_start = header_size + index_size      # 数据区从这儿开始

        offset = data_start
        for name, size in files:
            name_bytes = name.encode()             # 文件名转字节
            f.write(struct.pack("<H", len(name_bytes)))  # <H = 16 位整数（文件名长度）
            f.write(name_bytes)                          # 文件名本身
            f.write(struct.pack("<Q", offset))           # <Q = 64 位整数（数据在包里的位置）
            f.write(struct.pack("<I", size))             # 数据长度
            offset += size                               # 下一个文件的位置接着排

        # ── 3. 数据区：把每个文件的原始内容依次抄进去 ──
        for name, _ in files:
            with open(os.path.join(folder, name), "rb") as src:
                f.write(src.read())

    print(f"打包完成: {out_path}  共 {len(files)} 个文件")

def unpack(pack_path, out_dir):
    with open(pack_path, "rb") as f:
        if f.read(4) != MAGIC:                     # 先验魔数，格式不对就拒绝——真 VFS 也这么干
            sys.exit("不是 MPAK 文件！")
        version = struct.unpack("<I", f.read(4))[0]
        count = struct.unpack("<I", f.read(4))[0]

        os.makedirs(out_dir, exist_ok=True)        # 建输出目录
        for _ in range(count):                     # 逐条读索引
            name_len = struct.unpack("<H", f.read(2))[0]
            name = f.read(name_len).decode()       # 文件名转回文字
            offset = struct.unpack("<Q", f.read(8))[0]
            size = struct.unpack("<I", f.read(4))[0]
            here = f.tell()                        # 记住索引读到哪了
            f.seek(offset)                         # 直接跳到数据区该文件的位置
            data = f.read(size)                    # 只读这个文件那一段
            f.seek(here)                           # 跳回索引继续读下一条
            with open(os.path.join(out_dir, name), "wb") as dst:
                dst.write(data)
            print(f"  还原 {name}  ({size} 字节)")

    print(f"解包完成 → {out_dir}")

def read(pack_path, wanted):
    # 库函数：给程序调用，返回字节数据；找不到返回 None，不打印任何东西
    with open(pack_path, "rb") as f:
        f.read(4)                                    # 跳过魔数
        f.read(4)                                    # 跳过版本
        count = struct.unpack("<I", f.read(4))[0]
        for _ in range(count):                       # 扫索引找目标文件
            name_len = struct.unpack("<H", f.read(2))[0]
            name = f.read(name_len).decode()
            offset = struct.unpack("<Q", f.read(8))[0]
            size = struct.unpack("<I", f.read(4))[0]
            if name == wanted:                       # 找到了！
                f.seek(offset)                       # 直达数据区
                return f.read(size)
    return None                                       # 扫完索引都没有

def get(pack_path, wanted):
    data = read(pack_path, wanted)
    if data is None:
        print(f"包里没有叫 {wanted} 的文件")          # 扫完索引都没有 → 明确报告
    else:
        print(f"[{wanted}] 内容如下：")
        print(data.decode())                          # 按文字打印出来

if __name__ == "__main__":
    cmd = sys.argv[1]                              # 命令行第一个参数 = 动作 (pack/unpack)
    if cmd == "pack":
        pack(sys.argv[2])
    elif cmd == "unpack":
        unpack(sys.argv[2], sys.argv[3])
    elif cmd == "get":
        get(sys.argv[2], sys.argv[3])
    else:
        print("用法: pack <文件夹> | unpack <包> <目录> | get <包> <文件名>")
