# Mossbauer Experiment Control Software

## Installation
```
git clone https://github.com/StanfordMossbauer/mossbauer_control.git
cd mossbauer_control
pip install -r requirements.txt
pip install -e .
```

### CAEN DAQ Software

This is located under `dpp-readout`. We can always break it back out into its own repo if needed. Install (for anyone using your conda environment) with:

```
cd dpp-readout
sudo make clean
sudo make
```

You can test by running the CLI with the command `dpp-readout`.

## Usage
See `examples/rudimentary_sweep.py`.
