from mossbauer_control.instruments import Yoctopuce
import time

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