# ============================================================
# KaUDC004A — Ka 波段上/下变频模块控制（被测组件）
#
# 对应 MATLAB 版 KaUDC004A_CTRL.m + General/SetKaUDC004A.m +
# General/parseUartBack.m（组合成一个类，方法一一对应功能码）
# 通信：UART 串口 115200 8N1，自定义二进制帧协议（非 SCPI）
#
# 帧格式（发送，12 字节；读 Flash 响应 45 字节）：
#   AA 55 0C 00 | FCode | 数据... | CRCH CRCL
#   └──帧头──┘   └─功能码┘  └─载荷┘  └─CRC16(0x1021) 大端─┘
#
# 用法：
#   dut = KaUDC004A('COM9')
#   dut.set_lo('down', 19250)          # 下变频本振 19250 MHz
#   print(dut.temperature())           # (温度℃, 电压V)
#   dut.close()
# ============================================================

import serial

from .crc16 import crc16_ccitt
from .frame import pack_bits


class KaUDC004A:
    """Ka 波段上/下变频模块（UART 二进制帧协议控制）"""

    # ---- 帧头（Head1 Head0 FrameSize Rsd）----
    FRAME_HEAD = bytes([0xAA, 0x55, 0x0C, 0x00])

    # ---- 功能码 ----
    FC_RESET = 0x0A        # 复位
    FC_VERSION = 0x0B      # 版本回读
    FC_TEMP = 0x0C         # 温度查询
    FC_LO_DOWN = 0x0E      # 下变频本振切换
    FC_LO_UP = 0x12        # 上变频本振切换
    FC_LO_QUERY = 0x13     # 上下变频本振查询（含锁定状态）
    FC_ATTEN_UP = 0x14     # 上变频衰减控制
    FC_ATTEN_DOWN = 0x15   # 下变频衰减控制
    FC_ATTEN_QUERY = 0x16  # 上下变频衰减查询
    FC_DAC = 0xF1          # DAC 校准码设置
    FC_WRITE_FLASH = 0xF3  # 写 Flash（固化当前配置）
    FC_GAIN_TX = 0xF4      # 发射增益调整
    FC_GAIN_RX = 0xF5      # 接收增益调整
    FC_READ_FLASH = 0xFA   # 读 Flash（45 字节响应）

    # 查询类命令的载荷：FCode 后固定 5 字节 0
    QUERY_PAYLOAD = bytes(5)

    def __init__(self, com_port: str, baud_rate: int = 115200, timeout: float = 1.0):
        """打开串口（默认 115200 8N1，与 MATLAB 版 UART_Init 一致）"""
        self._sp = serial.Serial(com_port, baud_rate, timeout=timeout)

    # ============================================================
    # 帧收发
    # ============================================================

    def _exchange(self, fcode: int, body: bytes = None) -> bytes:
        """发送一帧并读回响应

        - 查询类命令 body 为 None：帧 = 头 + FCode + 5 字节 0
        - 控制类命令 body 由 pack_bits 生成（首字节即 FCode）
        - 响应以 AA 55 开头校验，否则抛异常
        """
        if body is None:
            frame = self.FRAME_HEAD + bytes([fcode]) + self.QUERY_PAYLOAD
        else:
            frame = self.FRAME_HEAD + body

        # 追加 CRC16（大端：高字节在前）
        crc = crc16_ccitt(frame)
        self._sp.write(frame + bytes([crc >> 8, crc & 0xFF]))

        # 读响应：读 Flash 45 字节，其余 12 字节
        length = 45 if fcode == self.FC_READ_FLASH else 12
        back = self._sp.read(length)
        if len(back) != length:
            raise TimeoutError(f'响应超时: 期望 {length} 字节, 收到 {len(back)} 字节')
        if back[0] != 0xAA or back[1] != 0x55:
            raise ValueError('收到的帧格式不正确')

        # 12 字节响应尾部 2 字节为 CRC16 大端（已与 MATLAB 抓包比对验证），
        # 读 Flash 的 45 字节响应布局不同，暂不校验
        if length == 12:
            calc = crc16_ccitt(back[:-2])
            if calc != back[-2] * 256 + back[-1]:
                raise ValueError(f'响应 CRC 校验失败: 期望 {back[-2]:02X}{back[-1]:02X}, 实际 {calc:04X}')
        return back

    @staticmethod
    def _be16(byte1: int, byte2: int) -> int:
        """两个字节按大端序拼成 16 位整数"""
        return byte1 * 256 + byte2

    # ============================================================
    # 系统类
    # ============================================================

    def reset(self) -> bool:
        """复位变频分机（FCode 0A），返回是否成功"""
        back = self._exchange(self.FC_RESET)
        return back[5] == 0xFF

    def version(self) -> int:
        """查询版本号（FCode 0B），返回 32 位整数"""
        back = self._exchange(self.FC_VERSION)
        b = back[5:9]
        return (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]

    def temperature(self):
        """查询模块温度和电压（FCode 0C）

        返回: (温度℃, 电压V)
        负数温度按 MATLAB 版规则解析：字节值 >=128 时温度 = 128 - 值
        """
        back = self._exchange(self.FC_TEMP)
        code = back[5]
        temp = 128 - code if code >= 128 else code
        volt = self._be16(back[8], back[9]) * 3.3 / 4096
        return float(temp), round(volt, 3)

    # ============================================================
    # 本振控制
    # ============================================================

    def set_lo(self, direction: str, freq_mhz: int) -> int:
        """切换本振频率（FCode 0E 下变频 / 12 上变频）

        direction: 'down' 下变频 / 'up' 上变频
        下变频可选: 16750 / 17250 / 18250 / 19250 MHz
        上变频可选: 26550 / 27400 / 28050 / 29050 MHz
        返回: 仪器确认的本振频率 (MHz)

        【实测固件行为】0x0E（下变频）会把当时的下变频+上变频本振
        一起固化进 Flash；0x12（上变频）只改运行值、不写 Flash。
        因此想让上变频本振进 Flash：先 set_lo('up', X) 再 set_lo('down', Y)，
        或两个都设完后调 write_flash()。
        """
        if direction == 'down':
            fcode = self.FC_LO_DOWN
        elif direction == 'up':
            fcode = self.FC_LO_UP
        else:
            raise ValueError("direction 只能是 'down' 或 'up'")

        body = pack_bits([fcode, 0, freq_mhz], [8, 24, 16])
        back = self._exchange(fcode, body)
        return self._be16(back[8], back[9])

    def query_lo(self) -> dict:
        """查询上下变频本振和锁定状态（FCode 13）

        返回: {'lo_up_mhz', 'lo_down_mhz', 'rx_locked', 'tx_locked', 'ref_locked'}
        注意: 第一条数据是上变频（发射）本振，第二条是下变频（接收）本振
        ——MATLAB 版两条均无标注，此映射由实物数据确认
        """
        back = self._exchange(self.FC_LO_QUERY)
        b = back[5:10]
        state = b[4]
        return {
            'lo_up_mhz': self._be16(b[0], b[1]),    # 第一条 = 上变频（发射）本振
            'lo_down_mhz': self._be16(b[2], b[3]),  # 第二条 = 下变频（接收）本振
            'rx_locked': bool(state & 1),    # bit0 接收锁定
            'tx_locked': bool(state & 2),    # bit1 发射锁定
            'ref_locked': bool(state & 4),   # bit2 参考锁定
        }

    # ============================================================
    # 衰减 / 增益控制
    # ============================================================

    def set_atten(self, side: str, db: float) -> float:
        """设置衰减 0~10 dB（FCode 14 上变频 / 15 下变频）

        注意编码方式：数值 ×10 后用 16 位传输（如 2.5dB → 25）
        返回: 仪器确认的衰减值 (dB)
        """
        if side == 'up':
            fcode = self.FC_ATTEN_UP
        elif side == 'down':
            fcode = self.FC_ATTEN_DOWN
        else:
            raise ValueError("side 只能是 'up' 或 'down'")

        body = pack_bits([fcode, 0, round(db * 10)], [8, 24, 16])
        back = self._exchange(fcode, body)
        return self._be16(back[8], back[9]) / 10

    def query_atten(self):
        """查询上下变频衰减值（FCode 16），返回 (上变频dB, 下变频dB)"""
        back = self._exchange(self.FC_ATTEN_QUERY)
        b = back[5:10]
        up = self._be16(b[0], b[1]) / 10
        down = self._be16(b[2], b[3]) / 10
        return up, down

    def set_gain(self, side: str, step: int) -> None:
        """增益调整 0~10（FCode F4 发射 / F5 接收）

        注意编码与 set_atten 不同：8 位直传（不 ×10），中间 32 位占位
        """
        if side == 'tx':
            fcode = self.FC_GAIN_TX
        elif side == 'rx':
            fcode = self.FC_GAIN_RX
        else:
            raise ValueError("side 只能是 'tx' 或 'rx'")

        body = pack_bits([fcode, 0, step], [8, 32, 8])
        self._exchange(fcode, body)

    # ============================================================
    # DAC / Flash
    # ============================================================

    def set_dac(self, channel: int, i_code: int, q_code: int) -> None:
        """I/Q 校准码写入（FCode F1）——本振泄漏抑制校准

        channel: 0~3 对应 TxBand1~4，同时对应上变频本振：
            0→26550, 1→27400, 2→28050, 3→29050 MHz
        i_code / q_code: I / Q 路校准码 0~4096（调节使 LO 峰值接近底噪）

        【固件行为】写入校准码的同时，固件会把上变频本振切换到
        channel 对应频段（便于直接在校准条件下观察频谱）。
        校准值存于模块 Flash，正式测试时 set_lo 切频段即自动生效。
        """
        body = pack_bits([self.FC_DAC, channel, i_code, q_code], [8, 8, 16, 16])
        self._exchange(self.FC_DAC, body)

    def write_flash(self) -> None:
        """写 Flash，把当前配置固化（FCode F3）"""
        self._exchange(self.FC_WRITE_FLASH)

    def read_flash(self) -> dict:
        """读 Flash 全部配置（FCode FA，45 字节响应）

        响应布局：帧头 4(第3字节=0x2D=45 帧长) + FCode 1 + 数据区 40 字节
        （45 字节响应无 CRC，与 12 字节响应不同——已与 MATLAB 抓包核实）

        注意：读的是 Flash 固化值（上电加载的配置），不是当前运行值；
        查当前本振/衰减请用 query_lo() / query_atten()。

        返回: 4 个频段的 I/Q DAC 码、收发本振、收发衰减、收发频率
        """
        back = self._exchange(self.FC_READ_FLASH)
        d = back[5:45]  # 40 字节数据区
        return {
            'band1_dac': (self._be16(d[0], d[1]), self._be16(d[2], d[3])),
            'band2_dac': (self._be16(d[4], d[5]), self._be16(d[6], d[7])),
            'band3_dac': (self._be16(d[8], d[9]), self._be16(d[10], d[11])),
            'band4_dac': (self._be16(d[12], d[13]), self._be16(d[14], d[15])),
            'lo_rx_mhz': self._be16(d[16], d[17]),
            'lo_tx_mhz': self._be16(d[18], d[19]),
            'rx_atten': d[20],
            'tx_atten': d[22],   # d[21] 为保留字节，跳过
            'rx_freq_mhz': self._be16(d[36], d[37]),
            'tx_freq_mhz': self._be16(d[38], d[39]),
        }

    # ============================================================
    # 释放
    # ============================================================

    def close(self) -> None:
        """关闭串口"""
        self._sp.close()


# ---- 协议中未实现的遗留功能码（待真机验证后补充）----
# 0x11 锁定查询   ：MATLAB 只在 parseUartBack 有解析、无发送分支
# 0x21 / 0x22     ：带 RF 频率的本振切换，主脚本未使用
# 0xA1 / 0xF2     ：单码 DAC / TxBand+增益码，主脚本未使用
