# ============================================================
# GPP4323 — 固纬 GWINSTEK GPP-4323 四通道可编程直流电源
#
# 对应 C# 版 Instruments/Gpp4323.cs（方法名 snake_case 一一对应）
# 通信：USB 虚拟串口，9600 8N1，命令以 \n 结尾
#
# 设计：整机 = 一个 Gpp4323 对象，四个通道 ch1~ch4
#   四通道共享同一串口连接，指令带通道号后缀，无需切换通道。
#
# 指令规则（见 C# 项目 docs/PowerSupply_SCPI_速查手册.md）：
#   - 输出控制：:OUTP{ch} On / :OUTP{ch} Off
#   - 电压/电流设置：VOLT{ch} <v> / CURR{ch} <a>（无冒号前缀、两位小数）
#   - 电压/电流测量：:MEAS{ch}:VOLT? / :MEAS{ch}:CURR?
#
# 用法：
#   gpp = Gpp4323('COM11')
#   gpp.ch1.set_voltage(12.0)
#   gpp.ch1.set_output(True)
#   print(gpp.ch1.measure_voltage())
#   gpp.close()
# ============================================================

from .ScpiInstrument import ScpiInstrument


class Gpp4323(ScpiInstrument):
    """GWINSTEK GPP-4323 四通道可编程直流电源"""

    def __init__(self, com_port: str, baud_rate: int = 9600, timeout_ms: int = 3000):
        # pyvisa-py 在 Windows 上会自动给资源串加 COM 前缀
        # （ASRL3::INSTR → COM3），所以资源串只写端口号数字。
        # 这里把 'COM3' 归一化为 '3'，传 'COM3' 或 '3' 均可。
        port_num = com_port.upper().replace('COM', '')
        super().__init__(f'ASRL{port_num}::INSTR', timeout_ms)
        self._instr.baud_rate = baud_rate

        # 四个通道共享同一串口连接，只差在通道号后缀
        self.ch1 = _Channel(self, 1)
        self.ch2 = _Channel(self, 2)
        self.ch3 = _Channel(self, 3)
        self.ch4 = _Channel(self, 4)


class _Channel:
    """单通道视图：无状态，仅拼命令后缀并通过宿主发出"""

    def __init__(self, host: Gpp4323, ch: int):
        self._host = host
        self._ch = ch

    def set_output(self, on: bool) -> None:
        """开启/关闭本通道输出"""
        self._host.write(f':OUTP{self._ch} {"On" if on else "Off"}')

    def set_voltage(self, volts: float) -> None:
        """设置本通道目标电压（伏特）"""
        self._host.write(f'VOLT{self._ch} {volts:.2f}')

    def set_current(self, amps: float) -> None:
        """设置本通道电流上限（安培）"""
        self._host.write(f'CURR{self._ch} {amps:.2f}')

    def measure_voltage(self) -> float:
        """测量本通道当前实际电压（伏特）"""
        return self._host.query_number(f':MEAS{self._ch}:VOLT?')

    def measure_current(self) -> float:
        """测量本通道当前实际电流（安培）"""
        return self._host.query_number(f':MEAS{self._ch}:CURR?')
