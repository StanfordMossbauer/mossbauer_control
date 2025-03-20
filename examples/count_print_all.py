from mossbauer_control.instruments import CAEN
config_file = 'caen_configs/co57_config_2ch'
integration_time = 100
digi = CAEN(config_file)
digi.timed_acquire(integration_time)

print(digi.count)
