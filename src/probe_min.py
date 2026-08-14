# ============================================================
# probe_min.py — 定位 Flash 里 29050 是谁写的（最小复现）
#
# 实验A: 只发 0x12(上变频=26550)，等 1 秒 → 读 Flash
# 实验B: 只发 0x0E(下变频=17250)，等 1 秒 → 读 Flash
#
# 判定：
#   A 后 lo_tx=26550，B 后变 29050 → 0x0E 固件写默认值（模块行为）
#   A 后就是 29050               → 0x12 命令/固化异常（需要查代码）
#   A、B 后都正常                → 29050 另有来源
#
# 每个实验同时打印实际发送帧，可逐字节核对无 29050。
# ============================================================

from Device import KaUDC004A
from Device.frame import pack_bits
from Device.crc16 import crc16_ccitt
import time

COM_PORT = 'COM4'   # ← 按实际串口号修改

dut = KaUDC004A(COM_PORT)


def show_send_frame(fcode, freq):
    """打印将要发送的帧（不含串口 IO）"""
    body = pack_bits([fcode, 0, freq], [8, 24, 16])
    frame = KaUDC004A.FRAME_HEAD + body
    crc = crc16_ccitt(frame)
    full = frame + bytes([crc >> 8, crc & 0xFF])
    print(f'  发送帧: {full.hex(" ").upper()}')


print('== 实验A: 只发上变频 0x12 = 26550，不发下变频 ==')
show_send_frame(0x12, 26550)
dut.set_lo('up', 26550)
time.sleep(1.0)   # 等固化
f = dut.read_flash()
print(f'  1秒后 Flash lo_tx = {f["lo_tx_mhz"]}')
print(f'  运行值 lo_up      = {dut.query_lo()["lo_up_mhz"]}')

print()
print('== 实验B: 只发下变频 0x0E = 17250 ==')
show_send_frame(0x0E, 17250)
dut.set_lo('down', 17250)
time.sleep(1.0)
f = dut.read_flash()
print(f'  1秒后 Flash lo_tx = {f["lo_tx_mhz"]}   ← 若变 29050，就是这条命令写的')

dut.close()
print('实验结束，串口已关闭')
