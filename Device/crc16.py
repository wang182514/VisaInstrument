# ============================================================
# crc16 — CRC16-CCITT 校验（变频模块帧协议通用）
#
# 对应 MATLAB 版 General/crc16_big_endian.m：
#   多项式 poly = 0x1021（X^16 + X^12 + X^5 + 1）
#   初始值 init = 0xFFFF，最终异或 0x0000（即 CRC-16/CCITT-FALSE）
#   帧内按大端序：高字节在前
#
# 这里用"逐位算法"自己实现一遍（MATLAB 版是查表法），
# 两种算法结果相同，逐位版更直观、便于学习对照。
# ============================================================


def crc16_ccitt(data: bytes) -> int:
    """计算 CRC16-CCITT 校验值

    data: 待校验字节（帧头 + FCode + 数据，不含 CRC 本身）
    返回: 16 位校验值，调用方自行拆成高/低字节追加到帧尾
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        # 逐位处理 8 次：最高位为 1 时异或多项式
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
