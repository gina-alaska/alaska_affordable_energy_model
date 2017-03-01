"""
Heat Recovery Outputs
---------------------

output functions for Heat Recovery component

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
    """Saves the summary by: community heat_recovery_summary.csv
    
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
        #~ it = coms[c]['community data'].intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
            comp = coms[c][COMPONENT_NAME]
            
            comp.get_diesel_prices()
            diesel_price = float(comp.diesel_prices[0].round(2))
            hfp = comp.cd['heating fuel premium']
            
            propsed_hr = comp.proposed_heat_recovery
            #~ eff = comp.cd["diesel generation efficiency"]
            
            try:
                break_even_cost = comp.break_even_cost
                levelized_cost_of_energy = comp.levelized_cost_of_energy
            except AttributeError:
                break_even_cost = np.nan
                levelized_cost_of_energy = np.nan
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name,  
                 
                 
                 propsed_hr,
                 diesel_price,
                 hfp,
                 diesel_price + hfp,
                 #~ eff,
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
            #~ print e
            pass
    
    cols = ['Community',
        
            'Proposed Heat Recovery [gallons]',
            'Diesel price - year 1 [$/gal]',
            'Heating Fuel Premimum [$/gal]',
            'Heating Fuel Price - year 1 [$/gal]',
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Heat Recovery NPV benefits [$]',
            'Heat Recovery NPV Costs [$]',
            'Heat Recovery NPV Net benefit [$]',
            'Heat Recovery Internal Rate of Return',
            'Heat Recovery Benefit-cost ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary by community\n"
            '# Community: ' + definitions.COMMUNITY + '\n'
            '# Proposed Heat Recovery [gallons]: Proposed gallons of diesel saved \n'
            '# Diesel price - year 1 [$/gal]: ' + definitions.PRICE_DIESEL + '\n' 
            '# Heating Fuel Premimum [$/gal]: ' + definitions.PREMIUM + '\n'
            '# Heating Fuel Price - year 1 [$/gal]: ' + definitions.PRICE_HF + '\n'
            '# Break Even Heating Fuel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_HF + '\n'
            '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
            '# Heat Recovery NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
            '# Heat Recovery NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
            '# Heat Recovery NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
            '# Heat Recovery Internal Rate of Return: ' + definitions.IRR +'\n'
            '# Heat Recovery Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
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
        pandas DataFrame containg regional results
    
    """
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
        try:
            displaced_hoil = round(comp.propsed_hr,0) if bc_ratio else 0
        except StandardError as e:
            displaced_hoil = 0
        
        
        if results[c]['community data'].intertie == 'parent' or \
            not c.find('heat_recovery') != -1:
            #~ print c
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] += net_benefit
            k = 'Heating oil displaced by cost-effective projects (gallons)'
            regions[c_region][k] += displaced_hoil
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Heating oil displaced by cost-effective projects (gallons)'
            regions[c_region][k] = displaced_hoil
            
    
    cols = ['Number of communities in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Heating oil displaced by cost-effective projects (gallons)']
    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
    
    
    summary.ix['All Regions'] = summary.sum()  
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region:  __regional_heat_recovery_summary.csv
    
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
    
