# from os import path, makedirs
# import csv
from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_pressure import *

from datetime import datetime
#import schedule
import time


class Yoctopuce():
    def __init__(self, handle, logfile = 'yoctolog_'+datetime.now().strftime('%Y%m%d')+'.csv', layout=None):
        # logger class with init and update methods
        # input: logger's name/handle (METEO...), log file w/ extension, parent's layout

        # file name and dir
        self.log_file = logfile

        errmsg = YRefParam()
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
        #if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
            # use YAPI.RegisterHub("127.0.0.1", errmsg) if dev is connected to the same pc
            # if this failed, try YAPI.RegisterHub("usb", errmsg)
            sys.exit("init error :" + errmsg.value)
        try:
            self.temperature = YTemperature.FindTemperature(handle+'.temperature')

            self.tempFound = True
            self.tempstatus = ""
        except Exception as e:
            self.tempFound = False
            print(e)
            self.tempstatus = "Temp. sensor error."

        try:
            self.humidity = YHumidity.FindHumidity(handle+'.humidity')

            self.humFound = True
            self.humstatus = ""
        except Exception as e:
            self.humFound= False
            print(e)
            self.humstatus = "Humidity sensor error."

        try:
            self.pressure = YPressure.FindPressure(handle+'.pressure')
            self.presFound = True
            self.presstatus = ""
        except Exception as e:
            self.presFound= False
            print(e)
            self.presstatus = "Humidity sensor error."

        # init time array in main 
        self.times = [datetime.now().timestamp()]
        # init TPH arrays in main 
        self.Tvals=[self.temperature.get_currentValue()]
        self.Pvals=[self.pressure.get_currentValue()]
        self.Hvals=[self.humidity.get_currentValue()]


    def measure(self):
        currentT= float(self.temperature.get_currentValue())
        currentH= float(self.humidity.get_currentValue())
        currentP= float(self.pressure.get_currentValue())

        return currentT, currentH, currentP

    
if __name__ == "__main__":
    
    loggername_mossbauer = 'METEOMK2-2377A2'
    Y = Yoctopuce(loggername_mossbauer)

    T_list = []
    H_list = []
    P_list = []
    for i in range(3):
        T, P, H = Y.measure()
        print(T, P, H)
        T_list.append(T)
        P_list.append(P)
        H_list.append(H)
        time.sleep(1)

    print(T_list, H_list, P_list)

    
 