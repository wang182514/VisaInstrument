function [crc_high, crc_low] = crc16_big_endian(data)
% CRC16 计算函数 (X^16 + X^12 + X^5 +1, 初始值0xFFFF, poly=0x1021)
% 按大端字节序输出CRC校验值
% 输入:
%   data: 输入数据，uint8类型数组
% 输出:
%   crc_high: CRC校验值的高字节 (uint8)
%   crc_low: CRC校验值的低字节 (uint8)

% CRC参数配置
polynomial = uint16(hex2dec('1021'));  % 多项式: X^16 + X^12 + X^5 +1
initial_value = uint16(hex2dec('FFFF')); % 初始值
final_xor = uint16(hex2dec('0000'));   % 最终异或值
%reverse_input = false;                % 不反转输入
%reverse_output = false;               % 不反转输出

% 初始化CRC寄存器
crc = uint16(initial_value);

% 预计算CRC查找表
crc_table = zeros(1, 256, 'uint16');
for i = 0:255
    crc_temp = bitshift(uint16(i), 8);
    for j = 0:7
        if bitand(crc_temp, uint16(hex2dec('8000'))) ~= 0
            crc_temp = bitxor(bitshift(crc_temp, 1), polynomial);
        else
            crc_temp = bitshift(crc_temp, 1);
        end
    end
    crc_table(i+1) = crc_temp;
end

% 计算CRC
for byte = data
    idx = bitxor(bitshift(crc, -8), byte) + 1;
    crc = bitxor(bitshift(crc, 8), crc_table(idx));
end

% 应用最终异或值
crc = bitxor(crc, final_xor);

% 分离为高字节和低字节（大端序）
crc_high = uint8(bitshift(bitand(crc, uint16(hex2dec('FF00'))), -8));
crc_low = uint8(bitand(crc, uint16(hex2dec('00FF'))));
end