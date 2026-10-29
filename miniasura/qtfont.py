# V2.8 字体引导 —— offscreen / minimal 平台下 Qt 不读系统字体（实测字体族 0，中文全方框）。
# native（正式运行）下字体库非空，本函数原样返回、不改系统默认字体（零风险）。
# 不把 TTF 拷进仓库（msyh 19MB），只引用系统字体路径；一个都找不到时静默跳过，不阻断启动。
import os

from PySide6.QtGui import QFont, QFontDatabase

# Windows / macOS / Linux 常见中文字体，按优先级
CANDIDATES = ("C:/Windows/Fonts/msyh.ttc",       # 微软雅黑（Win7+）
              "C:/Windows/Fonts/simhei.ttf",     # 黑体
              "C:/Windows/Fonts/simsun.ttc",     # 宋体
              "/System/Library/Fonts/PingFang.ttc",
              "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")


def ensure_cjk_font(app):
    """保证 app 能显示中文：字体库已可用则不动；为空（offscreen）才显式加载系统中文 TTF。
    返回当前字体族名（找不到返回 ""，调用方据此判断，不抛异常）。"""
    if QFontDatabase.families():
        return QFont().family()          # native：跟随系统默认（Windows = Microsoft YaHei UI）
    for path in CANDIDATES:
        if not os.path.exists(path):
            continue
        fid = QFontDatabase.addApplicationFont(path)
        fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
        if fams:
            app.setFont(QFont(fams[0], 10))
            return fams[0]
    return ""
