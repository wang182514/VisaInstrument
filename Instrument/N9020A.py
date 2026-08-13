# ============================================================
# N9020A — Keysight N9020A MXA 频谱分析仪（SA/NF/PN 三模式）
#
# 对应 C# 版 Instruments/KeysightN9020A.cs（方法名 snake_case 一一对应）
# 通信：TCP SCPI，端口 5025，命令以 \n 结尾
#
# 方法按模式分组，前缀指示所属模式：
#   sa_*   SA 模式（频谱分析，含 ACPR）
#   nf_*   NF 模式（噪声系数）
#   pn_*   PN 模式（相位噪声）
#
# 用法：
#   sa = N9020A('192.168.1.102')
#   sa.set_mode_sa()
#   print(sa.sa_marker_peak())
#   sa.close()
# ============================================================

import time

from .ScpiInstrument import ScpiInstrument


class N9020A(ScpiInstrument):
    """Keysight N9020A 频谱分析仪"""

    def __init__(self, ip: str, timeout_ms: int = 30000):
        super().__init__(f'TCPIP0::{ip}::5025::SOCKET', timeout_ms)

    # ---- 模式切换 ----

    def set_mode_sa(self) -> None:
        """切到 SA 模式（频谱分析）"""
        self.write(':INST SA')

    def set_mode_nf(self) -> None:
        """切到 NF 模式（噪声系数）"""
        self.write(':INST:SEL NFIGURE')

    def set_mode_pn(self) -> None:
        """切到 PN 模式（相位噪声）"""
        self.write(':INST PNOISE')

    # ---- 通用 ----

    def load_state(self, name: str) -> None:
        """调用仪器内保存的状态模板"""
        self.write('*CLS')
        self.write(f':MMEM:LOAD:STAT "{name}"')
        self.query('*OPC?')  # 等模板加载完成

    def check_error(self) -> str:
        """查询错误队列（正常返回 +0,"No error"）"""
        return self.query(':SYST:ERR?')

    def clear_markers(self) -> None:
        """清除所有标记（失败也无所谓，忽略异常）"""
        try:
            self.write(':CALC:MARK:AOFF')
        except Exception:
            pass

    def wait_for_complete(self) -> None:
        """阻塞等待仪器完成所有待处理操作 (*OPC?)"""
        self.query('*OPC?')

    def screenshot(self, save_path: str) -> None:
        """截取频谱仪屏幕，保存为本地 PNG 文件"""
        tmp = 'tmp_screenshot.png'
        self.write(f':MMEM:STOR:SCR "{tmp}"')  # 仪器内先存一张临时截图
        self.query('*OPC?')
        time.sleep(0.5)  # 等待文件写入完成

        # IE488.2 二进制块（#<digit><count><数据>）由 pyvisa 自动解析
        data = self._instr.query_binary_values(
            f':MMEM:DATA? "{tmp}"', datatype='B', container=bytes)
        with open(save_path, 'wb') as f:
            f.write(data)

    # ---- SA 模式 — 频谱分析 ----

    def sa_configure_mhz(self, start: float, stop: float, rbw: float,
                         vbw: float, ref_level: float, trace_type: str = 'WRIT') -> None:
        """配置 SA 模式扫频（MHz 单位）

        trace_type: WRIT(清屏重写,默认) / MAXHold(最大值保持) / AVERage(平均)
        """
        self.write(f':SENS:FREQ:STAR {start:.3f}MHz')
        self.write(f':SENS:FREQ:STOP {stop:.3f}MHz')
        self.write(f':SENS:BAND:RES {rbw:.0f}KHz')
        self.write(f':SENS:BAND:VID {vbw:.0f}KHz')
        self.write(f':DISP:WIND:TRAC:Y:RLEV {ref_level:.0f}dBm')
        self.write(f':TRAC1:TYPE {trace_type}')
        self.write(':INIT:CONT ON')

    def sa_set_offset(self, offset_db: float) -> None:
        """设置参考电平偏移 (dB)，用于射频线缆损耗补偿"""
        self.write(f':DISP:WIND1:TRAC:Y:RLEV:OFFS {offset_db:.2f}')

    def sa_marker_peak(self):
        """峰值搜索：返回 (频率 Hz, 幅度 dBm)"""
        self.write(':CALC:MARK1:STAT ON')
        self.write(':CALC:MARK1:MAX')
        time.sleep(0.1)
        freq = self.query_number('CALC:MARK1:X?')
        amp = self.query_number('CALC:MARK1:Y?')
        return freq, amp

    def sa_marker_ptp(self) -> float:
        """峰峰值标记：返回当前 trace 最大-最小差值 (dB)"""
        self.write(':CALC:MARK1:PTP')
        return self.query_number(':CALC:MARK1:Y?')

    def sa_marker_noise(self, freq_mhz: float, wait_sec: float = 3.0) -> float:
        """噪底标记：在指定频率点开启噪声功能，返回功率密度 (dBm/Hz)"""
        self.write(':CALC:MARK:AOFF')                # 先清所有标记
        self.write(':CALC:MARK1:STAT ON')
        self.write(f':CALC:MARK1:X {freq_mhz:.0f}MHz')
        self.write(':CALC:MARK1:FUNC NOIS')          # 开启噪声标记功能
        time.sleep(wait_sec)                         # 等仪器计算
        return self.query_number(':CALC:MARK1:Y?')

    def read_trace(self):
        """读取当前迹线 Y 轴数据（返回 float 列表）"""
        resp = self.query(':TRAC:DATA? TRACE1')
        return [float(x) for x in resp.split(',')]

    def read_acp(self):
        """读取 ACPR 结果：返回 (主信道功率 dBm, 下邻道 dBc, 上邻道 dBc)"""
        parts = self.query('read:acp?').split(',')
        if len(parts) < 3:
            return float('nan'), float('nan'), float('nan')
        return float(parts[0]), float(parts[1]), float(parts[2])

    # ---- NF 模式 — 噪声系数 ----

    def nf_init_cal(self) -> None:
        """启动噪声系数校准"""
        self.write(':NFIG:CAL:INIT')
        self.query('*OPC?')

    def nf_is_calibrated(self) -> bool:
        """查询噪声系数校准是否完成（True = 已校准）"""
        return self.query(':NFIG:CAL:STAT?') == '1'

    def nf_init_measurement(self) -> None:
        """启动单次噪声系数测量"""
        self.write(':INIT:CONT ON')
        self.write(':INIT:IMM')
        self.query('*OPC?')

    def nf_prepare_markers(self) -> None:
        """解除标记耦合并清除标记（测量前的准备）"""
        self.write(':CALC:NFIG:MARK:COUP OFF')
        self.write(':CALC:NFIG:MARK:AOFF')

    def nf_set_marker(self, marker: int, trace: int, freq_ghz: float) -> float:
        """在指定频率点设标记并读取噪声系数 (dB)

        marker: 标记号 1-4，trace: 迹线号 1-4（2 = 增益迹线）
        """
        self.write(f':CALC:NFIG:MARK{marker}:STAT ON')
        self.write(f':CALC:NFIG:MARK{marker}:TRAC TRAC{trace}')
        self.write(f':CALC:NFIG:MARK{marker}:X {freq_ghz:.2f}GHz')
        time.sleep(0.05)
        return self.query_number(f':CALC:NFIG:MARK{marker}:Y?')

    # ---- PN 模式 — 相位噪声 ----

    def pn_set_center_freq(self, ghz: float) -> None:
        """设置中心频率 (GHz)"""
        self.write(f':FREQ:CENT {ghz:.3f}GHz')

    def pn_init_measurement(self) -> None:
        """启动单次相位噪声测量

        注意：仪器完成测量可能需 120s 以上（见速查手册第六章），
        若此处的 *OPC? 超时报错，请先调用 set_timeout_ms(120000)，
        测量完成后再调回。
        """
        self.write(':INIT:CONT OFF')
        self.write(':INIT:IMM')
        self.query('*OPC?')

    def pn_read_spot(self, marker: int):
        """读取指定标记点的相位噪声：返回 (频率 Hz, 噪声 dBc/Hz)"""
        freq = self.query_number(f':CALC:LPLot:MARK{marker}:X?')
        noise = self.query_number(f':CALC:LPLot:MARK{marker}:Y?')
        return freq, noise
