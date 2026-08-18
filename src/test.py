import sys
from pathlib import Path
print(sys.path[0])
# 确保从任意 IDE/目录运行都能找到项目根目录下的 Instrument、Device 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print(sys.path[0])

import time

from Instrument import *

gpp = Gpp4323('COM3')
gpp.ch1.set_voltage(12.0)
gpp.ch1.set_output(True)
time.sleep(2)
print(gpp.ch1.measure_voltage())
gpp.ch1.set_output(False)

gpp.close()

