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


def get_number_buildings (community, data_dir, diagnostics):
    """
    Function doc
    
    
    """
    datafile = os.path.join(data_dir, 'non-res_count.csv')
    try:
        data = int(read_csv(datafile ,comment = "#", index_col = 0,
                                             header = 0).ix[community][0])
    except (KeyError):
        data = 0
        diagnostics.add_note("Non-residential Efficiency: Community ",
            ("" + community + " does not have an entry in "
             "" + os.path.split(datafile)[1] + ", using 0"
        ))

    return data
    
def get_consumption_estimates(data_dir, population, diagnostics):
    """
    """
    datafile = os.path.join(data_dir, 'non-res_consumption_estimates.csv')
    data = read_csv(datafile ,comment = u"#",index_col = 0, header = 0)

    units = set(data.ix["Estimate units"])
    l = []
    for itm in units:
        l.append(data.T[data.ix["Estimate units"] == itm]\
                      [(data.T[data.ix["Estimate units"] == itm]\
                      ["Lower Limit"].astype(float) <= population)]\
                      [data.ix["Estimate units"] == itm]\
                      [(data.T[data.ix["Estimate units"] == itm]\
                      ["Upper Limit"].astype(float) > population)])

    df = concat(l).set_index("Estimate units")
    del(df["Lower Limit"])
    del(df["Upper Limit"])
    df = df.T
    
    df.index.name = 'building type'
    return df

def get_building_inventory (community, data_dir, diagnostics, **kwargs):
    """ Function doc """
    datafile = os.path.join(data_dir, 'non-res_buildings.csv')
    data = read_csv(datafile, comment = '#', index_col = 0)
    
    order = ['int_index' , 'Building Type', 'Biomass',
        'Biomass Post', 'Electric', 'Electric Post', 'Fuel Oil',
        'Fuel Oil Post', 'HW District', 'HW District Post', 'Natural Gas',
        'Natural Gas Post', 'Propane', 'Propane Post', 'Retrofits Done',
        'Square Feet', 'implementation cost']
    
    try:
        data = data.ix[[community]]
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

    
   
   
def preprocess(community, data_dir, diagnostics, **kwargs):
    """
    """
    if not 'population' in kwargs:
        raise StandardError, 'Non-residential preprocessing needs population'
        
    population = kwargs['population']
    
    refit_cost = 7.0 
    if 'non-res-refit-cost' in kwargs:
        refit_cost = float(kwargs['non-res-refit-cost'])
    
    cohort_multiplier = .26 * 100
    if 'non-res-cohort-savings-percent' in kwargs:
        cohort_multiplier = float(kwargs['non-res-cohort-savings-percent'])
        
    start_year = 2017
    if 'non-res-start-year' in kwargs:
        start_year = int(kwargs['non-res-start-year'])   
    
    lifetime = 15
    if 'non-res-project-lifetime' in kwargs:
        lifetime = int(kwargs['non-res-project-lifetime']) 
    
    heating_cost_percent = 0.6 * 100 # convert to whole %
    if 'non-res-heating-cost-percent' in kwargs:
        heating_cost_percent = float(kwargs['non-res-heating-cost-percent']) 
   
   
    # The waste oil price is N% of the heating oil price
    waste_oil_cost_precent = 0.5 * 100# convert to whole %
    if 'non-res-waste-oil-cost-precent' in kwargs:
        waste_oil_cost_precent = float(kwargs['non-res-waste-oil-cost-precent']) 
    
   
    
    data = {
        'Non-residential Energy Efficiency':{
            'enabled': True,
            'start year': start_year,
            'lifetime': lifetime,
            'average refit cost': refit_cost,
            'cohort savings percent': cohort_multiplier,
            'heating cost percent': heating_cost_percent,
            'waste oil cost percent': waste_oil_cost_precent,
            'number buildings': get_number_buildings(community, 
                data_dir, diagnostics),
            'consumption estimates':  get_consumption_estimates(data_dir,
                population, diagnostics),
            'building inventory': get_building_inventory(community,
                data_dir, diagnostics)
        }
    }
    return data
    
   
    
    






