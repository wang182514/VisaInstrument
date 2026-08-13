# ============================================================
# PSW8027E — 固纬 GWINSTEK PSW-8027 单通道可编程直流电源
#
# 对应 C# 版 Instruments/PSW8027E.cs（方法名 snake_case 一一对应）
# 通信：TCP SCPI，端口 2268，命令以 \n 结尾
#
# 用法：
#   pwr = PSW8027E('192.168.1.11')
#   pwr.set_output(True)
#   print(pwr.measure_voltage())
#   pwr.close()
# ============================================================

import time

from .ScpiInstrument import ScpiInstrument


class PSW8027E(ScpiInstrument):
    """GWINSTEK PSW-8027 可编程直流电源"""

    def __init__(self, ip: str, port: int = 2268, timeout_ms: int = 3000):
        super().__init__(f'TCPIP0::{ip}::{port}::SOCKET', timeout_ms)

    # ---- 输出控制 ----

    def set_output(self, on: bool) -> None:
        """开启/关闭电源输出（发送后等 200ms 让仪器执行）"""
        self.write(f'OUTP {1 if on else 0}')
        time.sleep(0.2)

    # ---- 电压 / 电流设置 ----

    def set_voltage(self, volts: float) -> None:
        """设置目标电压（伏特）"""
        self.write(f'SOUR:VOLT {volts:.3f}')

    def set_current(self, amps: float) -> None:
        """设置电流上限（安培）"""
        self.write(f'SOUR:CURR {amps:.3f}')

    # ---- 电压 / 电流测量 ----

    def measure_voltage(self) -> float:
        """测量当前实际电压（伏特）"""
        return self.query_number('MEAS:VOLT?')

    def measure_current(self) -> float:
        """测量当前实际电流（安培）"""
        return self.query_number('MEAS:CURR?')
