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

    # ---- 系统类（一档补全）----

    def preset(self) -> None:
        """复位仪器到出厂默认状态（*RST）"""
        self.write('*RST')

    def clear_status(self) -> None:
        """清空状态寄存器和错误队列（*CLS）"""
        self.write('*CLS')

    def save_state(self, name: str) -> None:
        """保存当前仪器状态到内部存储（:MMEM:STOR:STAT）"""
        self.write(f':MMEM:STOR:STAT "{name}"')
        self.query('*OPC?')

    def query_opc(self) -> str:
        """阻塞等待仪器所有待处理操作完成（*OPC?），返回 '+1'"""
        return self.query('*OPC?')

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

    # ---- SA 模式 — 独立 setter（一档补全）----
    # sa_configure_mhz 是一次配齐；下面这些是流程中需要细调单参数时用的

    def sa_set_span_mhz(self, span_mhz: float) -> None:
        """单独设置 SA 扫描跨度 (MHz)"""
        self.write(f':SENS:FREQ:SPAN {span_mhz:.3f}MHz')

    def sa_set_rbw_khz(self, rbw_khz: float) -> None:
        """单独设置分辨率带宽 RBW (kHz)"""
        self.write(f':SENS:BAND:RES {rbw_khz:.0f}KHz')

    def sa_set_vbw_khz(self, vbw_khz: float) -> None:
        """单独设置视频带宽 VBW (kHz)"""
        self.write(f':SENS:BAND:VID {vbw_khz:.0f}KHz')

    def sa_set_ref_level_dbm(self, level_dbm: float) -> None:
        """单独设置参考电平 (dBm)"""
        self.write(f':DISP:WIND:TRAC:Y:RLEV {level_dbm:.0f}dBm')

    def sa_set_atten_db(self, atten_db: float) -> None:
        """单独设置 RF 衰减 (dB)"""
        self.write(f':SENS:POW:RF:ATT {atten_db:.1f}')

    def sa_set_preamp(self, on: bool) -> None:
        """开关前置放大器"""
        self.write(f':POW:GAIN {"ON" if on else "OFF"}')

    def sa_set_sweep_time_sec(self, sec: float) -> None:
        """单独设置扫描时间 (秒)"""
        self.write(f':SENS:SWE:TIME {sec:.3f}')

    def sa_set_sweep_count(self, n: int) -> None:
        """单独设置扫描次数（ACPR 模板常用，>1 时仪器自动平均）"""
        self.write(f':SENS:SWE:COUN {n}')

    def sa_set_detector(self, mode: str) -> None:
        """设置检波器：POS/NEG/AVER/SAMP"""
        self.write(f':DET:TRAC1 {mode}')

    def sa_set_trigger_source(self, source: str) -> None:
        """设置触发源：IMM(自由)/VIDeo/EXT/IF"""
        self.write(f':TRIG:SOUR {source}')

    def sa_set_cf_step(self, freq_hz: float) -> None:
        """设置中心频率步进大小（Hz）— 与键盘上箭头增减频率对应"""
        self.write(f':CALC:MARK:STEP {freq_hz:.0f}')

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

    # ---- SA 模式 — Marker 高级操作（二档补全）----

    def marker_on(self, marker: int) -> None:
        """打开指定 marker (1~12)"""
        self.write(f':CALC:MARK{marker}:STAT ON')

    def marker_off(self, marker: int) -> None:
        """关闭指定 marker"""
        self.write(f':CALC:MARK{marker}:STAT OFF')

    def set_marker_freq_hz(self, marker: int, freq_hz: float) -> None:
        """把指定 marker 设到给定频率 (Hz)"""
        self.write(f':CALC:MARK{marker}:X {freq_hz:.0f}')

    def read_marker_x(self, marker: int) -> float:
        """读取指定 marker 的 X 轴（频率 Hz）"""
        return self.query_number(f':CALC:MARK{marker}:X?')

    def read_marker_y(self, marker: int) -> float:
        """读取指定 marker 的 Y 轴（幅度 dBm）"""
        return self.query_number(f':CALC:MARK{marker}:Y?')

    def peak_search_next(self) -> float:
        """峰值搜索下一个最高点，返回 Y 轴 (dBm)。谐波测量必用"""
        self.write(':CALC:MARK:MAX:NEXT')
        time.sleep(0.1)
        return self.query_number(':CALC:MARK1:Y?')

    def delta_marker_on(self, marker: int, ref_marker: int) -> None:
        """把指定 marker 设为与参考 marker 的差值"""
        self.write(f':CALC:DELT{marker}:STAT ON')
        self.write(f':CALC:DELT{marker}:MARK {ref_marker}')

    def set_delta_marker_freq_hz(self, marker: int, freq_hz: float) -> None:
        """设置 delta marker 的频率（相对参考 marker 的偏移）"""
        self.write(f':CALC:DELT{marker}:X {freq_hz:.0f}')

    def read_delta_marker_y(self, marker: int) -> float:
        """读取 delta marker 的 Y 轴（与参考的幅度差 dB）"""
        return self.query_number(f':CALC:DELT{marker}:Y?')

    def read_xdb_bw(self) -> float:
        """N dB 带宽测量：返回当前 marker 处的带宽 (Hz)，C/N 与占用带宽必用"""
        return self.query_number(':CALC:BAND:RES?')

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
