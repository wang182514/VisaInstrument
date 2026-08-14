%Applied-Wave Inc
%detect connected device
addpath('.\UART');
addpath('.\General');
COM_Port_Name='com4'; %设备管理器中查询设备的串口号
UART_Init;
%%
%温度查询
clc
KaUDC004A.FCode=hex2dec('0C');
SetKaUDC004A;
%%
%下变频本振切换控制
clc
KaUDC004A.FCode=hex2dec('0E');
KaUDC004A.LO=19250; % 16750MHz、17250MHz、18250MHz、19250MHz
SetKaUDC004A;
%%
%上变频本振切换控制
clc
KaUDC004A.FCode=hex2dec('12');
KaUDC004A.LO=28050; % 26550MHz、27400,28050,29050
SetKaUDC004A;
%%
%上下变频本振查询
clc;
KaUDC004A.FCode=hex2dec('13');
SetKaUDC004A;

%%
%上变频衰减控制
clc;     
KaUDC004A.FCode=hex2dec('14');
KaUDC004A.UCAtten=2; %0-10  
SetKaUDC004A;
%%
%上下变频衰减查询
clc;
KaUDC004A.FCode=hex2dec('16');
SetKaUDC004A;
%%
%版本回读
clc
KaUDC004A.FCode=hex2dec('0B');
SetKaUDC004A;
%%
%DAC设置
clc;
KaUDC004A.FCode=hex2dec('F1');
KaUDC004A.DACch=3; %TxBand1-0,TxBand2-1，TxBand3-2,TxBand4-3,
KaUDC004A.DACcode1=2245; %I  0-4096
KaUDC004A.DACcode2=2210; %Q
SetKaUDC004A;
%%
%发射增益90
clc;
KaUDC004A.FCode=hex2dec('F4');
KaUDC004A.UCAtten=8; %0-10
SetKaUDC004A
%%
%接收增益调整
clc;
KaUDC004A.FCode=hex2dec('F5');
KaUDC004A.DCAtten=0; %0-10
SetKaUDC004A;


%%
%读flash
clc
KaUDC004A.FCode=hex2dec('FA');
SetKaUDC004A;
