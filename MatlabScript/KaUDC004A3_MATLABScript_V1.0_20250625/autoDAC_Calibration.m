%% DAC自动调节IQ — 四频段校准
% 基于 autoDAC.m 框架
% 使用前修改: COM口号、频谱仪IP

clc
fprintf('===== DAC I/Q 自动校准 =====\n');
fprintf('开始时间: %s\n', datestr(now, 'HH:MM:SS'));

%% 环境初始化
% 清理旧连接 + 串口 + 频谱仪
fprintf('\n--- 清理旧连接 ---\n');
mxas = instrfind;
if ~isempty(mxas)
    n = length(mxas);
    fclose(mxas);
    delete(mxas);
    fprintf('已关闭 %d 个旧连接\n', n);
else
    fprintf('无旧连接\n');
end

% 串口
fprintf('\n--- 初始化串口 ---\n');
addpath('.\UART');
addpath('.\General');
COM_Port_Name = 'com9';             % ★ 确认串口号
fprintf('尝试打开串口: %s\n', COM_Port_Name);
try
    UART_Init;
    fprintf('串口初始化完成: %s, %d\n', COM.Port, COM.BaudRate);
catch ME
    fprintf('*** 串口初始化失败: %s\n', ME.message);
    return;
end

% 频谱仪
fprintf('\n--- 连接频谱仪 ---\n');
IP_SA = "192.168.1.50";            % ★ 确认频谱仪IP
fprintf('目标IP: %s\n', IP_SA);
try
    SA = visa('rs', sprintf('TCPIP0::%s::inst0::INSTR', IP_SA));
    SA.InputBufferSize = 2000000;
    SA.OutputBufferSize = 2000000;
    SA.Timeout = 10;
    fopen(SA);
    fprintf(SA, '*CLS');
    idn = strtrim(query(SA, '*IDN?'));
    fprintf('频谱仪已连接: %s\n', idn);
catch ME
    fprintf('*** 频谱仪连接失败: %s\n', ME.message);
    return;
end

fprintf('\n--- 频谱仪初始设置 ---\n');
fprintf(SA, 'INST:SEL SPECTRUM');
fprintf(SA, 'FREQ:SPAN 500MHz');
fprintf(SA, ':CALC:MARK1:STAT ON');
fprintf('Span=500MHz, Marker1=ON\n');
pause(0.5);

%% 参数配置
LO_GHz   = [26.55, 27.40, 28.05, 29.05];  % 本振 GHz (频谱仪)
LO_MHz   = [26550, 27400, 28050, 29050];   % 本振 MHz (TR组件)
DACch    = [0,     1,     2,     3];        % DAC通道
I_init   = [2286,  2260,  2247,  2237];     % I 历史均值
Q_init   = [2148,  2140,  2153,  2197];     % Q 历史均值

limit    = -65;        % 目标阈值 dBm
STEP_C   = 40;         % 粗扫步长
STEP_F   = 15;         % 精扫步长
WAIT_DAC = 0.15;       % DAC稳定等待 (秒)
WAIT_SA  = 0.10;       % 频谱仪读数余量 (秒)
SA_READ_TIMEOUT = 5;   % 未使用，仅为兼容调用

fprintf('\n参数: limit=%ddBm, 粗扫步长=%d, 精扫步长=%d\n', limit, STEP_C, STEP_F);
fprintf('      WAIT_DAC=%.2fs, WAIT_SA=%.2fs\n', WAIT_DAC, WAIT_SA);

% 结果存储
rI = zeros(1,4); rQ = zeros(1,4); rPk = zeros(1,4);

