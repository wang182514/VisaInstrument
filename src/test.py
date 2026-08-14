import time

from Instrument import *

gpp = Gpp4323('COM3')
gpp.ch1.set_voltage(12.0)
gpp.ch1.set_output(True)
time.sleep(2)
print(gpp.ch1.measure_voltage())
gpp.ch1.set_output(False)

gpp.close()
