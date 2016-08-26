"""
outputs.py

    ouputs functions for Non-Residential Building Efficiency component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

def component_summary (coms, res_dir): 
    """
    creates a log for the non-residental component outputs by community
    
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
        a csv file "non-residential_summary.csv"log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1:# or c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['non-residential buildings']
            savings = (com.baseline_HF_consumption -\
                      com.proposed_HF_consumption ) * constants.mmbtu_to_gal_HF
            out.append([c,
                com.get_NPV_benefits(),com.get_NPV_costs(),
                com.get_NPV_net_benefit(),com.get_BC_ratio(),
                com.hoil_price[0], com.elec_price[0], 
                com.num_buildings , com.total_sqft_to_retrofit,
                com.break_even_cost,
                com.levelized_cost_of_energy['MMBtu'],
                com.levelized_cost_of_energy['kWh'],
                com.baseline_HF_consumption * constants.mmbtu_to_gal_HF, 
                com.baseline_kWh_consumption,
                savings,
                com.baseline_kWh_consumption - com.proposed_kWh_consumption])
        except (KeyError,AttributeError) as e:
            #~ print c +":"+ str(e)
            pass
            
            
    cols = ['community',
            'Nonresidential Efficiency NPV Benefit',
            'Nonresidential Efficiency NPV Cost',
            'Nonresidential Efficiency NPV Net Benefit',
            'Nonresidential Efficiency B/C Ratio',
            'Heating Oil Price - year 1',
            '$ per kWh - year 1',
            'Number Nonresidential Buildings',
            'Nonresidential Total Square Footage',
            'Break Even Heating Fuel Price [$/gal heating oil equiv.]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Levelized Cost of Energy [$/kWh]',
            'Nonresidential Heating Oil  oil equiv. Consumed(gal) - year 1',
            'Nonresidential Electricity Consumed(kWh) - year 1',
            'Nonresidential Efficiency Heating Oil  oil equiv. Saved[gal/year]',
            'Nonresidential Efficiency Electricity Saved[kWh/year]']
            
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,'non-residential_summary.csv')
    ##fd = open(f_name,'w')
    ##fd.write("# non residental building component summary by community\n")
    ##fd.close()
    data.to_csv(f_name, mode='w')
