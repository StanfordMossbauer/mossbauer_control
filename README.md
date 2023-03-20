# CAEN Digitizer Readout for DPP-PHA Firmware

### Installation
```
cd dpp-readout
sudo make
```

### Usage
```
dpp-readout <config-file>
```
where `<config-file>` is a text file formatted like `test_config`.

If you hit `w` during acquisition, you can plot the outputs with `plot_traces.py`.


# Stepper Motor Control

In the Mössbauer lab at Stanford, we are using a stepper motor to scan a reference absorber at some velocity relative to a stationary source in order to exploit the non-relativistic doppler shift induced and hence map out the resonance. This repo contains a set of functions that may be useful to interact with the Stepper Motor. More details may be found in the Mössbauer elog.

## Functions
 - `stepperMotorCtrl.py` - the current most up-to-date set of functions to scan absorber relative to source.
 - `stepperMotorCtrl_BK.py` - a legacy version of the code, which used a different function generator to generate the clock signal for the stepper.`
