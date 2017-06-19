"""
Non-Residential Efficiency preprocessing 
----------------------------------------

preprocessing functions for Non-residential Efficiency component  

"""
#~ import os.path
#~ from pandas import read_csv

# preprocessing in preprocessor
import os
from pandas import read_csv, concat, DataFrame
import numpy as np
import copy

def get_number_buildings (community, data_dir, diagnostics):
    """Load # buildings from file
    
    Parameters
    ----------
    community: list
        list of community ids (community names)
    data_dir: path
        path to datafile
    diagnostics: Diagnostics
        diagnostics object
    
    Returns
    -------
    int:
        # buidings in community
    """
    datafile = os.path.join(data_dir, 'non-res_count.csv')
    try:
        data = int(
            read_csv(
                datafile ,
                comment = "#", 
                index_col = 0,
                header = 0
            ).ix[community]['Buildings'].sum()
        )
    except (KeyError, ValueError):
        data = 0
        diagnostics.add_note("Non-residential Efficiency: Community ",
            ("" + community[0] + " does not have an entry in "
             "" + os.path.split(datafile)[1] + ", using 0"
        ))

    return data
    
def get_consumption_estimates(data_dir, population, diagnostics):
    """Get consumption estimates
    
    Parameters
    ----------
    data_dir: path
        path to datafile
    population: int
        population size for estimates
    diagnostics: Diagnostics
        diagnostics object
        
    Returns
    -------
    DataFrame
        estimate data
    """
    datafile = os.path.join(data_dir, 'non-res_consumption_estimates.csv')
    data = read_csv(datafile ,comment = "#",index_col = 0, header = 0)

    units = set(data.ix["Estimate units"])
    l = []
    for itm in units:
        col = data.T[data.ix["Estimate units"] == itm]\
                      [(data.T[data.ix["Estimate units"] == itm]\
                      ["Lower Limit"].astype(float) <= population)]\
                      [data.ix["Estimate units"] == itm]\
                      [(data.T[data.ix["Estimate units"] == itm]\
                      ["Upper Limit"].astype(float) > population)]
        l.append(col)

    data = concat(l).set_index("Estimate units")
    del( data["Lower Limit"])
    del( data["Upper Limit"])
    data =  data.T
    
    data.index.name = 'building type'

    return data
    
def get_building_inventory (community, data_dir, diagnostics, **kwargs):
    """load the building inventory
    
    Parameters
    ----------
    community: list
        list of community ids (community names)
    data_dir: path
        path to datafile
    diagnostics: Diagnostics
        diagnostics object
        
    Returns
    -------
    DataFrame
        building inventory
    """
    datafile = os.path.join(data_dir, 'non-res_buildings.csv')
    data = read_csv(datafile, comment = '#', index_col = 1)
    
    order = ['int_index' , 'Building Type', 'Biomass',
        'Biomass Post', 'Electric', 'Electric Post', 'Fuel Oil',
        'Fuel Oil Post', 'HW District', 'HW District Post', 'Natural Gas',
        'Natural Gas Post', 'Propane', 'Propane Post', #'Retrofits Done',
        'Square Feet', 'implementation cost']
    
    #~ print community
    try:
        data = data.ix[community]
        numbers = [i for i in order if not i in ['Building Type', 'int_index']]
        data[numbers] = data[numbers].replace(r'\S+', np.nan, regex=True)
        #~ print data
        data = data[data.isnull().all(1) == False]
    except KeyError:
        diagnostics.add_note(
            'Non-residential Energy Efficiency: Building Inventory',
            'no buildings in inventory creating empty inventory'
        )
        data = DataFrame(columns = order)


    #~ print data
    data['int_index'] = range(len(data))
    
    data = data[order]
    data = data.set_index('int_index')
    return data

    
def preprocess(preprocessor, **kwargs):
    """Preprocess Non-residential data
    
    Parameters
    ----------
    preprocessor: aaem.preprocessor.Preprocessor object
    
    Returns
    -------
    dict
        data for component configuration
    """
    #~ if not 'population' in kwargs:
        #~ raise StandardError, 'Non-residential preprocessing needs population'
        
    #~ population = kwargs['population']
    
    refit_cost = 7.0 
    #~ if 'non-res-refit-cost' in kwargs:
        #~ refit_cost = float(kwargs['non-res-refit-cost'])
    
    cohort_multiplier = .26 * 100
    #~ if 'non-res-cohort-savings-percent' in kwargs:
        #~ cohort_multiplier = float(kwargs['non-res-cohort-savings-percent'])
        
    start_year = 2017
    #~ if 'non-res-start-year' in kwargs:
        #~ start_year = int(kwargs['non-res-start-year'])   
    
    lifetime = 15
    #~ if 'non-res-project-lifetime' in kwargs:
        #~ lifetime = int(kwargs['non-res-project-lifetime']) 
    
    heating_cost_percent = 0.6 * 100 # convert to whole %
    #~ if 'non-res-heating-cost-percent' in kwargs:
        #~ heating_cost_percent = float(kwargs['non-res-heating-cost-percent']) 
   
   
    # The waste oil price is N% of the heating oil price
    waste_oil_cost_precent = 0.5 * 100# convert to whole %
    #~ if 'non-res-waste-oil-cost-precent' in kwargs:
        #~ waste_oil_cost_precent = float(kwargs['non-res-waste-oil-cost-precent']) 
    
    inventory_ids = preprocessor.GNIS_ids
    count_ids = preprocessor.communities
    if not preprocessor.process_intertie:
        if preprocessor.intertie_status == 'child':
            inventory_ids = [inventory_ids[1]]
            count_ids = [count_ids[1]]
        else:
            inventory_ids = [inventory_ids[0]]
            count_ids = [count_ids[0]]
    #~ print inventory_ids
    population = \
        preprocessor.data['community']['population'].ix[2010]['population']
    #~ print 'C', population
    if not preprocessor.process_intertie and \
        preprocessor.intertie_status == 'child':    
        population = preprocessor.load_population(get_it_ids = True).ix[2010]['population']
    
    
    data = {
        'Non-residential Energy Efficiency':{
            'enabled': True,
            'start year': start_year,
            'lifetime': lifetime,
            'average refit cost': refit_cost,
            'cohort savings percent': cohort_multiplier,
            'heating percent': heating_cost_percent,
            'waste oil cost percent': waste_oil_cost_precent,
            'number buildings': get_number_buildings(
                count_ids, 
                preprocessor.data_dir, 
                preprocessor.diagnostics
            ),
            'consumption estimates':  get_consumption_estimates(
                preprocessor.data_dir,
                population, 
                preprocessor.diagnostics),
            'building inventory': get_building_inventory(
                inventory_ids,
                preprocessor.data_dir, 
                preprocessor.diagnostics)
        }
    }
    return data
    
   
    
    






