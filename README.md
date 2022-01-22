# WELCOME TO INTELLIGENT TRAFFIC

## Prerequisites

###Install conda (anaconda)

On MacOS with homebrew

`brew install --cask anaconda`

###Setup Python Environment

Goto project directory.

`conda env create -f environment.yml`

This will produce a conda environment `inteltraffic`

Activate environment:

`conda activate inteltraffic`

### Start Manually
Start manually with default model_01

`python src/run_manually.py`

Start manually with model_02

`python src/run_manually.py model_02`

### Start Round Robin

Run with user interface

`python src/run_round_robin.py model_01`

Run without user interface

`python src/run_round_robin.py model_01  headless`


### Start Training (No user interface)

`python src/run_train.py model_01  headless`
