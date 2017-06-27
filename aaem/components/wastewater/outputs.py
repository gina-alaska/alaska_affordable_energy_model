"""
Water Wastewater Outputs
------------------------

output functions for Water Wastewater component

"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order, definitions



## component summary
def component_summary (results, res_dir):
    """Creates the regional and communities summary for the component in provided 
    directory
    
    Parameters
    ----------
    results : dictionary
        results from the model, dictionary with each community or project 
        as key
    res_dir :  path
        location to save file
    
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """Saves the component summary by community
    
    Parameters
    ----------
    coms : dictionary
        results from the model, dictionary with each community or project 
        as key
    res_dir :  path
        location to save file
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            www = coms[c][COMPONENT_NAME]
            try:
                oil_p, elec_p =  www.hoil_price[0], www.elec_price[0]
            except AttributeError:
                oil_p, elec_p = 0,0
            
            savings = (www.baseline_HF_consumption -\
                      www.proposed_HF_consumption) * constants.mmbtu_to_gal_HF
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            
            out.append([name,
                www.get_NPV_benefits(),www.get_NPV_costs(),
                www.get_NPV_net_benefit(),www.irr,www.get_BC_ratio(),
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
            
            
    cols = ['Community',
            'Water/Wastewater Efficiency NPV Benefit',
            'Water/Wastewater Efficiency NPV Cost',
            'Water/Wastewater Efficiency NPV Net Benefit',
            'Water/Wastewater Internal Rate of Return',
            'Water/Wastewater Efficiency B/C Ratio',
            'Heating Oil Price - year 1',
            '$ per kWh - year 1',
            #~ 'Number Water/Wastewater Buildings',
            #~ 'Water/Wastewater Total Square Footage',
            'Break Even Diesel Price [$/gal heating oil equiv.]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Levelized Cost of Energy [$/kWh]',
            'Water/Wastewater Heating Oil Equiv. Consumed (gal) - year 1',
            'Water/Wastewater Electricity Consumed (kWh) - year 1',
            'Water/Wastewater Efficiency Heating Oil Equiv. Saved [gal/year]',
            '# Water/Wastewater Efficiency Electricity Saved [kWh/year]']
            
    data = DataFrame(out,columns = cols).set_index('Community').round(2)
    f_name = os.path.join(res_dir,
                    COMPONENT_NAME.lower().replace(' ','_').\
                    replace('&','and') + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# non residential building component summary by community\n"
        '# \n'
        '# Community: '+definitions.COMMUNITY+'\n'
        '# Water/Wastewater Efficiency NPV Benefit: '+definitions.NPV_BENEFITS+'\n'
        '# Water/Wastewater Efficiency NPV Cost: '+definitions.NPV_COSTS+'\n'
        '# Water/Wastewater Efficiency NPV Net Benefit: '+definitions.NPV_NET_BENEFITS+'\n'
        '# Water/Wastewater Internal Rate of Return: '+definitions.IRR+'\n'
        '# Water/Wastewater Efficiency B/C Ratio: '+definitions.NPV_BC_RATIO+'\n'
        '# Heating Oil Price - year 1:'
            ' Heating Oil Price year one of project\n'
        '# $ per kWh - year 1: Electricity Price year one of project\n'
        '# Break Even Diesel Price [$/gal heating oil equiv.]: '+definitions.BREAK_EVEN_COST_DIESEL+'\n'
        '# Levelized Cost of Energy [$/MMBtu]: \n'
        '# Levelized Cost of Energy [$/kWh]: \n'
        '# Water/Wastewater Heating Oil Equiv. Consumed (gal) - year 1:'
            ' heating oil equivalent consumed by water wastewater system\n'
        '# Water/Wastewater Electricity Consumed (kWh) - year 1:'
            ' Electricity consumed by water wastewater system\n'
        '# Water/Wastewater Efficiency Heating Oil Equiv. Saved [gal/year]:\n'
        '# Water/Wastewater Efficiency Electricity Saved [kWh/year]:\n'))
    fd.close()
    data.to_csv(f_name, mode='a')

def create_regional_summary (results):
    """Creates the regional summary
    
    Parameters
    ----------
    results : dictionary
        results from the model, dictionary with each community or project 
        as key
            
    Returns
    -------
    DataFrame 
        containing regional results
    
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
                      comp.proposed_HF_consumption)[0] * constants.mmbtu_to_gal_HF ,0) if bc_ratio else 0
                      
        displaced_kWh = round(comp.baseline_kWh_consumption[0] -\
                comp.proposed_kWh_consumption[0],0) if bc_ratio else 0

        if (c.find('+') != -1 or c.find("_intertie") != -1):
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
            
            k = 'Heating oil equiv. displaced yearly'
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
            
            k = 'Heating oil equiv. displaced yearly'
            regions[c_region][k] = displaced_fuel
            k = 'kWh displaced yearly (kwh)'
            regions[c_region][k] = displaced_kWh
            
    cols = ['Number of communities/interties in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Heating oil equiv. displaced yearly',
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
    summary : DataFrame
        compiled regional results
    res_dir :  path
        location to save file

    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
    
