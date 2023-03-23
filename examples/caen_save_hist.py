from mossbauer_control.instruments import CAEN

savedir = r'/home/mossbauer_lab/Data/'
filename  = 'Hist_skim_550_1200_v_0_t_100_noabsorber.txt'

config_file = r'/home/mossbauer_lab/mossbauer_control/caen_configs/co57_config'
integration_time = 100
digi = CAEN(config_file)
digi.timed_acquire(integration_time)
print('rate is {:.2f} Hz'.format(digi.count/integration_time))
h = digi.histogram( savefile = savedir+filename, skim_lim_lower = 500, skim_lim_upper = 1250)
