"""
This was taken from Gautam's old code and was specifically for controlling
the stepper through the MokuGo. It is no longer used in the current setup.
"""


import serial
import atexit

class DFR1507A:
    '''
    Initiates an instance of the DFR1507A driving a KR26.
    '''
    def __init__(self, resource, timeout = 1000000):
        
        self.device = serial.Serial(resource, timeout)
        atexit.register(self.close)  # close self if python process dies
        print(self.device.readline())
    
            
        self.RES_1 = 2*0.00288/360 # (ball screw lead mm/rev) * (?) / 1rev
        self.RES_2 = 2*0.009/360 # (ball screw lead mm/rev) * (?) / 1rev
        self.DIR_SELECT = 24  # Direction select. 0=CW, 1=CCW
        self.RES_SELECT = 16  # res select. 0=RS1, 1=RS2
        self.AW_OFF = 25      # All windings off pin. 0=no drive. 1= regular drive
        self.MAX_FREQ = 500e3    # Don't pulse faster than this. Controller technically can handle up to 1MHz.

    
    def setResolution(self, res=1):
       
        if res==1:
            self.device.write(b'a')
        elif res==2:
            self.device.write(b'b') 
        return
    
    def setDirection(self, DIR="CW"):
    
        if DIR=='CW':
            self.device.write(b'c')
        elif DIR=='CCW':
            self.device.write(b'd')
        return

    def AWon(self):
        self.device.write(b'e')
        return
    
    def AWoff(self):
        self.device.write(b'f')
        return


    def readFlagState(self):
        #True means detector is uncovered

        self.device.write(b'?')
        response = self.device.readline()
        response = response.replace(b"\r\n", b"")
        if response == b'w': 
            return False, False
        elif response == b'x': 
            return True, False
        elif response == b'y': 
            return False, True
        elif response == b'z': 
            return True, True
        else: 
            return


    def close(self):
        self.AWoff()
        self.device.close()

    def __del__(self):
        self.AWoff()
        self.device.close()

       
if __name__ == "__main__":
    motordrive = DFR1507A("/dev/ttyACM0")
    motordrive.setDirection("CW")
    motordrive.__del__()
    

