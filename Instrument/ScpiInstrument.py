# ============================================================
# ScpiInstrument — SCPI 仪器公共基类
# （对应 C# 版 ScpiInstrument.cs + TcpConnection + SerialConnection）
#
# pyvisa 已经封装了底层通信（TCP/串口连接、终止符、超时、
# IE488.2 二进制块解析），所以基类只需要做三件事：
#   1. 打开 VISA 资源，设置终止符和超时
#   2. 提供 write / query / query_number 三个收发方法
#   3. 提供 close 释放连接
#
# 子类只写仪器特有的 SCPI 命令，完全不接触 pyvisa 细节。
# ============================================================

import pyvisa

# 全局唯一的 VISA 资源管理器（整个程序只需要一个）
# '@py' = 纯 Python 后端，无需安装 NI-VISA；若已安装 NI-VISA，
# 把参数去掉即可使用系统后端（功能更全）
_rm = pyvisa.ResourceManager('@py')


class ScpiInstrument:
    """SCPI 仪器基类 — 持有 pyvisa 仪器句柄，提供基础收发"""

    def __init__(self, resource: str, timeout_ms: int = 3000):
        """打开仪器资源并配置通信参数

        resource: VISA 资源字符串，例如
            'TCPIP0::192.168.1.90::5025::SOCKET'  TCP 仪器
            'ASRLCOM11::INSTR'                    串口仪器
        """
        self._instr = _rm.open_resource(resource)
        self._instr.read_termination = '\n'   # 响应以换行结尾
        self._instr.write_termination = '\n'  # 命令以换行结尾
        self._instr.timeout = timeout_ms      # 单次收发超时 (ms)

    # ---- 收发 ----

    def write(self, cmd: str) -> None:
        """发送 SCPI 命令（只发不收）"""
        self._instr.write(cmd)

    def query(self, cmd: str) -> str:
        """发送查询命令并返回完整响应（已去除终止符）"""
        return self._instr.query(cmd).strip()

    def query_number(self, cmd: str) -> float:
        """发送查询并把响应转为数字；解析失败返回 NaN
        （对应 C# 版 double.TryParse 的容错行为）"""
        try:
            return float(self.query(cmd))
        except ValueError:
            return float('nan')

    def query_idn(self) -> str:
        """查询仪器身份 *IDN?（连接后首先验证）"""
        return self.query('*IDN?')

    def set_timeout_ms(self, timeout_ms: int) -> None:
        """调整单次收发超时 (ms)。

        个别操作耗时很长（如频谱仪 PN 测量 *OPC? 可达 120s 以上），
        执行前把超时调大，完成后调回，即可不影响其他快速操作。
        """
        self._instr.timeout = timeout_ms

    # ---- 释放 ----

    def close(self) -> None:
        """关闭与仪器的连接"""
        self._instr.close()
