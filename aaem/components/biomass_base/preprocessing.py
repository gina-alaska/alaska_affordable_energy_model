"""
Biomass base preprocessing 
--------------------------

    preprocessing functions for Biomass Base Component

"""
import os.path
from pandas import read_csv
import numpy as np
    
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
    comp_name = kwargs['biomass_type']
    cost_per_btu_hrs = kwargs['biomass_cost_per_btu_hrs']
    energy_density = kwargs['biomass_energy_density']
    #~ btu_hrs = kwargs['ashp_btu_hrs']
    boiler_assumed_output = kwargs['biomass_boiler_output']
    
    
    start_year = preprocessor.data['community']['current year'] + 1
    
    ids = [preprocessor.communities[0],preprocessor.aliases[0]]
    if preprocessor.intertie_status == 'child':
        ids = [preprocessor.communities[1],preprocessor.aliases[1]]
    
    
    data = read_csv(
        os.path.join(preprocessor.data_dir,"biomass_resource_data.csv"),
        comment = '#',
        index_col = 0)
    
    bio_data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
    
    if len(bio_data) != 0:
        sufficient = \
            bio_data['Sufficient Biomass for 30% of Non-residential buildings']
        sufficient = True if sufficient.lower() == 'yes' else False
        peak = data['Peak Month % of total']
        cap_factor = bio_data['Capacity Factor']
    else:
        sufficient = False
        peak = np.nan
        cap_factor = np.nan
        
                
    return {
        comp_name: {
            'enabled': True, # 
            'lifetime': 20, # number years <int>
            'start year': start_year, # start year <int>
            
            'cost per btu/hrs': cost_per_btu_hrs,
            'o&m per year': 320,
            
            'Sufficient Biomass for 30% of Non-residential buildings': 
                sufficient,
            'Peak Month % of total': peak,
            'Capacity Factor': cap_factor,
            

            }
            
        }
    }
  

  hours of storage for peak: 4 # <float>
  percent at max output: 0.5 # <float>
  cordwood system efficiency: 0.88 # <float>
  hours operation per cord: 5.0 # <float>
  operation cost per hour: 20.0 # <float>
  boiler assumed output: 325000 # <float>


  
  pellet efficiency: 0.8 # effcicieny of pellets (% as decimal) <float>

  default pellet price: 400 # pellet cost per ton ($) <float>


## list of wind preprocessing functions
preprocess_funcs = [preprocess]
