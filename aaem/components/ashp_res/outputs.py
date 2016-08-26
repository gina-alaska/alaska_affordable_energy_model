"""
outputs.py

    ouputs functions for Air Source Heat Pumps - Residential component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

## component summary
def component_summary (coms, res_dir):
    """
    save thes the summary for biomass cordwood
    """
    out = []
    for c in sorted(coms.keys()):
        #~ it = coms[c]['community data'].intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
            ashp = coms[c][COMPONENT_NAME]
            
            kw_exess = ashp.monthly_value_table['kWh consumed'].max()/\
                                (24 * 31)
            try:
                peak_monthly_btu_hr_hh = ashp.peak_monthly_btu_hr_hh
                price =  float(ashp.electricity_prices.ix[ashp.start_year])
                #~ print float(ashp.electricity_prices.ix[ashp.start_year])
            except AttributeError:
                peak_monthly_btu_hr_hh = 0
                price = 0
           
            try:
                intertie = coms[c]['community data'].parent
            except AttributeError:
                intertie = c
            try:
                levelized_cost = ashp.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
                
            try:
                break_even = ashp.break_even_cost
            except AttributeError:
                break_even = 0
                
            ashp.get_diesel_prices()
            diesel_price = float(ashp.diesel_prices[0].round(2))
            hf_price = diesel_price + ashp.cd['heating fuel premium']   
            
            l = [c, 
                 ashp.average_cop,
                 ashp.num_houses,
                 peak_monthly_btu_hr_hh,
                 price,
                 ashp.electric_consumption,
                 kw_exess,
                 ashp.heating_oil_saved,
                 ashp.electric_heat_energy_reduction,
                 diesel_price,
                 hf_price,
                 break_even,
                 levelized_cost,
                 ashp.get_NPV_benefits(),
                 ashp.get_NPV_costs(),
                 ashp.get_NPV_net_benefit(),
                 ashp.get_BC_ratio(),
                 intertie,
                 ashp.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print c
            #~ print e
            pass
    
    cols =  ['Community',
             "ASHP Residential Average Coefficient of Performance (COP)",
             'Number Houses',
             'ASHP Residential Peak Household Monthly Btu/hr',
             'Electricity Price [$/kWh]',
             'ASHP Residential kWh consumed per year',
             "ASHP Residential Excess Generation Capacity"
                                        " Needed for Peak Monthly Load (kW)",
             "ASHP Residential Displaced Heating Oil [Gal]",
             "ASHP Residential Displaced Electricity [kWh]",
             "Diesel Price - year 1 [$/gal]",
             "Heating Fuel Price - year 1 [$/gal]",
             'Break Even Heating Fuel Price [$/gal]',
             'Levelized Cost Of Energy [$/MMBtu]',
             'ASHP Residential NPV benefits [$]',
             'ASHP Residential NPV Costs [$]',
             'ASHP Residential NPV Net benefit [$]',
             'ASHP Residential Benefit Cost Ratio',
             'Intertie',
             'notes'
             ]
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
