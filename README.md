# Mossbauer Experiment Control Software

## Installation
```
git clone https://github.com/StanfordMossbauer/mossbauer_control.git
cd mossbauer_control
pip install -r requirements.txt
pip install -e .
```

## Pull updates

git pull

## Push updates

```
git config --global credential.helper store     #the foirs time you pushk for credentials, but never again!

git add .                                       #adds all modification is directory and subdirectories
git commit -m "message"
git push
```


## New drivers

When adding a new instrument driver, place it in mossbauer_control/instruments/.
In order to make it findable add a line to the __init__.py file:
```
    from .driver_file import driver_class
```
Doin this you will be able to do this from any location:
```
    from mossbauer_control.instruments import driver_class
```
### CAEN DAQ Software

The CAEN DAQ software is based on code from [here](https://github.com/cjpl/caen-suite/tree/master/CAENDigitizer/samples/ReadoutTest_DPP_PHA_x724), with config format etc mostly stolen from [here](https://github.com/cjpl/caen-suite/blob/master/WaveDump/src/WDconfig.c).

This is located under `dpp-readout`. We can always break it back out into its own repo if needed. Install (for anyone using your conda environment) with:

```
cd dpp-readout
make clean
make
```

You can test by running the CLI with the command `dpp-readout`.

## Usage
See `examples/rudimentary_sweep.py`.
