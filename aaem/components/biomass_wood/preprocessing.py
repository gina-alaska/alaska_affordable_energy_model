"""
Biomass Cordwood preprocessing 
------------------------------

    preprocessing functions for Biomass Cordwood component
    
    .. note::
        Uses Biomass Base preprocessor functions  

"""
#~ import os.path
#~ from pandas import read_csv
import aaem.components.biomass_base as bmb
import config
from copy import deepcopy

def preprocess (preprocessor, **kwargs):
    """preprocess data related to existing projects
    
    Parameters
    ----------
    preprocessor: preprocessor.Proprocessor
        a preprocessor object
        
    Returns
    -------
    list
        project names
    
    """
    kwargs['biomass_type'] = config.COMPONENT_NAME
    kwargs['biomass_cost_per_btu_hrs'] = .6
    kwargs['biomass_energy_density'] = 16000000
    
    my_config = bmb.preprocessing.preprocess(preprocessor, **kwargs)

    my_config[config.COMPONENT_NAME]["hours of storage for peak"] = 4
    my_config[config.COMPONENT_NAME]["percent at max output"] = .5 * 100
    my_config[config.COMPONENT_NAME]["cordwood system efficiency"] = .88
    my_config[config.COMPONENT_NAME]["hours operation per cord"] = 5.0
    my_config[config.COMPONENT_NAME]["operation cost per hour"] = 20.00
    my_config[config.COMPONENT_NAME]["boiler assumed output"] = 325000
    
    return my_config
    
