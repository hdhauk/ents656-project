# Project ENTS656

## Usage

```shell
# Show help page
python main.py -h

# Run simulation with standard config "output.json"
python main.py

# Run 5 simulations concurrently, saving output for 
# each in "results_{sim number}.txt"
python main.py -m -o "results"

# Run 5 simulations with config "q2_config.json"
python main.py -m -c "q2_config.json"

# Run unittests
python -m unittest *_test.py -v

# Run unittest plotting for question 3 
# (+ some visual verification of some functions)
python rf_test.py -plot
```


## Architecture

|Module|Purpose|
|-|-|
|`main.py`| Main entry point and overall program flow based on passed command line arguments.|
|`simulation.py`| Functionality for setting up and running actual simulations.
|`rf.py`| Functions for generating RSL values, and stochastic values.|
|`user.py`| Class defining a user in the simulation. Store primarily data specific to one user.|
|`tower.py`| Class defining a generic base station (in the project referred to as a tower, in order to avoid confusion with *the* base station). The towers store most of the statistics/data generated during simulation.|
|`output.py`| Printing and plotting data and statistics.
|`cfg.py`| Reading and parsing json config files.|
|`errors.py`|Provide project specific exceptions and error codes.|
|`*_test.py`| Unit tests for some of the functionality in the corresponding module.|
