"""
outputs.py

    ouputs functions for Hydropower component
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
            # ??? NPV or year one
            hydro = coms[c]['Hydropower']
            
            start_yr = hydro.comp_specs['start year']
            hydro.get_diesel_prices()
            diesel_price = float(hydro.diesel_prices[0].round(2))
            #~ print hydro.diesel_prices[0]
            if not hydro.comp_specs["project details"] is None:
                phase = hydro.comp_specs["project details"]['phase']
            else:
                phase = "Reconnaissance"

            name = hydro.comp_specs["project details"]['name']
            
            average_load = hydro.average_load
            proposed_load =  hydro.load_offset_proposed
            
            
            heat_rec_opp = hydro.cd['heat recovery operational']
            
           
            net_gen_hydro = hydro.net_generation_proposed
            
            captured_energy = hydro.captured_energy
            
            
            lost_heat = hydro.lost_heat_recovery
            electric_diesel_reduction= hydro.generation_diesel_reduction
            
            diesel_red = hydro.captured_energy - hydro.lost_heat_recovery
            
            eff = hydro.cd["diesel generation efficiency"]
            
            levelized_cost = hydro.levelized_cost_of_energy
            break_even = hydro.break_even_cost
            #~ except AttributeError:
                #~ offset = 0
                #~ net_gen_hydro = 0
                #~ decbb = 0
                #~ electric_diesel_reduction=0
                #~ loss_heat = 0
                
                #~ diesel_red = 0
                #~ eff = hydro.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_hydro / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            l = [c, 
                name,
                start_yr,
                phase,

                average_load, 
                proposed_load,
                net_gen_hydro,
                
                captured_energy, 
                lost_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                
                eff,
                diesel_price,
                break_even,
                levelized_cost,
                hydro.get_NPV_benefits(),
                hydro.get_NPV_costs(),
                hydro.get_NPV_net_benefit(),
                hydro.get_BC_ratio(),
                hydro.reason
            ]
            out.append(l)
        except (KeyError,AttributeError,TypeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Project Name',
            'Start Year',
            'project phase',
            
            'Average Diesel Load [kw]',
            'Wind Capacity Proposed [kW]',
            'Net Proposed Hydro Generation [kWh]',
            
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net Reduction in Heating Oil Consumption [gal]',
            'Hydro Power Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Hydro NPV benefits [$]',
            'Hydro NPV Costs [$]',
            'Hydro NPV Net benefit [$]',
            'Hydro Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')

    data.to_csv(f_name, mode='w')
