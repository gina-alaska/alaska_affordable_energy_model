"""
preprocessing.py

    preprocessing functions for Air Source Heat Pumps - Non-Residential component  
"""
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

## list of data files
raw_data_files = deepcopy(ashp_base.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(ashp_base.preprocess)]
