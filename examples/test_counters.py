from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS2000, BK4060B, HP5335A, Yoctopuce
import time

counter1 = HP5335A("GPIB::3::INSTR")
#counter1.device.write("FN3")
#counter1.device.write("AU1")
#counter1.device.write("AT1.3")
#counter1.setup_mossbauer_scan()


time.sleep(0.1)
counter1.gate_open()
time.sleep(1)
counter1.gate_close()
time.sleep(0.1)
print(counter1.read_count2())


'''

counter1.device.write("IN")
counter2.device.write("IN")
counter3.device.write("IN")

counter1.device.write("DR0")
counter2.device.write("DR0")
counter3.device.write("DR0") 

#counter1.device.write("SR1")
#counter2.device.write("SR1")
#counter3.device.write("SR1") 



counter1.set_total_a_mode()
counter2.set_total_a_mode()
counter3.set_total_a_mode()



counter1.device.write("CY3")
counter2.device.write("CY3")
counter3.device.write("CY3") 

counter1.device.write("WA1")
counter2.device.write("WA1")
counter3.device.write("WA1") 

#counter1.device.write("WA0")
#counter2.device.write("WA0")
#counter3.device.write("WA0") 



#counter1.device.write("RE")
#counter2.device.write("RE")
#counter3.device.write("RE")


counter1.device.write("GO")
counter2.device.write("GO")
counter3.device.write("GO")



counter1.device.write("GC")
counter2.device.write("GC")
counter3.device.write("GC")



'''

#counter1 = HP5335A("GPIB::1::INSTR")
#counter2 = HP5335A("GPIB::2::INSTR")
#counter3 = HP5335A("GPIB::3::INSTR")

#counter1.setup_mossbauer_scan()
#counter2.setup_mossbauer_scan()
#counter3.setup_mossbauer_scan()


#counter1.set_coupling("DC")
#counter1.device.write("AU0")
#counter1.device.write("TR0")
#counter1.device.write("AT2")

#counter1.set_trigger_level(1.3)


#counter2.set_coupling("DC")
#counter2.set_trigger_level(-1.3)

#counter3.set_coupling("AC")
#counter3.set_trigger_level(0.02)
#counter3.set_trigger_level(-1.02)


#counter1.gate_open()
#counter2.gate_open()
#counter3.gate_open()

#time.sleep(1)

#counter1.gate_close()
#counter2.gate_close()
#counter3.gate_close()





#try:
#	a = counter1.read_count2()
#	print(a/10)
#	b = counter2.read_count2()
#	print(b/10)
#	c = counter3.read_count2()
#	print(c/10)
#except:#
#	pass
