"""
outputs.py

    ouputs functions for Water/Waste Water efficiency component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

## component summary
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
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            www = coms[c]['water wastewater']
            try:
                oil_p, elec_p =  www.hoil_price[0], www.elec_price[0]
            except AttributeError:
                oil_p, elec_p = 0,0
            
            savings = (www.baseline_HF_consumption -\
                      www.proposed_HF_consumption) * constants.mmbtu_to_gal_HF
            out.append([c,
                www.get_NPV_benefits(),www.get_NPV_costs(),
                www.get_NPV_net_benefit(),www.get_BC_ratio(),
                oil_p, elec_p ,
                #~ www.num_buildings , www.refit_sqft_total,
                www.break_even_cost,
                www.levelized_cost_of_energy['MMBtu'],
                www.levelized_cost_of_energy['kWh'],
                www.baseline_HF_consumption[0] * constants.mmbtu_to_gal_HF,
                www.baseline_kWh_consumption[0],
                savings[0],
                (www.baseline_kWh_consumption - www.proposed_kWh_consumption)[0]
                ])
        except (KeyError,AttributeError) as e:
            #~ print c +":"+ str(e)
            pass
            
            
    cols = ['community',
            'Water/Wastewater Efficiency NPV Benefit',
            'Water/Wastewater Efficiency NPV Cost',
            'Water/Wastewater Efficiency NPV Net Benefit',
            'Water/Wastewater Efficiency B/C Ratio',
            'Heating Oil Price - year 1',
            '$ per kWh - year 1',
            #~ 'Number Water/Wastewater Buildings',
            #~ 'Water/Wastewater Total Square Footage',
            'Break Even Diesel Price [$/gal heating oil equiv.]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Levelized Cost of Energy [$/kWh]',
            'Water/Wastewater Heating Oil Equiv. Consumed(gal) - year 1',
            'Water/Wastewater Electricity Consumed(kWh) - year 1',
            'Water/Wastewater Efficiency Heating Oil Equiv. Saved[gal/year]',
            'Water/Wastewater Efficiency Electricity Saved[kWh/year]']
            
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,'water-wastewater_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# non residental building component summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')
