"""
outputs.py

ouputs for diesel_efficiency component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

def component_summary (coms, res_dir):
    """
    generates the summary for diesel efficiency compoenent
    
    input:
        coms: set of resultes from model <dict>
        res_dir: path to results directory <string>
    
    output:
        saves diesel_efficiecy_summary.csv in res_dir
    
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['model'].cd.intertie
        if it is None:
            it = 'parent'
        if it == 'child' or c.find("+") != -1:
            continue
        #~ if c.find("_intertie") != -1:
            #~ continue
        try:
            comp = coms[c]['model'].comps_used[COMPONENT_NAME]
            
            comp.get_diesel_prices()
            diesel_price = float(comp.diesel_prices[0].round(2))
            try:
                average_load = comp.average_load
            except AttributeError:
                average_load = np.nan
            try:
                current_capacity = comp.comp_specs['data']\
                                            ['Total Capacity (in kW)']
            except AttributeError:
                current_capacity = np.nan
            try:
                max_capacity = comp.max_capacity
            except AttributeError:
                max_capacity = np.nan
            try:
                generation = comp.generation[0]
            except AttributeError:
                generation = np.nan
            try:
                baseline_eff = comp.baseline_diesel_efficiency
            except AttributeError:
                baseline_eff = np.nan
            try:
                proposed_eff = comp.proposed_diesel_efficiency
            except AttributeError:
                proposed_eff = np.nan
            try:
                baseline_fuel = comp.baseline_generation_fuel_use[0]
            except AttributeError:
                baseline_fuel = np.nan
            try:
                proposed_fuel = comp.proposed_generation_fuel_use[0]
            except AttributeError:
                proposed_fuel = np.nan
            
            try:
                break_even_cost = comp.break_even_cost
                levelized_cost_of_energy = comp.levelized_cost_of_energy
            except AttributeError:
                break_even_cost = np.nan
                levelized_cost_of_energy = np.nan
            
            l = [c, 
                 average_load,
                 current_capacity,
                 max_capacity,
                 generation,
                 
                 baseline_eff,
                 proposed_eff,
                 baseline_fuel,
                 proposed_fuel,
                 diesel_price,
                 
                 break_even_cost,
                 levelized_cost_of_energy,
                 comp.get_NPV_benefits(),
                 comp.get_NPV_costs(),
                 comp.get_NPV_net_benefit(),
                 comp.get_BC_ratio(),
                 comp.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            print e
            pass
    
    cols = ['Community', 'Average Load [kW]', 'Current Capacity [kW]',
            'Proposed Capacity [kW]', 'Generation - year 1[kWh]',
            
            'Baseline Diesel Generator Efficiency [Gal/kWh]',
            'Proposed Diesel Generator Efficiency [Gal/kWh]',
            'Baseline Generation Fuel Consumption [Gal]',
            'Proposed Generation Fuel Consumption [Gal]',
            'Diesel price - year 1 [$/gal]',
            
            'Break Even Diesel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Diesel Efficiency NPV benefits [$]',
            'Diesel Efficiency NPV Costs [$]',
            'Diesel Efficiency NPV Net benefit [$]',
            'Diesel Efficiency Benefit Cost Ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
