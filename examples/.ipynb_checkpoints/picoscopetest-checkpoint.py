from mossbauer_control.instruments import PS2000

ps = PS2000()
ps.setup_mossbauer_scan()

si = ps.setSamplingInterval(5e-3,1)

ps.setSimpleTrigger(trigSrc="B",threshold_V= 1.0,direction="Rising",delay=0,enabled=True,timeout_ms=5000)   
ps.runBlock()

ps.waitReady()

data = ps.getDataV("A")