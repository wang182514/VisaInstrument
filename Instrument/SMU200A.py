# ============================================================
# SMU200A — R&S SMU200A 矢量信号源
#
# 对应 C# 版 Instruments/RsSmu200A.cs（方法名 snake_case 一一对应）
# 通信：TCP SCPI，端口 5025，命令以 \n 结尾
#
# 调制命令详见 C# 项目 docs/SMU200A_SCPI_速查手册.md 第「五、调制控制」。
#
# 用法：
#   vsg = SMU200A('192.168.1.90')
#   vsg.set_cw(1200.0, -14.0)
#   vsg.rf_on()
#   vsg.close()
# ============================================================

from .ScpiInstrument import ScpiInstrument


class SMU200A(ScpiInstrument):
    """R&S SMU200A 矢量信号源"""

    def __init__(self, ip: str, timeout_ms: int = 5000):
        super().__init__(f'TCPIP0::{ip}::5025::SOCKET', timeout_ms)
        # 连接后清空状态寄存器（对应 C# 版 OnConnected 钩子）
        self.write('*CLS')

    # ---- CW / RF 输出 ----

    def set_cw(self, freq_mhz: float, power_dbm: float) -> None:
        """设置点频输出：频率 (MHz) + 功率 (dBm)，并切到 CW 模式"""
        self.write(f'FREQ {freq_mhz:.3f}MHz')
        self.write(f'POW {power_dbm:.2f}dBm')
        self.write(':FREQ:MODE CW')

    def rf_on(self) -> None:
        """开启 RF 输出"""
        self.write('OUTP ON')

    def rf_off(self) -> None:
        """关闭 RF 输出"""
        self.write('OUTP OFF')

    def set_cw_mode(self) -> None:
        """切回点频 (CW) 模式"""
        self.write(':FREQ:MODE CW')

    # ---- 调制开关 ----

    def mod_on(self) -> None:
        """开启调制"""
        self.write(':MOD:STAT ON')

    def mod_off(self) -> None:
        """关闭调制"""
        self.write(':MOD:STAT OFF')

    # ---- 基带数字调制输出 ----

    def bb_on(self) -> None:
        """开启基带数字调制输出"""
        self.write(':SOUR:BB:DM:STAT ON')

    def bb_off(self) -> None:
        """关闭基带数字调制输出"""
        self.write(':SOUR:BB:DM:STAT OFF')

    # ---- 数字调制参数 ----

    def set_symbol_rate(self, symbol_rate: float) -> None:
        """设置符号速率"""
        self.write(f':SOURce:BB:DM:SRAT {symbol_rate}')

    def set_modulation_type(self, fmt: str) -> None:
        """设置调制类型，如 QPSK / PSK8 / QPSK45 / QEDG / P4QP"""
        self.write(f':SOURce:BB:DM:FORMat {fmt}')

    def set_filter_type(self, typ: str) -> None:
        """设置滤波器类型，如 RCOSine（升余弦）"""
        self.write(f':SOURce:BB:DM:FILTer:TYPE {typ}')

    def set_roll_off(self, roll_off: float) -> None:
        """设置滚降系数 (roll-off factor)，典型值 0.25"""
        self.write(f':SOURce:BB:DM:FILTer:PARameter:RCOSine {roll_off}')

    # ---- 扫频 ----

    def configure_sweep(self, start_ghz: float, stop_ghz: float, step_khz: float,
                        dwell_ms: float, power_dbm: float) -> None:
        """配置扫频模式（用于平坦度测试等需信号源自动扫频的场景）

        依次设置固定功率、起止频率、步进、驻留时间、线性/自动扫频，
        最后切到扫频模式。调用后如需回到点频，另调 set_cw_mode()。
        """
        self.write(f'POW {power_dbm:.2f}dBm')
        self.write(f'FREQ:STAR {start_ghz:.3f}GHz')
        self.write(f'FREQ:STOP {stop_ghz:.3f}GHz')
        self.write(f'SWE:STEP {step_khz:.0f}KHz')
        self.write(f'SWE:DWEL {dwell_ms:.0f}ms')
        self.write('SWE:SPAC LIN')
        self.write('SWE:MODE AUTO')
        self.write('FREQ:MODE SWE')

    # ---- 组合便捷 ----

    def configure_digital_mod(self, symbol_rate: float, fmt: str, roll_off: float) -> None:
        """一键配置数字调制：符号速率 + 调制类型 + 升余弦滤波器 + 滚降系数

        注意：只设参数，不开 BB 输出和调制——需另调 bb_on() / mod_on()。
        """
        self.set_symbol_rate(symbol_rate)
        self.set_modulation_type(fmt)
        self.set_filter_type('RCOSine')
        self.set_roll_off(roll_off)
