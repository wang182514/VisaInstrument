# ============================================================
# flash_probe.py — Flash 固化机制定案实验
#
# 背景：read_flash() 的 lo_tx 字段显示 29050，而运行值已是 26550。
# 4 轮实测数据指向两种可能机制，本脚本一次性区分：
#   假说A: 0x12 固化是异步的，连续执行时被打断 → 等待后固化成功
#   假说B: 0x0E 固化时 lo_tx 回填默认值 29050，与运行值无关
#
# 运行：python src/flash_probe.py，把输出贴回来即可。
# 注意：会真实修改模块的上变频本振与 Flash，跑完请确认状态。
# ============================================================

from Device import KaUDC004A
import time

COM_PORT = 'COM4'   # ← 按实际串口号修改

dut = KaUDC004A(COM_PORT)


def probe(name, action, wait_sec):
    """执行设置 → 可选等待 → 读 Flash 打印 lo_tx"""
    action()
    if wait_sec:
        time.sleep(wait_sec)
    f = dut.read_flash()
    print(f'{name:<28} → lo_tx = {f["lo_tx_mhz"]}')


print('== 实验 1: 0x12(26550) 后立即读 vs 等待 1 秒 ==')
probe('0x12=26550 后立即读', lambda: dut.set_lo('up', 26550), 0)
probe('0x12=28050 后等1秒', lambda: dut.set_lo('up', 28050), 1.0)

print()
print('== 实验 2: 0x0E 之后 Flash 的 lo_tx 是否被回填 ==')
probe('0x0E=17250 后立即读', lambda: dut.set_lo('down', 17250), 0)

print()
print('== 实验 3: write_flash() 显式固化后 ==')
dut.set_lo('up', 26550)
dut.write_flash()
time.sleep(1.0)
f = dut.read_flash()
print(f'write_flash 后(up=26550)  → lo_tx = {f["lo_tx_mhz"]}')

dut.close()
print('实验结束，串口已关闭')
