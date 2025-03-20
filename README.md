# Mossbauer Experiment Control Software

## Installation
```
git clone https://github.com/StanfordMossbauer/mossbauer_control.git
cd mossbauer_control
pip install -r requirements.txt
pip install -e .
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
