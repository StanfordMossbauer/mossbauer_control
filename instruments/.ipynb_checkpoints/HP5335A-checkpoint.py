



#MANUAL UNIVERSAL COUNTER. main functions found at p.61-62 of:
#https://bukosek.si/hardware/collection/hp-5335a/hp-5335a-operating-and-service-manual.pdf



import pyvisa
import sys
import atexit
import time
#from .base import MossbauerInstrument

class HP5335A():
    
    def __init__(self, resource):
        
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(resource)
        #atexit.register(self.close)  # close self if python process dies
        #print(self.device.query('*IDN?'))
        self.device.read_termination = '\r\n'
        self.device.clear()
        self.device.write('RE')
        self.device.write('WA0') #wait to output data untill asked. Alternative is is ready-for-data (RFD) mode: if the reader is ready it takes it, but if not too late, counter will go on.
        self.device.write('DR0')

    def setup_mossbauer_scan(self):
        self.set_total_a_mode()
        self.reset()
        return

    def setup_sweep(self, frequency, cycles):
        """placeholder"""
        return

    def setup_dummy_sweep(self):
        """placeholder"""
        return

    def set_trigger_level(self,value):
        self.device.write("AT{:+.2f}".format(value))

    def set_trigger_remote(self,value=True):
        if value: 
            self.device.write("TR1")
        else:
            self.device.write("TR0")

    def set_frequency_mode(self):
        self.device.write("FN1")
        
    def set_total_a_mode(self):
        self.device.write("FN3")
        
    def reset(self):
        self.device.write('RE')
        
        
    def gate_open(self):
        self.device.write('GO')
        
    def gate_close(self):
        self.device.write('GC')
    
    def read_count(self):
        try:
            out1 = self.device.read()
            out2 = self.device.read()

        except:
            print("Reading error!")
            self.device.clear()
            return
        
        value1 = float(out1.split(" ")[-1])
        value2 = float(out2.split(" ")[-1])
        
        self.device.clear()
        #print(out1, out2)

        return value2

    def read_count2(self):
        try:
            out = self.device.read()
        except:
            print("Reading error!")
            self.device.clear()
            return
        
        self.device.clear()
        value  = float(out.split(" ")[-1])
        #print(out)
        return value

    
    def read_frequency(self):
        Flag = True
        
        while Flag:
            try:
                out = self.device.read()
                self.device.clear()
                Flag = False
            except:
                pass

        self.device.clear()
        value = float(out.split(" ")[-1])
        return value

    def close(self):
        self.device.__del__()
    


if __name__ == "__main__":
    counter1 = HP5335A("GPIB::1::INSTR")
    counter2 = HP5335A("GPIB::2::INSTR")
    counter3 = HP5335A("GPIB::3::INSTR")

    counter1.setup_mossbauer_scan()
    counter2.setup_mossbauer_scan()
    counter3.setup_mossbauer_scan()


    time.sleep(0.1)

    counter1.gate_open()
    counter2.gate_open() 
    counter3.gate_open()
   



    time.sleep(10)
    counter1.gate_close()   
    counter2.gate_close()
    counter3.gate_close()

    time.sleep(0.1)

    count = [counter1.read_count(),counter2.read_count(),counter3.read_count()]
    time.sleep(0.1)
    print(count)
    
    #counter.mode("FREQ A")
    #counter.reset()
    #a = counter.read_frequency()
    #print(a)

    