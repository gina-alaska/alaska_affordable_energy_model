"""
Residential Efficiency preprocessing 
------------------------------------

preprocessing functions for Residential Efficiency component  

"""
import os
from pandas import read_csv, concat, DataFrame
import numpy as np

def preprocess(preprocessor, **kwargs):
    """Preprocess Residential data
    
    Parameters
    ----------
    preprocessor: aaem.preprocessor.Preprocessor object
    
    Returns
    -------
    dict
        data for component configuration
    """

    data_file = os.path.join(preprocessor.data_dir, "res_model_data.csv")
    fuel_file = os.path.join(preprocessor.data_dir, "res_fuel_source.csv")

    fuel_data = read_csv(fuel_file, index_col=0, comment = "#")
    
    ids = [preprocessor.communities[0] , preprocessor.aliases[0]]
    if preprocessor.intertie_status == 'child':
       ids = [preprocessor.communities[1] , preprocessor.aliases[1]] 
    
    fuel = fuel_data.ix[ids][fuel_data.ix[ids].isnull().all(1) == False].T
    
    fuel = fuel.ix[["Total", "Utility Gas", "LP", "Electricity", "Fuel Oil",
                    "Coal", "Wood", "Solar", "Other", "No fuel used"]]
    fuel = fuel * 100
    #~ print fuel
    #~ print preprocessor.community
    data = read_csv(
        data_file, 
        index_col=0, 
        comment = "#"
    ).ix[preprocessor.community]
    #~ print data
    

    #~ fuel.columns = [preprocessor.community]
    data = DataFrame(data)
    data.columns = [ preprocessor.community ]
    fuel.columns = [ preprocessor.community ]
    df = concat([DataFrame(data),fuel])
    #~ print df
    df = df.T
    del df['Energy Region']
    df = df.T
    
    start_year = 2017
    if 'res_start_year' in kwargs:
        start_year = int(kwargs['res_start_year'])   
    
    lifetime = 20
    if 'res_project_lifetime' in kwargs:
        lifetime = int(kwargs['res_project_lifetime']) 
    
    min_kwh = 6000
    if 'res_min_kwh' in kwargs:
        lifetime = int(kwargs['res_min_kwh']) 
    
    cost = 11000
    if 'res_refit_cost' in kwargs:
        cost = int(kwargs['res_refit_cost']) 
    
    df = df[df.columns[0]]
    
    data = df.to_dict()

    if preprocessor.process_intertie:
        ids = preprocessor.communities + preprocessor.aliases
        #~ print ids
        total_hh = read_csv(
            data_file, 
            index_col=0, 
            comment = "#"
        )['Total Occupied'].ix[ids].sum()
        data['Total Occupied'] = int(total_hh)

     
    try:
        data['average kWh per house'] = \
            preprocessor.data['community']\
                ['utility info']\
                ['consumption residential']\
                .ix[data['Year']]/ data['Total Occupied']
    except (KeyError, IndexError):
        data['average kWh per house'] = np.nan
    data = {
        'Residential Energy Efficiency' : {
            'enabled': True, 
            'start year': start_year,
            'lifetime': lifetime, 
            'min kWh per household': min_kwh, 
            'average refit cost': cost,
            
            'data': data
            
        
        }
    }
    ## NOTE these are the keys that are needed if we wanted to clean this up
    #~ total occupied
    #~ year
    #~ average kWh per house
    #~ "Total Consumption (MMBtu)"
    #~ "BEES Total Consumption (MMBtu)"
    #~ "Pre-Retrofit Avg Area (SF)"
    #~ "Pre-Retrofit Avg EUI (MMBtu/sf)"
    #~ fuel oil percent
    #~ wood percent
    #~ utility Gas percent
    #~ propane percent
    #~ electric percent
    #~ print data
    return data
    #~ print df[df.columns[0]]
   
    #~ out_file = os.path.join(self.out_dir, "residential_data.csv")
    #~ fd = open(out_file,'w')
    #~ fd.write(self.residential_header())
    #~ fd.write("key,value\n")
    #~ fd.close()

    #~ df.to_csv(out_file,mode="a",header=False)
    #~ self.residential_data = df
    
    #~ self.init_households = int(df.ix["Total Occupied"])
    #~ self.init_household_year = int(df.ix["Year"])
