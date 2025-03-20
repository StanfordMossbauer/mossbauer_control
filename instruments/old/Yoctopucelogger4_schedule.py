from os import path, makedirs
import csv
from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_pressure import *

from datetime import datetime
import schedule
import time


class yoctopucelogger():
    def __init__(self, handle, logfile, layout=None):
        # logger class with init and update methods
        # input: logger's name/handle (METEO...), log file w/ extension, parent's layout

        # file name and dir
        self.log_file = logfile

        errmsg = YRefParam()

        if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
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


    def update(self):
        """Updates TPH and time. save to file."""
        try:
            currentT= self.temperature.get_currentValue()
            currentH=self.humidity.get_currentValue()
            currentP=self.pressure.get_currentValue()
            currenttime = datetime.now().timestamp()
            timedisplay= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except:
            YAPI.Sleep(1000)
            print('update error. try again...')
            currentT= self.temperature.get_currentValue()
            currentH=self.humidity.get_currentValue()
            currentP=self.pressure.get_currentValue()
            currenttime = datetime.now().timestamp()
            timedisplay= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        self.Tvals.append(currentT)
        self.Pvals.append(currentP)
        self.Hvals.append(currentH)
        self.times.append(currenttime)

        ## Save to file. Append if exists, otherwise create.
        if path.exists(self.log_file):
            type = 'a'
        else:
            type = 'w'
            with open(self.log_file, type, newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['time', 'temp [C]', 'RH [%]', 'P [mbar]'])

        with open(self.log_file, type, newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timedisplay, currentT, currentH, currentP])
           
        
def updateall(loggers, closingtime='0100'):
    ''' update loggers via schedule'''
    
    today =datetime.now()   
    for l in loggers:
        l.update()
        
    if today.strftime('%H%M')==closingtime:
        #clear the task every day at closing time 
        schedule.clear()
        print('cancelling at (mdHM)'+today.strftime('%m%d%H%M'))
        
        # cleaning up ...
        YAPI.UpdateDeviceList()
        YAPI.HandleEvents()
        sys.exit()
    

# new trap side: side/near input beam
logger2name = 'METEOMK2-23B50F'
# new trap: fiber
logger3name = 'METEOMK2-23CD30'
# new trap: output
logger4name = 'METEOMK2-23CAC1'
 # old trap logger w/ red extension cable
logger1name = 'METEOMK2-23B47A'

today =datetime.now()
# save to a sub folder
path_name = '/home/gravity/Data/'+ today.strftime('%Y%m%d') 
if not path.exists(path_name):
    makedirs(path_name)
else:
    path_name = path_name + today.strftime('%H%M') 
    makedirs(path_name)
fextension = '.csv'
# filenames for log
filename = path_name + '/'  +'yoctopuce_oldtrap'+ fextension
filename2 = path_name + '/' +'yoctopuce_newtrap_input'+ fextension
filename3 = path_name + '/' + 'yoctopuce_newtrap_fiber'+ fextension
filename4 = path_name + '/' + 'yoctopuce_newtrap_output'+ fextension
# init loggers
loggers=[]
Y2= yoctopucelogger(logger2name, filename2)
Y3= yoctopucelogger(logger3name, filename3)
Y4 =yoctopucelogger(logger4name, filename4)
Y1= yoctopucelogger(logger1name, filename)
loggers = [Y1, Y2, Y3, Y4]

#for l in loggers:
 #   print(l.log_file)

# update loggers every 10 s
schedule.every(10).seconds.do(updateall, loggers, closingtime='1605')

# keep going 
while True:
    schedule.run_pending()
