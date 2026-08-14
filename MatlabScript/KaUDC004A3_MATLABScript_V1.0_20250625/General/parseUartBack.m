Fcode=UART_Back(5);
BackCode=[UART_Back(6) UART_Back(7) UART_Back(8) UART_Back(9) UART_Back(10)];
switch Fcode
    case hex2dec('0A') %复位
         if(BackCode(1)==255)
            fprintf('变频分机已经复位完成!\n')
         else
            fprintf('变频分机复位失败!\n')
         end
     
    case hex2dec('0B') %查询版本号
           fprintf('版本号：')
           %fprintf('%02X',BackCode(1:4));
           fprintf('%d\n',BackCode(1)*256*256*256+BackCode(2)*256*256+BackCode(3)*256+ BackCode(4));
           fprintf('\n')
    case hex2dec('0C') %温度查询
        if BackCode(1)>=128
          fprintf('模块温度为：%d℃\n',128-BackCode(1));
        else
          fprintf('模块温度为：%d℃\n',BackCode(1));  
        end
        fprintf('电压为：%dv\n',(BackCode(4)*256 + BackCode(5))*3.3/4096);
     case hex2dec('0E') %下变频本振切换控制帧
          fprintf('返回的LO频率为：%dMHz\n',BackCode(4)*256 + BackCode(5));
       
     case hex2dec('12') %上变频本振切换控制帧
         fprintf('返回的LO频率为：%dMHz\n',BackCode(4)*256 + BackCode(5));
    
     case hex2dec('13') %上下变频本振查询
         fprintf('返回的LO频率为：%dMHz\n',BackCode(1)*256 + BackCode(2));
         fprintf('返回的LO频率为：%dMHz\n',BackCode(3)*256 + BackCode(4));
         State=BackCode(5);
        if (bitand(State,2,'uint8')==2)
             fprintf('发射锁定\n');
         else
             fprintf('发射失锁\n')
         end
         
        if (bitand(State,1,'uint8')==1)
            fprintf('接收锁定\n');
         else
            fprintf('接收失锁\n')
        end
         if (bitand(State,4,'uint8')==4)
            fprintf('参考锁定\n');
         else
            fprintf('参考失锁\n')
         end
       
     case hex2dec('14') %上变频衰减控制
         fprintf('上变频衰减为：%.1fdB\n',(BackCode(4)*256 + BackCode(5))/10);
     
     case hex2dec('15') %上变频衰减控制
         fprintf('下变频衰减为：%.1fdB\n',(BackCode(4)*256 + BackCode(5))/10);
         
     case hex2dec('16') %上变频衰减控制
         fprintf('上变频衰减为：%.1fdB\n',(BackCode(1)*256 + BackCode(2))/10);
         fprintf('下变频衰减为：%.1fdB\n',(BackCode(3)*256 + BackCode(4))/10);
    
    case hex2dec('21') %下变频本振切换控制帧
          fprintf('返回的LO频率为：%dMHz\n',BackCode(4)*256 + BackCode(5));
          fprintf('返回的接收频率为：%dMHz\n',BackCode(2)*256 + BackCode(3));
     case hex2dec('22') %上变频本振切换控制帧
         fprintf('返回的LO频率为：%dMHz\n',BackCode(4)*256 + BackCode(5));
         fprintf('返回的发射频率为：%dMHz\n',BackCode(2)*256 + BackCode(3));
    
    case hex2dec('FA') %上变频衰减控制
         fprintf('BAND1_IDAC：%d\n',UART_Back(6)*256 + UART_Back(7));
         fprintf('BAND1_QDAC：%d\n',UART_Back(8)*256 + UART_Back(9));
         fprintf('BAND2_IDAC：%d\n',UART_Back(10)*256 + UART_Back(11));
         fprintf('BAND2_QDAC：%d\n',UART_Back(12)*256 + UART_Back(13));
         fprintf('BAND3_IDAC：%d\n',UART_Back(14)*256 + UART_Back(15));
         fprintf('BAND3_QDAC：%d\n',UART_Back(16)*256 + UART_Back(17));
         fprintf('BAND4_IDAC：%d\n',UART_Back(18)*256 + UART_Back(19));
         fprintf('BAND4_QDAC：%d\n',UART_Back(20)*256 + UART_Back(21));
         fprintf('接收本振频率：%d\n',UART_Back(22)*256 + UART_Back(23));
         fprintf('发射本振频率：%d\n',UART_Back(24)*256 + UART_Back(25));
         fprintf('接收衰减为：%d\n',UART_Back(26)); 
         fprintf('发射衰减为：%d\n',UART_Back(28));
         fprintf('接收频率：%d\n',UART_Back(42)*256 + UART_Back(43));
         fprintf('发射频率：%d\n',UART_Back(44)*256 + UART_Back(45));
         
     case hex2dec('11') %锁定查询
         
         if(BackCode(1)==hex2dec('FF'))
            fprintf('发射锁定\n');
         else
             fprintf('发射失锁\n')
         end
         
         if(BackCode(2)==hex2dec('FF'))
            fprintf('接收锁定\n');
         else
            fprintf('接收失锁\n')
         end
 
       
    otherwise
  
end