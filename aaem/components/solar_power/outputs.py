"""
outputs.py

    ouputs functions for Solar Power component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

## component summary
def component_summary (coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            solar = coms[c]['solar power']

            start_yr = solar.comp_specs['start year']
            solar.get_diesel_prices()
            diesel_price = float(solar.diesel_prices[0].round(2))
            assumed_out = solar.comp_specs['data']['Output per 10kW Solar PV']
            average_load = solar.average_load
            proposed_capacity = solar.proposed_load + 0
            existing_capacity = solar.comp_specs['data']['Installed Capacity']
            wind_capacity = solar.comp_specs['data']['Wind Capacity']
           
            try:
                net_gen = solar.generation_proposed [0]
                loss_heat = solar.fuel_displaced[0]
                hr_op = solar.cd['heat recovery operational']
                net_heating =   -1* loss_heat
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = solar.generation_fuel_used[0]
            except AttributeError:
                net_gen = 0
                loss_heat = 0
                hr_op = solar.cd['heat recovery operational']
                net_heating = 0
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = 0
                
            try:
                levelized_cost = solar.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0

            try:
                break_even = solar.break_even_cost
            except AttributeError:
                break_even = 0
            
            l = [c, assumed_out, average_load, proposed_capacity, 
                 existing_capacity, wind_capacity, net_gen, loss_heat, hr_op,
                 net_heating, red_per_year, eff, diesel_price,
                 break_even,
                 levelized_cost,
                 solar.get_NPV_benefits(),
                 solar.get_NPV_costs(),
                 solar.get_NPV_net_benefit(),
                 solar.get_BC_ratio(),
                 solar.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    
    
    cols = ['Community',
            'Assumed  Output per 10kW Solar PV Array',
            'Average Diesel Load [kw]',
            'Solar Capacity Proposed [kW]',
            'Existing Solar Capacity [kW]',
            'Existing Wind Capacity [kW]',
            'Net Proposed Solar Generation [kWh]',
            'Loss of Recovered Heat from Proposed Solar [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption from Proposed Solar [gal]',
            'Proposed Solar Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Solar NPV benefits [$]',
            'Solar NPV Costs [$]',
            'Solar NPV Net benefit [$]',
            'Solar Benefit Cost Ratio',
            'notes']
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('&','and') + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# solar summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
