# ============================================================
# probe_bisect.py — 定位"把本振改成 29050"的命令（逐条排查）
#
# 背景：test2 完整流程后，连运行值 lo_up 都变成 29050；
#       probe_min 证明 0x12/0x0E 干净 → 嫌疑在衰减/增益/DAC 命令。
#
# 方法：先设上变频 26550 并确认，然后逐个执行嫌疑命令，
#       每条命令后立即检查 Flash lo_tx 与运行值 lo_up。
#       哪条命令执行后变成 29050，元凶就是它。
# ============================================================

from Device import KaUDC004A
import time

COM_PORT = 'COM4'   # ← 按实际串口号修改

dut = KaUDC004A(COM_PORT)


def check(tag):
    """打印当前 Flash 固化值 + 运行值"""
    f = dut.read_flash()
    lo = dut.query_lo()['lo_up_mhz']
    bad = '  ← 元凶!' if (f['lo_tx_mhz'] == 29050 or lo == 29050) else ''
    print(f'{tag:<34} Flash lo_tx={f["lo_tx_mhz"]:<7} 运行值 lo_up={lo}{bad}')


# 基线：设置上变频 26550，等待固化
dut.set_lo('up', 26550)
time.sleep(1.0)
check('基线 (只设上变频 26550)')

# 逐条执行嫌疑命令
suspects = [
    ('0x14 上变频衰减 2.0dB', lambda: dut.set_atten('up', 2.0)),
    ('0x15 下变频衰减 1.5dB', lambda: dut.set_atten('down', 1.5)),
    ('0x16 衰减查询',         dut.query_atten),
    ('0xF4 发射增益 8',        lambda: dut.set_gain('tx', 8)),
    ('0xF5 接收增益 0',        lambda: dut.set_gain('rx', 0)),
    ('0xF1 DAC设置 3/2245/2210', lambda: dut.set_dac(3, 2245, 2210)),
]

for name, fn in suspects:
    fn()
    check(name)

dut.close()
print('排查结束，串口已关闭')
