# ============================================================
# test2.py — KaUDC004A 变频模块实物联调测试
#
# 依次调用 KaUDC004A 类的各个功能并打印结果，
# 单项失败不中断，继续测下一项，便于逐条排查。
#
# 运行前：
#   1. 连接变频模块串口，确认串口号（设备管理器查询），
#      修改下面的 COM_PORT（MATLAB 版脚本用的是 com9）
#   2. 确认模块供电正常
# ============================================================

from Device import KaUDC004A
import time

COM_PORT = 'COM4'   # ← 按实际串口号修改，如 'COM3'


def run(name, func):
    """执行一项测试：成功打印结果，失败打印原因，不影响后续项"""
    try:
        print(f'{name} → {func()}')
    except Exception as e:
        print(f'{name} → 失败: {e}')


dut = KaUDC004A(COM_PORT)

# ---- 系统类（只读，先测）----
run('版本号      ', dut.version)
run('温度/电压   ', dut.temperature)

# ---- DAC 校准设置 ----
# 0xF1 写校准码时会把上变频本振切到 channel 对应频段（3→29050），
# 所以 DAC 设置放在本振设置之前，最后由 set_lo 确定测试频段。
run('DAC校准设置 ', lambda: dut.set_dac(3, 2245, 2210))

# ---- 衰减 / 增益 ----
run('上变频衰减  ', lambda: dut.set_atten('up', 2.0))
run('下变频衰减  ', lambda: dut.set_atten('down', 1.5))
run('衰减查询    ', dut.query_atten)
run('发射增益    ', lambda: dut.set_gain('tx', 8))
run('接收增益    ', lambda: dut.set_gain('rx', 0))

# ---- 本振控制（最后设置，避免被 DAC 命令重置）----
run('下变频本振  ', lambda: dut.set_lo('down', 17250))
run('上变频本振  ', lambda: dut.set_lo('up', 26550))
time.sleep(1.0)   # 等待固化完成
run('本振+锁定   ', dut.query_lo)   # 读当前运行值，实时正确
run('读Flash     ', dut.read_flash)  # 此时 Flash 应为本振最终值

# ---- 以下两项默认不执行，确认需要时取消注释 ----
# run('写Flash     ', dut.write_flash)  # ← 会把当前配置固化进 Flash，慎用
# run('复位       ', dut.reset)         # ← 复位变频分机

dut.close()
print('测试结束，串口已关闭')
