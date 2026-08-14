# ============================================================
# frame — 二进制帧位打包工具（变频模块帧协议通用）
#
# 对应 MATLAB 版 General/GenerateFrame.m：
#   把"数值 + 位宽"列表按位拼接成大端字节流。
#   总位长不是 8 的倍数时，在高位（左侧）补零。
#
# 例: pack_bits([0x0E, 0, 19250], [8, 24, 16])
#     → b'\x0e\x00\x00\x00\x4b\x32'   （0x4B32 = 19250）
# ============================================================


def pack_bits(elements: list, widths: list) -> bytes:
    """按位宽把数值列表打包成字节串（大端序）

    elements: 数值列表（负数钳位为 0，超出位宽上限钳位为最大值）
    widths:  与 elements 一一对应的位宽列表
    """
    if len(elements) != len(widths):
        raise ValueError('elements 与 widths 长度不一致')

    bits = ''
    for value, width in zip(elements, widths):
        # 越界钳位（与 MATLAB 版 GenerateFrame 一致）
        if value < 0:
            value = 0
        elif value > 2 ** width - 1:
            value = 2 ** width - 1

        # 转二进制字符串，左侧补零到 width 位
        bin_str = bin(value)[2:]
        bits += '0' * (width - len(bin_str)) + bin_str

    # 总位长不是 8 的倍数时，在高位补零
    pad = (-len(bits)) % 8
    bits = '0' * pad + bits

    # 每 8 位转一个字节
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
