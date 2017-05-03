"""
Non-Residential Efficiency preprocessing 
----------------------------------------

preprocessing functions for Non-residential Efficiency component  

"""
#~ import os.path
#~ from pandas import read_csv

# preprocessing in preprocessor
import os
from pandas import read_csv


def get_number_buildings (datafile, community, diagnostics = None):
    """
    Function doc
    """
    count_file = datafile
    try:
        data = int(read_csv(count_file ,comment = "#", index_col = 0,
                                             header = 0).ix[community][0])
    except (KeyError):
        data = 0
        if not diagnostics is None:
            self.diagnostics.add_note((
                "Non-residential Efficiency: Community " + community + ""
                " does not have an entry in "+ os.path.split(count_file) + ","
                " using 0"
            ))

    return data
    
def buildings_estimates(datafile, community, population, diagnostics = None):
    """
    """
    est_file = datafile
    data = read_csv(est_file ,comment = u"#",index_col = 0, header = 0)

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
    return df


def expand_args (kwargs):
    if 'preprocessor' in kwargs.keys():
        preprocessor = kwargs['preprocessor']
        community = preprocessor.community
        data_dir = preprocessor.data_dir
        diagnostics = preprocessor.diagnostics
        population = 
    else:
        preprocessor = None
        community = kwargs['community']
        population = kwargs['population']
        data_dir = kwargs['data_dir']
        diagnostics = None
        if 'diagnostics ' in kwargs.keys():
            diagnostics = kwargs['diagnostics']  
    return community, data_dir, diagnostics, preprocessor, population

def build_data_dict (**kwargs):
    #~ print kwargs
    community, data_dir, diagnostics, preprocessor = expand_args (kwargs)
             
    
    data = {}
    data['number buildings'] = get_number_buildings(
        os.path.join(data_dir, "non-res_count.csv"),
        community,
        diagnostics
    )
    data['building estimates'] = 
    
    return data
    
   
   
   
    
    






