# SRS830 Programming Manual: https://www.thinksrs.com/downloads/pdfs/manuals/SR830m.pdf
import pyvisa

# Time constants are in seconds
TIME_CONSTANTS = {
    0: 10e-6, 1: 30e-6, 2: 100e-6, 3: 300e-6, 4: 1e-3, 5: 3e-3, 6: 10e-3,
    7: 30e-3, 8: 100e-3, 9: 300e-3, 10: 1, 11: 3, 12: 10, 13: 30, 14: 100,
    15: 300, 16: 1e3, 17: 3e3, 18: 10e3, 19: 30e3
}

# Sensitivities are in volts
SENSITIVITIES = {
    0: 2e-9, 1: 5e-9, 2: 10e-9, 3: 20e-9, 4: 50e-9, 5: 100e-9, 6: 200e-9,
    7: 500e-9, 8: 1e-6, 9: 2e-6, 10: 5e-6, 11: 10e-6, 12: 20e-6, 13: 50e-6,
    14: 100e-6, 15: 200e-6, 16: 500e-6, 17: 1e-3, 18: 2e-3, 19: 5e-3,
    20: 10e-3, 21: 20e-3, 22: 50e-3, 23: 100e-3, 24: 200e-3, 25: 500e-3,
    26: 1, 27: 2, 28: 5, 29: 10, 30: 20, 31: 50
}


class SRS830:
    def __init__(self, gpib_address):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}")

    def set_sensitivity(self, sensitivity):
        closest_sensitivity = min(SENSITIVITIES.values(), key=lambda x: abs(x - sensitivity))
        sensitivity = list(SENSITIVITIES.keys())[list(SENSITIVITIES.values()).index(closest_sensitivity)]
        self.instrument.write(f"SENS {sensitivity}")
        return SENSITIVITIES[sensitivity]
    
    
    def set_time_constant(self, time_constant):
        closest_time_constant = min(TIME_CONSTANTS.values(), key=lambda x: abs(x - time_constant))
        time_constant = list(TIME_CONSTANTS.keys())[list(TIME_CONSTANTS.values()).index(closest_time_constant)]
        self.instrument.write(f"OFLT {time_constant}")
        return TIME_CONSTANTS[time_constant]

    def set_output_amplitude(self, amplitude):
        self.instrument.write(f"SLVL {amplitude}")

    def set_output_frequency(self, frequency):
        self.instrument.write(f"FREQ {frequency}")


    def set_resolution(self, resolution):
        self.instrument.write(f"DDEF 1,{resolution}")

    def read_amplitude(self):
        return float(self.instrument.query("OUTP? 1"))

    def read_phase(self):
        return float(self.instrument.query("OUTP? 2"))

    def close(self):
        self.instrument.close()
        self.rm.close()
