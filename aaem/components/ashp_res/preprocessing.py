"""
Air Source Heat Pump Residential preprocessing 
----------------------------------------------

    preprocessing functions for Air Source Heat Pump Residential component
    
    .. note::
        Uses ASHP Base preprocessor functions  

"""
import aaem.components.ashp_base as ashp_base
import config

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
    kwargs['ashp_type'] = config.COMPONENT_NAME
    kwargs['ashp_cost_per_btu_hrs'] = 6000
    kwargs['ashp_btu_hrs'] = 18000
    return ashp_base.preprocess(preprocessor, **kwargs)
