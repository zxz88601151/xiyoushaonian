# MiniAsura §1 一键构建：复用第 3 课的 mypack.py，把 assets/ 打成 assets.mpak
# 用法: python build.py
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lesson03"))
import mypack

if __name__ == "__main__":
    mypack.pack(os.path.join(HERE, "assets"))
