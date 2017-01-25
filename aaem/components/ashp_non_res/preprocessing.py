"""
Air Source Heat Pump Non-residential preprocessing 
---------------------------

    preprocessing functions for Air Source Heat Pump Non-residential component
    
    .. note::
        Uses ASHP Base preprocessor functions  

"""
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

## list of data files
raw_data_files = deepcopy(ashp_base.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(ashp_base.preprocess)]
