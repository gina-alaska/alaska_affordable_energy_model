"""
Air Source Heat Pump Residential Outputs
----------------------------------------

output functions for Air Source Heat Pump Residential component

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
        results from the model, dictionay with each community or project as key
        
    res_dir : path
        location to save file
    
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)
    
def communities_summary (coms, res_dir):
    """Saves the summary by: community residential_ashp_summary.csv
    
    Parameters
    ----------
    coms : dictionay
        results from the model, dictionay with each community or project as key
            
    res_dir : path
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
            
            ashp = coms[c][COMPONENT_NAME]
            
            kw_exess = ashp.monthly_value_table['kWh consumed'].max()/\
                                (24 * 31)
            try:
                peak_monthly_btu_hr_hh = ashp.peak_monthly_btu_hr_hh
            except AttributeError:
                peak_monthly_btu_hr_hh = 0
                    
            try:
                #~ ashp.get_electricity_prices()
                price =  ashp.electricity_prices[0]
                #~ print float(ashp.electricity_prices.ix[ashp.start_year])
            except AttributeError:
                
                price = 0
           
            intertie = ashp.cd['intertie']
            if type(intertie) is list:
                intertie  = intertie[0]
            else:
                intertie = ashp.cd['name']
                
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
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            l = [name, 
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
                 ashp.irr,
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
             'ASHP Residential Internal Rate of Return',
             'ASHP Residential Benefit-cost ratio',
             'Intertie',
             'notes'
             ]
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary by community\n"
        '# Community: ' + definitions.COMMUNITY + '\n'
        '# ASHP Residential Average Coefficient of Performance (COP): '
            'ratio of useful heating provided to work required\n'
        '# Number Houses: '
            'Estimated count of homes that would be heated by ASHP\n'
        '# ASHP Residential Peak Household Monthly Btu/hr: \n'
        '# Electricity Price [$/kWh]: '+ definitions.PRICE_ELECTRICITY + '\n'
        '# ASHP Residential kWh consumed per year: electricity consumed\n'
        '# ASHP Residential Excess Generation Capacity '
            ' Needed for Peak Monthly Load (kW): \n'
        '# ASHP Residential Displaced Heating Oil [Gal]:'
            ' Fuel that would be displaced by ASHP\n'
        '# Diesel Price - year 1 [$/gal]: ' + definitions.PRICE_DIESEL + '\n'
        '# Heating Fuel Price - year 1 [$/gal]:' + definitions.PRICE_HF + '\n'
        '# Break Even Heating Fuel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_HF + '\n'
        '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
        '# '+ COMPONENT_NAME +' NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
        '# '+ COMPONENT_NAME +' NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
        '# '+ COMPONENT_NAME +' NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
        '# '+ COMPONENT_NAME +' Internal Rate of Return: ' + definitions.IRR +'\n'
        '# '+ COMPONENT_NAME +' Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
        '# Intertie: Interie community is part of \n'
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
        displaced_hoil = round(comp.heating_oil_saved,0) if bc_ratio else 0
        
        add_kW = round(comp.monthly_value_table['kWh consumed'].max()/\
                                (24 * 31),0) if bc_ratio else 0
        
        
        
        if results[c]['community data'].intertie == 'parent' or \
                                                            c.find('+') != -1:
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
            k = 'Additional capacity needed (kW)'
            regions[c_region][k] += add_kW
            
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
            k = 'Additional capacity needed (kW)'
            regions[c_region][k] = add_kW
            
    cols = ['Number of communities in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects ($)',
                        'Net benefit of cost-effective projects ($)',
                        'Heating oil displaced by cost-effective projects (gallons)',
                        'Additional capacity needed (kW)']
                        
    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
    
    summary.ix['All Regions'] = summary.sum()  
    return summary
    
def save_regional_summary (summary, res_dir):
    """Saves the summary by region:  __regional_residential_ashp_summary.csv
    
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
    
