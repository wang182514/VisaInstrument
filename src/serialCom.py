# ============================================================
# src/serialCom.py — 串口通信 4 个示例（线性脚本，无函数封装）
#
# pySerial 是 Python 的串口通信库，封装了 Windows/Linux 差异。
# 4 段由浅入深：① 打开 → ② 收发 → ③ 异常处理 → ④ 实际协议
#
# 运行方式：
#   python src/serialCom.py         全部示例依次运行（需连接 COM3 仪器）
#   按需注释/启用某些示例
# ============================================================

import sys
from pathlib import Path

# 确保能 import 项目根目录下的包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import serial
import time


# ============================================================
# ① 最简单的打开 — 打开串口，读一行，关掉
# ============================================================

print('=== 示例 1 ===')
port = serial.Serial('COM3', baudrate=9600, timeout=1)
line = port.readline()             # 阻塞读一个 \n（最多 1 秒）
print('收到:', line.decode('ascii', errors='replace'))
port.close()


# ============================================================
# ② 收发 — 写一帧，读一帧（多数仪器协议的标准流程）
# ============================================================

print('=== 示例 2 ===')
port = serial.Serial('COM3', baudrate=9600, timeout=1)
port.write(b'*IDN?\n')              # 写：bytes + 终止符 \n
time.sleep(0.1)                      # 给仪器反应时间（异步协议）
resp = port.readline().decode('ascii').strip()
print('仪器:', resp)
port.close()


# ============================================================
# ③ 异常处理 — 真实硬件可能丢包、断连、超时
# ============================================================

print('=== 示例 3 ===')
port = serial.Serial('COM3', baudrate=9600, timeout=1)
try:
    port.write(b'*IDN?\n')
    resp = port.readline().decode('ascii', errors='replace').strip()
    if not resp:
        raise TimeoutError('仪器没响应')
    print('仪器:', resp)
except serial.SerialException as e:
    print('串口错误:', e)
except TimeoutError as e:
    print('超时:', e)
finally:
    port.close()                     # 无论成功失败都关


# ============================================================
# ④ 实际协议 — 模拟 KaUDC004A 的 send/receive 流程
#    真实完整版见 Device/KaUDC004A.py（CRC16-CCITT + 解析）
# ============================================================

print('=== 示例 4 ===')

# ---- 帧格式 ----
HEAD = bytes([0xAA, 0x55, 0x0C, 0x00])  # 帧头 + 帧长

fcode = 0x0C                            # 温度查询
payload = bytes(5)                       # 查询类命令的 5 字节 0

body = bytes([fcode]) + payload
# 简化版校验（真实协议是 CRC16-CCITT）
checksum = (sum(HEAD + body) ^ 0xFF) & 0xFF
frame = HEAD + body + bytes([checksum])

port = serial.Serial('COM3', baudrate=115200, timeout=1)
try:
    port.write(frame)
    back = port.read(12)                # 响应固定 12 字节
    if len(back) != 12:
        raise TimeoutError(f'收到 {len(back)} 字节，期望 12')
    if back[:2] != bytes([0xAA, 0x55]):
        raise ValueError('帧头错误')
    print('温度:', back[5], '°C')
finally:
    port.close()


print()
print('全部示例执行完毕')