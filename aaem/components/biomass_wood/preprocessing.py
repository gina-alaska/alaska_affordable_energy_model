"""
preprocessing.py

    preprocessing functions for Biomass - Cordwood component  
"""
#~ import os.path
#~ from pandas import read_csv
import aaem.components.biomass_base as bmb
from copy import deepcopy

# data files for preprocessing
raw_data_files = deepcopy(bmb.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(bmb.preprocess)]