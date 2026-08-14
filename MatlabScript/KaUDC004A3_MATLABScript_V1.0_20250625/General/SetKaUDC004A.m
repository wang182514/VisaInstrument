FramePrefix=[hex2dec('AA') hex2dec('55') hex2dec('0C') hex2dec('00')]; %Head1 Head0 FrameSize Rsd

switch KaUDC004A.FCode
    case hex2dec('0A')
            fprintf('复位帧\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
    
     case hex2dec('0B')
            fprintf('版本回读\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
      case hex2dec('0C')
            fprintf('温度回读\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];       
        
    case hex2dec('0E')
            fprintf('下变频本振切换控制帧\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.LO];
            CtrlLength=[8 24 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);


            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
        
     case hex2dec('12')
            fprintf('上变频本振切换控制帧\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.LO];
            CtrlLength=[8 24 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];

            
         case hex2dec('13')
            fprintf('上下变频本振查询\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL]; 
        
      case hex2dec('14')
            fprintf('上变频衰减控制\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.UCAtten*10];
            CtrlLength=[8 24 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
        
        case hex2dec('15')
            fprintf('下变频衰减控制\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.DCAtten*10];
            CtrlLength=[8 24 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
            
         case hex2dec('16')
            fprintf('衰减查询\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL]; 
            
         case hex2dec('A1')
            fprintf('DAC设置\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.DACcode];
            CtrlLength=[8 24 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
          case hex2dec('F1')
            fprintf('DAC设置\n')
            CtrlData=[KaUDC004A.FCode KaUDC004A.DACch KaUDC004A.DACcode1 KaUDC004A.DACcode2];
            CtrlLength=[8 8 16 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
            
            case hex2dec('F2')
            fprintf('DAC设置\n')
            CtrlData=[KaUDC004A.FCode KaUDC004A.TxBand 0 KaUDC004A.Gaincode];
            CtrlLength=[8 8 16 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);
            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
            
           case hex2dec('F3')      
            fprintf('写Flash\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL]; 
            
            case hex2dec('F4')
            fprintf('上变频衰减控制\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.UCAtten];
            CtrlLength=[8 32 8];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
             case hex2dec('F5')
            fprintf('下变频衰减控制\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.DCAtten];
            CtrlLength=[8 32 8];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
            
            case hex2dec('21')
            fprintf('下变频本振切换控制帧\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.RF KaUDC004A.LO];
            CtrlLength=[8 8 16 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);


            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
        
            case hex2dec('22')
            fprintf('上变频本振切换控制帧\n')
            CtrlData=[KaUDC004A.FCode 0 KaUDC004A.RF KaUDC004A.LO];
            CtrlLength=[8 8 16 16];
            CtrlBody = GenerateFrame(CtrlData,CtrlLength);

            CMD=[FramePrefix  CtrlBody];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL];
            
            case hex2dec('FA')      
            fprintf('读Flash\n')
            CMD=[FramePrefix KaUDC004A.FCode 0 0 0 0 0];
            [CRCH, CRCL]= crc16_big_endian(CMD);
            UART_Send = [CMD CRCH CRCL]; 

    otherwise
  
end


%================Send Data===============
fprintf('===================================')
fprintf('\n') 
fprintf('UART_Send = ')
fprintf('%02X ',UART_Send)
fprintf('\n')  

tic               
fwrite(COM,UART_Send,'uint8');


%===============Read Data=================
if (KaUDC004A.FCode==hex2dec('FA'))
   UART_Back=(fread(COM,40+5,'uint8')).'; 
else
UART_Back=(fread(COM,12,'uint8')).';
end
if(~isempty(UART_Back))
    fprintf('UART Back = ') 
    fprintf('%02X ',UART_Back);
    fprintf('\n') 
    fprintf('===================================')   
    fprintf('\n') 
    if(UART_Back(1)==hex2dec('AA') && UART_Back(2)==hex2dec('55') )
        parseUartBack;
    else
        fprintf('收到的帧格式不正确！\n')
    end
end

toc
