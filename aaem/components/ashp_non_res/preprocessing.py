"""
Air Source Heat Pump Non-residential preprocessing 
--------------------------------------------------

    preprocessing functions for Air Source Heat Pump Non-residential component
    
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
    kwargs['ashp_cost_per_btu_hrs'] = 25000 
    kwargs['ashp_btu_hrs'] = 90000
    return ashp_base.preprocess(preprocessor, **kwargs)
    
