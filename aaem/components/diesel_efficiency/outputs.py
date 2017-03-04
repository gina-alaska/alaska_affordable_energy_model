"""
Diesel Efficiency Outputs
-------------------------

output functions for Diesel Efficiency component

"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order, definitions


## component summary
def component_summary (results, res_dir):
    """Creates the regional and communites summary for the component in provided 
    directory
    
    Parameters
    ----------
    results : dictionay
        results from the model, dictionay with each community or project 
        as key
    res_dir :  path
        location to save file
    
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """Saves the summary by: community diesel_efficiency_summary.csv
    
    Parameters
    ----------
    coms : dictionay
        results from the model, dictionay with each community or project 
        as key
    res_dir :  path
        location to save file
    
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child' or c.find("+") != -1:
            continue
        #~ if c.find("_intertie") != -1:
            #~ continue
        try:
            comp = coms[c][COMPONENT_NAME]
            
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
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            l = [name,  
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
                 comp.irr,
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
            'Diesel Efficiency Internal Rate of Return',
            'Diesel Efficiency Benefit-cost ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary by community\n"
            '# Community: ' + definitions.COMMUNITY + '\n' 
            '# Average Load [kW]: ' + definitions.DIESEL_LOAD + '\n'
            '# Current Capacity [kW]: \n'
            '# Proposed Capacity [kW]: \n'
            '# Generation - year 1[kWh]: \n'
            '# Baseline Diesel Generator Efficiency [Gal/kWh]: Current diesel generator efficiency\n'
            '# Proposed Diesel Generator Efficiency [Gal/kWh]: Proposed diesel generator efficiency\n'
            '# Baseline Generation Fuel Consumption [Gal]: Current diesel used for generation\n'
            '# Proposed Generation Fuel Consumption [Gal]: Proposed diesel used for generation\n'
            '# Diesel price - year 1 [$/gal]: ' + definitions.PRICE_DIESEL + '\n' 
            '# Break Even Diesel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_HF + '\n'
            '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
            '# Diesel Efficiency NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
            '# Diesel Efficiency NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
            '# Diesel Efficiency NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
            '# Diesel Efficiency Internal Rate of Return: ' + definitions.IRR +'\n'
            '# Diesel Efficiency Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
            '# notes: '+ definitions.NOTES +'\n'))
    fd.close()
    data.to_csv(f_name, mode='a')

def create_regional_summary (results):
    """Creates the regional summary
    
    Parameters
    ----------
    results : dictionay
        results from the model, dictionay with each community or project 
        as key
            
    Returns
    -------
    DataFrame 
        containg regional results
    
    """
    #~ print "start"
    regions = {}
    for c in results:
        c_region = results[c]['community data'].get_item('community','region')
        comp = results[c][COMPONENT_NAME]
        #~ print comp
        bc_ratio = comp.get_BC_ratio()
        bc_ratio = (not type(bc_ratio) is str) and (not np.isinf(bc_ratio))\
                                              and (bc_ratio > 1)
        #~ print bc_ratio ,comp.get_BC_ratio()
        #~ return
        capex = round(comp.get_NPV_costs(),0)  if bc_ratio else 0
        net_benefit = round(comp.get_NPV_net_benefit(),0)  if bc_ratio else 0
       
        displaced_fuel = \
            round(comp.baseline_generation_fuel_use[0] - \
                    comp.proposed_generation_fuel_use[0],0) if bc_ratio else 0

        if (results[c]['community data'].intertie == 'child' or c.find('+') != -1):
            #~ print c
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities/interties in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] += net_benefit
            k = 'Generation diesel displaced by cost-effective projects (gallons)'
            regions[c_region][k] += displaced_fuel
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Generation diesel displaced by cost-effective projects (gallons)'
            regions[c_region][k] = displaced_fuel
            
    cols = ['Number of communities/interties in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Generation diesel displaced by cost-effective projects (gallons)']
    
    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
    
    
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region:  __regional_diesel_efficiency_summary.csv
    
    Parameters
    ----------
    summary : Dataframe
        compiled regional results
    res_dir :  path
        location to save file

    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
