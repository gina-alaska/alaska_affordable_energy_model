"""
Non-residential Efficiency outputs
----------------------------------

output functions for Non-residential Efficiency component

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
    """Saves the summary by: community non-residentail_building_summary.csv
    
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
        if c.find('+') != -1:# or c.find("_intertie") != -1:
            continue
        try:
            com = coms[c][COMPONENT_NAME]
            savings = (com.baseline_HF_consumption -\
                      com.proposed_HF_consumption ) * constants.mmbtu_to_gal_HF
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            
            out.append([name,
                com.get_NPV_benefits(),com.get_NPV_costs(),
                com.get_NPV_net_benefit(),com.irr,com.get_BC_ratio(),
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
            
            
    cols = ['Community',
            'Non-residential Efficiency NPV Benefit',
            'Non-residential Efficiency NPV Cost',
            'Non-residential Efficiency NPV Net Benefit',
            
            'Non-residential Internal Rate of Return',
            'Non-residential Efficiency B/C Ratio',
            'Heating Oil Price - year 1',
            '$ per kWh - year 1',
            'Number Non-residential Buildings',
            'Non-residential Total Square Footage',
            'Breakeven Heating Fuel Price [$/gal heating oil equiv.]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Levelized Cost of Energy [$/kWh]',
            'Non-residential Heating oil equiv. Consumed(gal) - year 1',
            'Non-residential Electricity Consumed (kWh) - year 1',
            'Non-residential Efficiency Heating oil equiv. Saved[gal/year]',
            'Non-residential Efficiency Electricity Saved [kWh/year]']
            
    data = DataFrame(out,columns = cols).set_index('Community').round(2)
    f_name = os.path.join(res_dir, COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# non residental building component summary by community\n"
            '# Community: '+ definitions.COMMUNITY + '\n'
            '# Non-residential Efficiency NPV Benefit: ' + definitions.NPV_BENEFITS + '\n'
            '# Non-residential Efficiency NPV Cost: ' + definitions.NPV_COSTS + '\n'
            '# Non-residential Efficiency NPV Net Benefit: ' + definitions.NPV_NET_BENEFITS + '\n'
            '# Non-residential Internal Rate of Return: ' + definitions.IRR +'\n'
            '# Non-residential Efficiency B/C Ratio: ' + definitions.NPV_BC_RATIO + '\n'
            '# Heating Oil Price - year 1: ' + definitions.PRICE_HF + '\n'
            '# $ per kWh - year 1: ' + definitions.PRICE_ELECTRICITY + '\n'
            '# Number Non-residential Buildings: Number of buildings in the community.\n'
            '# Non-residential Total Square Footage: Total Square footage from buildings.\n'
            '# Breakeven Heating Fuel Price [$/gal heating oil equiv.]: ' + definitions.BREAK_EVEN_COST_HF + '\n'
            '# Levelized Cost of Energy [$/MMBtu]: ' + definitions.LCOE + '\n'
            '# Levelized Cost of Energy [$/kWh]: ' + definitions.LCOE + '\n'
            '# Non-residential Heating Oil equiv. Consumed(gal) - year 1: Heating energy consumed in a community with out improvments.\n'
            '# Non-residential Electricity Consumed (kWh) - year 1: Electricity consumed in a community without improvements.\n'
            '# Non-residential Efficiency Heating oil equiv. Saved[gal/year]: Heating energy saved in a community with improvments.\n'
            '# Non-residential Efficiency Electricity Saved [kWh/year]: Electricity consumed in a community with improvements.\n'))
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
            round((comp.baseline_HF_consumption -\
                      comp.proposed_HF_consumption ) * constants.mmbtu_to_gal_HF ,0) if bc_ratio else 0

        displaced_kWh = round(comp.baseline_kWh_consumption -\
                comp.proposed_kWh_consumption,0) if bc_ratio else 0

        if (c.find('+') != -1):
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
            k = 'Heating oil displaced yearly (gallons)'
            regions[c_region][k] += displaced_fuel
            k = 'kWh displaced yearly (kwh)'
            regions[c_region][k] += displaced_kWh
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Heating oil displaced yearly (gallons)'
            regions[c_region][k] = displaced_fuel
            k = 'kWh displaced yearly (kwh)'
            regions[c_region][k] = displaced_kWh
            
    cols = ['Number of communities/interties in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Heating oil displaced yearly (gallons)',
            'kWh displaced yearly (kwh)']
                        
    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
                        
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region
    
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
    
