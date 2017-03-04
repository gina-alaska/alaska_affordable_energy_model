"""
Solar Power Outputs
-------------------

output functions for Solar Power component

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
    """Saves the summary by: community Solar_power_summary.csv
    
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
        if it == 'child':
            continue
        try:
            solar = coms[c][COMPONENT_NAME]

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
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            l = [name,  assumed_out, average_load, proposed_capacity, 
                 existing_capacity, wind_capacity, net_gen, loss_heat, hr_op,
                 net_heating, red_per_year, eff, diesel_price,
                 break_even,
                 levelized_cost,
                 solar.get_NPV_benefits(),
                 solar.get_NPV_costs(),
                 solar.get_NPV_net_benefit(),
                 solar.irr,
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
            
            'Solar Internal Rate of Return',
            'Solar Benefit-cost ratio',
            'notes']
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('&','and') + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# solar summary\n"
        '# Community: name of community/project.\n'
        '# Assumed  Output per 10kW Solar PV Array: '
            'Assumed power out put of solar pannel\n'
        '# Average Diesel Load [kw]: '
            'Average diesel generation load in a community\n'
        '# Solar Capacity Proposed [kW]: ' 
            'Proposed generation offset by solar system\n'
        '# Existing Solar Capacity [kW]: '
            'Generation capacity of existing solar systems in community\n'
        '# Existing Wind Capacity [kW]: '
            'Generation capacity of existing wind systems in community\n'
        '# Net Proposed Solar Generation [kWh]: '
            'Net electric generation from new systems in kilowatt hours\n'
        '# Loss of Recovered Heat from Proposed Solar [gal]: '
            'Loss in heat recovery cauesd by new solar systems.\n'
        '# Heat Recovery Operational: ' + definitions.HR_OP + '\n'
        '# Net Change in Heating Oil Consumption from Proposed Solar [gal]:'
            ' Change in heating oil consumption that would be caused by '
            'improvments\n'
        '# Proposed Solar Reduction in Utility Diesel Consumed per year: '
            'Reduction in generation diesel from proposed solar system.\n'
        '# Diesel Denerator Efficiency: '+ definitions.GEN_EFF + ' \n '
        '# Diesel Price - year 1 [$\gal]: ' + definitions.PRICE_DIESEL + '\n'
        '# Break Even Diesel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_DIESEL + '\n'
        '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
        '# Wind power NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
        '# Wind power NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
        '# Wind power NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
        '# Wind power Internal Rate of Return: ' + definitions.IRR +'\n'
        '# Wind power Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
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
       
        #~ try:
        displaced_fuel = \
                round(comp.generation_fuel_used[0],0) if bc_ratio else 0
        #~ except StandardError as e:
            #~ print e

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
    
