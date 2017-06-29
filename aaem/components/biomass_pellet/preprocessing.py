"""
Biomass Pellet preprocessing 
----------------------------

    preprocessing functions for Biomass Pellet component
    
    .. note::
        Uses Biomass Base preprocessor functions  

"""
import aaem.components.biomass_base as bmb
import config

def preprocess (preprocessor, **kwargs):
    """preprocess data related to existing projects
    
    Parameters
    ----------
    preprocessor: preprocessor.Preprocessor
        a preprocessor object
        
    Returns
    -------
    list
        project names
    
    """
    kwargs['biomass_type'] = config.COMPONENT_NAME
    kwargs['biomass_cost_per_btu_hrs'] = .54
    kwargs['biomass_energy_density'] =  17600000
    
    my_config = bmb.preprocessing.preprocess(preprocessor, **kwargs)

    my_config[config.COMPONENT_NAME]["pellet efficiency"] = .8
    my_config[config.COMPONENT_NAME]["default pellet price"] = 400
    
    return my_config
