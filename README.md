# VisaInstrument — Python + PyVISA 仪器控制

基于 **PyVISA** 实现 SCPI 仪器控制的学习项目，覆盖 4 台常用测试仪器。与 C# 版项目（`D:\Project\Csharp\Demo`）方法一一对应，适合对照学习两种语言在仪器控制上的实现差异。

## 目录结构

```
VisaInstrument/
├── main.py                    # PyVISA 入门示例（资源发现、连接、收发）
└── Instrument/                # 仪器类包
    ├── __init__.py            # 包导出 + 类名对照表
    ├── ScpiInstrument.py      # 基类：打开资源、终止符/超时、write/query
    ├── PSW8027E.py            # 固纬 PSW-8027 单通道电源（TCP :2268）
    ├── GPP4323.py             # 固纬 GPP-4323 四通道电源（USB 串口 9600 8N1）
    ├── N9020A.py              # Keysight N9020A 频谱仪（TCP :5025，SA/NF/PN）
    └── SMU200A.py             # R&S SMU200A 信号源（TCP :5025）
```

## 环境准备

```bash
python -m venv .venv
.venv/Scripts/pip install pyvisa pyvisa-py pyserial
```

| 依赖 | 作用 |
| --- | --- |
| `pyvisa` | VISA 资源管理（连接、收发、超时、终止符） |
| `pyvisa-py` | 纯 Python 后端，无需安装 NI-VISA |
| `pyserial` | 串口资源支持（GPP-4323） |

> 本项目的 `ScpiInstrument` 基类使用 `ResourceManager('@py')` 纯 Python 后端；
> 若已安装 NI-VISA，把基类里的 `'@py'` 参数去掉即可使用系统后端。

## 快速开始

```python
from Instrument import N9020A, SMU200A, PSW8027E, Gpp4323

# 频谱仪：峰值搜索 + 截图
sa = N9020A('192.168.1.102')
sa.set_mode_sa()
freq, amp = sa.sa_marker_peak()
print(f'峰值: {freq/1e6:.3f} MHz, {amp:.2f} dBm')
sa.screenshot('trace.png')
sa.close()

# 信号源：点频输出
vsg = SMU200A('192.168.1.90')
vsg.set_cw(1200.0, -14.0)   # 频率 MHz + 功率 dBm
vsg.rf_on()
vsg.close()

# 单通道电源
pwr = PSW8027E('192.168.1.11')
pwr.set_output(True)
print(pwr.measure_voltage(), 'V')
pwr.close()

# 四通道电源：四个通道共享串口连接
gpp = Gpp4323('COM11')
gpp.ch1.set_voltage(12.0)
gpp.ch1.set_output(True)
print(gpp.ch1.measure_voltage(), 'V')
gpp.close()
```

## 设计说明

- **基类只有一层薄封装**：PyVISA 已封装 TCP/串口连接、终止符、超时、
  IE488.2 二进制块解析（截图），基类只做资源打开 + 三个收发方法
- **构造即连接**：`__init__` 中 `open_resource`，连接失败立刻抛异常（PyVISA 默认行为）
- **`query_number()` 容错**：解析失败返回 `NaN`，对应 C# 版 `double.TryParse` 的容错行为
- **`set_timeout_ms()`**：个别操作耗时很长（如 N9020A 的 PN 测量 `*OPC?` 需 ≥120s），
  执行前调大超时、完成后调回

## 与 C# 版（Demo 项目）对照

| C#（Demo 项目） | Python（本项目） | 说明 |
| --- | --- | --- |
| `ScpiInstrument.cs` + `TcpConnection.cs` + `SerialConnection.cs` | `ScpiInstrument.py` | 通信层：C# 约 600 行手写 → PyVISA 约 60 行 |
| 接口层（`IPowerSupply` 等 6 个文件） | 无（Python 鸭子类型） | 运行时多态隐式完成 |
| `PSW8027E.cs` / `Gpp4323.cs` | `PSW8027E.py` / `GPP4323.py` | 方法 snake_case 一一对应 |
| `KeysightN9020A.cs` | `N9020A.py` | 同上 |
| `RsSmu200A.cs` | `SMU200A.py` | 同上 |

**命名对照规则**：C# PascalCase → Python snake_case（每个大写字母处拆分、转小写、下划线连接），
如 `SaMarkerPeak()` → `sa_marker_peak()`。

**SCPI 命令来源**：所有命令以 C# 项目 `docs/` 下实测确认过的速查手册为准
（`N9020A_SCPI_速查手册.md` / `SMU200A_SCPI_速查手册.md` / `PowerSupply_SCPI_速查手册.md`）。

## 注意事项

1. **GPP-4323 串口独占**：串口为独占资源，同一时刻只能一个进程打开；四通道共享串口，指令串行发送
2. **GPP-4323 指令格式**：电压/电流设置无冒号前缀、两位小数（如 `VOLT1 12.00`）；其余指令带冒号
3. **N9020A PN 测量**：`*OPC?` 等待可能超过 120s，超时先 `set_timeout_ms(120000)` 再测量
4. **安全顺序**：测试结束先关闭输出再断开连接
5. 本项目的使用对象为实验室/学习环境，连接参数（IP / COM 口）随现场设备枚举变化
