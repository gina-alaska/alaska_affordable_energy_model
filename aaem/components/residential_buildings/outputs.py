"""
outputs.py

    ouputs functions for Residential Building Efficiency component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

def component_summary (coms, res_dir):
    """
    creates a log for the residental component outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "residential_summary.csv" log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            res = coms[c][COMPONENT_NAME]
            out.append([c,
                res.get_NPV_benefits(),res.get_NPV_costs(),
                res.get_NPV_net_benefit(),res.get_BC_ratio(),
                res.hoil_price[0], res.init_HH, res.opportunity_HH,
                res.break_even_cost, res.levelized_cost_of_energy,
                res.baseline_fuel_Hoil_consumption[0]/constants.mmbtu_to_gal_HF,
                (res.baseline_fuel_Hoil_consumption[0] - \
                    res.proposed_fuel_Hoil_consumption[0])/\
                        constants.mmbtu_to_gal_HF,
                round(float(res.fuel_oil_percent)*100,2),
                res.baseline_HF_consumption[0],
                res.baseline_HF_consumption[0] - \
                        res.proposed_HF_consumption[0],
                ])
        except (KeyError,AttributeError) as e :
            #~ print e
            pass
            
    cols = ['community',
           'Residential Efficiency NPV Benefit',
           'Residential Efficiency NPV Cost', 
           'Residential Efficiency NPV Net Benefit',
           'Residential Efficiency B/C Ratio',
           'Heating Oil Price - year 1',
           'Occupied Houses', 
           'Houses to Retrofit', 
           'Break Even Heating Fuel Price [$/gal heating oil equiv.]',
           'Levelized Cost of Energy [$/MMBtu]',
           'Residential Heating Oil Consumed(mmbtu) - year 1',
           'Residential Efficiency Heating Oil Saved(mmbtu/year)',
           'Residential Heating Oil as percent of Total Heating Fuels',
           'Total Residentital Heating Fuels (mmbtu) - year 1',
           'Residential Efficiency Total Heating Fuels Saved (mmbtu/year)',
            ]
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# residental building component summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')
