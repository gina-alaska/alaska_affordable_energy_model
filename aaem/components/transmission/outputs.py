"""
outputs.py

    ouputs functions for Transmission Line component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants


def component_summary (coms, res_dir):
    """
    save the component summary
    
    pre:
        res_dir: is a directory 
        coms: set of results retuned from running the model.
            component should exist for some communites in coms
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
            it = coms[c][COMPONENT_NAME]
            connect_to = it.comp_specs['nearest community']\
                        ['Nearest Community with Lower Price Power']
                
            if it.reason == 'Not a transmission project':
                continue
            try:
                if it.connect_to_intertie:
                    connect_to += 'intertie'
            except AttributeError:
                pass
                
            start_yr = it.comp_specs['start year']
            
            dist = it.comp_specs['nearest community']['Distance to Community']
            
            it.get_diesel_prices()
            diesel_price = float(it.diesel_prices[0].round(2))
            
            try:
                diesel_price_it = float(it.intertie_diesel_prices[0].round(2))
            except AttributeError:
                diesel_price_it = np.nan
            
            
            if not it.comp_specs["project details"] is None:
                phase = it.comp_specs["project details"]['phase']
            else:
                phase = "Reconnaissance"
                
                
                
            heat_rec_opp = it.cd['heat recovery operational']
            
            try:
                generation_displaced = it.pre_intertie_generation[0]
            except AttributeError:
                generation_displaced = np.nan
            
            try:
                generation_conserved = it.intertie_offset_generation[0]
            except AttributeError:
                generation_conserved = np.nan
                    
            try:
                lost_heat = it.lost_heat_recovery[0]
            except AttributeError:
                lost_heat = np.nan
                
            try:
                levelized_cost = it.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0

            try:
                break_even = it.break_even_cost
            except AttributeError:
                break_even = 0
            
            eff = it.cd["diesel generation efficiency"]
            try:
                pre_price = it.pre_intertie_generation_fuel_used[0] * \
                            diesel_price
            except AttributeError:
                pre_price = np.nan
                
            try:
                post_price = it.intertie_offset_generation_fuel_used[0] * \
                            diesel_price_it
            except AttributeError:
                post_price = np.nan
                
            try:
                eff_it = it.intertie_generation_efficiency
            except AttributeError:
                eff_it = np.nan
                
            
                
            
            try:
                losses = it.annual_tranmission_loss
            except AttributeError:
                losses = np.nan
                
            
                
            l = [c, 
                connect_to,
                start_yr,
                phase,
                dist,

                generation_displaced,
                generation_conserved,
                
                lost_heat,
                heat_rec_opp,
                
                eff,
                eff_it,
                diesel_price,
                diesel_price_it,
                break_even,
                losses,
                
                levelized_cost,

                pre_price,
                post_price,
                pre_price - post_price,
                

                it.get_NPV_benefits(),
                it.get_NPV_costs(),
                it.get_NPV_net_benefit(),
                it.get_BC_ratio(),
                it.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            print e
            pass
        
    
    cols = ['Community to connect',
            'Community/Intertie to connect to',
            'Start Year',
            'Project Phase',
            'Miles of Transmission Line',
            
            'Generation Displaced in community to connect [kWh]',
            'Electricity Generated, Conserved, or transmitted [kWh]',
            
            'Loss of Recovered Heat from Genset in community to connect  [gal]',
            'Heat Recovery Operational in community to connect',
           
           
            'Diesel Generator Efficiency in community to connect',
            'Diesel Generator Efficiency in community to connect to',
            'Diesel Price - year 1 [$/gal] in community to connect',
            'Diesel Price - year 1 [$/gal] in community to connect to',
            'Break Even Diesel Price [$/gal]',
            'Annual Transmission loss percentage',
            

            'Levelized Cost Of Energy [$/kWh]',

            'Status Quo generation Cost (Year 1)',
            'Proposed generation cost (Year 1)',
            'Benefit from reduced generation cost (year 1)',
            
            'Transmission NPV benefits [$]',
            'Transmission NPV Costs [$]',
            'Transmission NPV Net benefit [$]',
            'Transmission Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community to connect')
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')

    data.to_csv(f_name, mode='w')
