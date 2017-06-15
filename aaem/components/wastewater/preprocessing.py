"""
Water Wastewater Preprocessing 
------------------------------

preprocessing functions for the Water Wastewater component  

"""
# preprocessing in preprocessor
import os
from pandas import read_csv, concat, DataFrame

def preprocess(preprocessor, **kwargs):
    """Preprocess Water/Wastewater data
     
    Parameters
    ----------
    preprocessor: aaem.preprocessor.Preprocessor object
    
    Returns
    -------
    dict
        data for component configuration
    """
    data_file = os.path.join(preprocessor.data_dir,
        "water-wastewater_projects_potential.csv")
    assumptions_file =  os.path.join(preprocessor.data_dir,
        "water-wastewater_assumptions.csv")

    ## system type mapping From Neil
    ##Circulating/Gravity: Circulating/Gravity, Circulating/Pressure,
    ##                     Circulating/ST/DF
    ##Circulating/Vacuum: Circulating/Vacuum, Closed Haul/Vacuum
    ##Haul:  Closed Haul/Closed, Haul, Watering Point
    ##Pressure/Gravity: Pressure/Gravity, Pressure/NA, Pressure/ST/DF
    ##Washeteria/Honey Bucket: Washeteria
    ##None:  Wells/Gravity, Wells/NA, Wells/ST/DF, Wells/ST/OF

    sys_map = {
                "Circulating/Gravity":"Circulating/Gravity",
                "Circulating/Pressure":"Circulating/Gravity",
                "Circulating/ST/DF":"Circulating/Gravity",
                "Circulating/Vacuum":"Circulating/Vac",
                "Closed Haul/Vacuum":"Circulating/Vac",
                "Haul":"Haul",
                "Closed Haul/Closed Haul":"Haul",
                "Watering Point":"Haul",
                "Pressure/Gravity": "Pressure/Gravity",
                "Pressure/NA": "Pressure/Gravity",
                "Pressure/ST/DF": "Pressure/Gravity",
                "Washeteria":"Wash/HB",
                "None": "None",
              }


    try:
        ww_d = read_csv(data_file, comment = '#',
            index_col = 0).ix[preprocessor.community]
    except KeyError:
        #~ raise StandardError, str(com_id) + " is not in " + data_file
        preprocessor.diagnostics.add_warning("Wastewater",
                                     "system not found, " + \
                                     "assuming zeros")
        ww_d = read_csv(data_file, comment = '#', index_col = 0).ix[-1]
        ww_d[:] = 0
        ww_d["System Type"] = "UNKNOWN"
        ww_d["HR Installed"] = False


    try:
        a = ww_d["Biomass"]
    except KeyError:
        ww_d["Biomass"] = False

    try:
        sys_type = sys_map[ww_d["System Type"]]
        if sys_type == "None":
            raise ValueError, "no w/ww system"
        ww_a = read_csv(assumptions_file, comment = '#', index_col = 0)
        ww_a = ww_a.ix[sys_type]
        ww_a["assumption type used"] = sys_type
        df = concat([ww_d,ww_a])
    except (KeyError, ValueError )as e:
        preprocessor.diagnostics.add_warning("wastewater",
                                     "system type unknown")
        ww_d['HDD kWh']	= 0.0
        ww_d['HDD HF'] = 0.0
        ww_d['pop kWh'] = 0.0
        ww_d['pop HF'] = 0.0
        
        ww_d["Year"] = 2010
        ww_d["assumption type used"] = "UNKNOWN"
        #~ ww_d.to_csv(out_file, mode = 'a')
        df = ww_d

    start_year = 2017
    if 'www_start_year' in kwargs:
        start_year = int(kwargs['www_start_year'])   
    
    lifetime = 15
    if 'www_project_lifetime' in kwargs:
        lifetime = int(kwargs['www_project_lifetime']) 

    data = {
        'Water and Wastewater Efficiency': {
            'enabled': True, 
            'start year': start_year,
            'lifetime': lifetime, 
            'audit cost': 10000,
            'average refit cost': 360.0, 
            'electricity refit reduction': 25,
            'heating fuel refit reduction': 35,
            'heat recovery multiplier': .5, 
            'heating cost percent': 50,
            'data': df.to_dict()
        }
    }

    return data
