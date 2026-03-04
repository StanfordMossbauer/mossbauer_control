

import pyvisa
import time



class LK220:
    def __init__(self, address="ASRL7::INSTR"):
        self.address = address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(self.address)
        self.instrument.baud_rate =115200
        self.instrument.write_termination = "\r\n"
        self.instrument.read_termination = "\r\n"

    def get_temperature(self):        
        self.instrument.write(f"TACT?")
        r1 = self.instrument.read()
        r2 = self.instrument.read()
        try:
            return float(r1)
        except:
            return float(r2)
        
    def close(self):
        self.instrument.close()
    

if __name__ == "__main__":

    chiller = LK220()
    time.sleep(1)
    print(chiller.get_temperature())
    chiller.close()
    