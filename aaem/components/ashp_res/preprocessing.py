"""
preprocessing.py

    preprocessing functions for Air Source Heat Pumps - Residential component  
"""
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

raw_data_files = deepcopy(ashp_base.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(ashp_base.preprocess)]
