

from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_pressure import *
from datetime import datetime




class Yoctopuce:
	def __init__(self, address):

		errmsg = YRefParam()
		if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
			sys.exit("init error :" + errmsg.value)

		print(address)
		
		self.temperature = YTemperature.FindTemperature(address +'.temperature')
		self.humidity = YHumidity.FindHumidity(address+'.humidity')
		self.pressure = YPressure.FindPressure(address+'.pressure')

	def __del__(self):
		print("Closing yoctopuce")

        #if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
            # use YAPI.RegisterHub("127.0.0.1", errmsg) if dev is connected to the same pc
            # if this failed, try YAPI.RegisterHub("usb", errmsg)



            
        


if __name__=='__main__':

	address = 'METEOMK2-2377A2'
	address = 'METEOMK2-23CD30'
	address = 'METEOMK2-23CAC1'
	address = 'METEOMK2-23B47A'

	yct1= yoctopuce_class(address)

	temp  = yct1.temperature.get_currentValue()
	temp  = yct1.humidity.get_currentValue()
	temp  = yct1.pressure.get_currentValue()