%% 逐频段校准
for band = 1:4
    fprintf('\n========== Band%d (%.2fGHz, LO=%dMHz, ch=%d) ==========\n', ...
        band, LO_GHz(band), LO_MHz(band), DACch(band));
    
    % 切换本振
    KaUDC004A.FCode = hex2dec('12');
    KaUDC004A.LO    = LO_MHz(band);
    SetKaUDC004A;
    pause(0.5);
    
    % 查询锁定
    KaUDC004A.FCode = hex2dec('13');
    SetKaUDC004A;
    pause(0.2);
    
    % 频谱仪中心频率
    fprintf(SA, sprintf('FREQ:CENT %.2fGHz', LO_GHz(band)));
    pause(0.2);
    
    % 初始值测试
    I = I_init(band);
    Q = Q_init(band);
    KaUDC004A.FCode    = hex2dec('F1');
    KaUDC004A.DACch    = DACch(band);
    KaUDC004A.DACcode1 = I;
    KaUDC004A.DACcode2 = Q;
    SetKaUDC004A;
    pause(WAIT_DAC);
    
    pk = readPeak(SA, WAIT_SA, SA_READ_TIMEOUT);
    fprintf('初始: I=%d, Q=%d, peak=%.1f dBm\n', I, Q, pk);
    
    if pk < limit
        fprintf('已达标，跳过\n');
        rI(band)=I; rQ(band)=Q; rPk(band)=pk;
        continue;
    end
    
    fprintf('开始优化 (差 %.1f dB)...\n', pk - limit);
    
    % ---- 粗扫 I ----
    fprintf('粗扫I (固定Q=%d)...\n', Q);
    best_I = I; best_pk = pk;
    for vi = max(0,I-200):STEP_C:min(4096,I+200)
        KaUDC004A.DACcode1 = vi; KaUDC004A.DACcode2 = Q; SetKaUDC004A;
        pause(WAIT_DAC);
        p = readPeak(SA, WAIT_SA, SA_READ_TIMEOUT);
        if p < best_pk, best_pk = p; best_I = vi; end
    end
    I = best_I; pk = best_pk;
    KaUDC004A.DACcode1 = I; KaUDC004A.DACcode2 = Q; SetKaUDC004A; pause(WAIT_DAC);
    fprintf('  I=%d, pk=%.1f\n', I, pk);
    if pk < limit, fprintf('达标\n'); rI(band)=I; rQ(band)=Q; rPk(band)=pk; continue; end
    
    % ---- 粗扫 Q ----
    fprintf('粗扫Q (固定I=%d)...\n', I);
    best_Q = Q; best_pk = pk;
    for vq = max(0,Q-200):STEP_C:min(4096,Q+200)
        KaUDC004A.DACcode1 = I; KaUDC004A.DACcode2 = vq; SetKaUDC004A;
        pause(WAIT_DAC);
        p = readPeak(SA, WAIT_SA, SA_READ_TIMEOUT);
        if p < best_pk, best_pk = p; best_Q = vq; end
    end
    Q = best_Q; pk = best_pk;
    KaUDC004A.DACcode1 = I; KaUDC004A.DACcode2 = Q; SetKaUDC004A; pause(WAIT_DAC);
    fprintf('  Q=%d, pk=%.1f\n', Q, pk);
    if pk < limit, fprintf('达标\n'); rI(band)=I; rQ(band)=Q; rPk(band)=pk; continue; end
    
    % ---- 精扫 I ----
    fprintf('精扫I (固定Q=%d)...\n', Q);
    best_I = I; best_pk = pk;
    for vi = max(0,I-60):STEP_F:min(4096,I+60)
        KaUDC004A.DACcode1 = vi; KaUDC004A.DACcode2 = Q; SetKaUDC004A;
        pause(WAIT_DAC);
        p = readPeak(SA, WAIT_SA, SA_READ_TIMEOUT);
        if p < best_pk, best_pk = p; best_I = vi; end
    end
    I = best_I; pk = best_pk;
    KaUDC004A.DACcode1 = I; KaUDC004A.DACcode2 = Q; SetKaUDC004A; pause(WAIT_DAC);
    fprintf('  I=%d, pk=%.1f\n', I, pk);
    
    % ---- 精扫 Q ----
    fprintf('精扫Q (固定I=%d)...\n', I);
    best_Q = Q; best_pk = pk;
    for vq = max(0,Q-60):STEP_F:min(4096,Q+60)
        KaUDC004A.DACcode1 = I; KaUDC004A.DACcode2 = vq; SetKaUDC004A;
        pause(WAIT_DAC);
        p = readPeak(SA, WAIT_SA, SA_READ_TIMEOUT);
        if p < best_pk, best_pk = p; best_Q = vq; end
    end
    Q = best_Q; pk = best_pk;
    KaUDC004A.DACcode1 = I; KaUDC004A.DACcode2 = Q; SetKaUDC004A; pause(WAIT_DAC);
    fprintf('  Q=%d, pk=%.1f\n', Q, pk);
    
    rI(band)=I; rQ(band)=Q; rPk(band)=pk;
end

%% 写入并验证 — 最后一个频段的最优值
KaUDC004A.FCode    = hex2dec('F1');
KaUDC004A.DACch    = DACch(4);
KaUDC004A.DACcode1 = rI(4);
KaUDC004A.DACcode2 = rQ(4);
SetKaUDC004A;
pause(WAIT_DAC);
pk_final = readPeak(SA, WAIT_SA, SA_READ_TIMEOUT);

%% 结果
fprintf('\n========== 结果 ==========\n');
for band = 1:4
    s = '✅'; if rPk(band) >= limit, s = '❌'; end
    fprintf('Band%d  I=%d  Q=%d  peak=%.1f dBm  %s\n', band, rI(band), rQ(band), rPk(band), s);
end

%% 清理
fclose(SA); delete(SA); clear SA;
fprintf('\n频谱仪已断开\n');

% ============================================================
function pk = readPeak(vSA, vWaitSA, ~)
    if vSA.BytesAvailable > 0
        flushinput(vSA);
    end
    fprintf(vSA, ':CALC:MARK1:MAX');
    pause(vWaitSA);
    pk = str2double(query(vSA, ':CALC:MARK1:Y?'));
end
