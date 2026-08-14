# Device 包 — 被测射频组件控制类集合
#
# 与 Instrument/（测试仪器）平行：组件走自定义二进制帧协议，
# 仪器走 SCPI 文本协议，两者在测试项层组合使用。
#
# 文件对照 MATLAB 版：
#   KaUDC004A.py ← KaUDC004A_CTRL.m + SetKaUDC004A.m + parseUartBack.m
#   crc16.py     ← General/crc16_big_endian.m
#   frame.py     ← General/GenerateFrame.m
#
# 用法：
#   from Device import KaUDC004A

from .KaUDC004A import KaUDC004A
