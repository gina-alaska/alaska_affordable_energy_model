"""
Wind Power Outputs
------------------

output functions for Wind Power component

"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order, definitions


from datetime import datetime

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
    """Saves the component summary by community
    
    Parameters
    ----------
    coms : dictionay
        results from the model, dictionay with each community or project 
        as key
    res_dir :  path
        location to save file
    """
    #~ return
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            wind = coms[c][COMPONENT_NAME]
            
            start_yr = wind.comp_specs['start year']
            wind.get_diesel_prices()
            diesel_price = float(wind.diesel_prices[0].round(2))
            phase = wind.comp_specs["project details"]['phase']
            average_load = wind.average_load
            existing_load = wind.comp_specs['resource data']\
                                            ['existing wind']
            existing_solar = wind.comp_specs['resource data']['existing solar']
            wind_class = float(wind.comp_specs['resource data']\
                                                ['Assumed Wind Class']) 
            proposed_load =  wind.load_offset_proposed
            cap_fac = float(wind.comp_specs['resource data']\
                                            ['assumed capacity factor'])
            heat_rec_opp = wind.cd['heat recovery operational']
            try:
                #~ offset = wind.load_offset_proposed
                net_gen_wind = wind.net_generation_wind
                decbb = wind.diesel_equiv_captured
                
                
                loss_heat = wind.loss_heat_recovery
                electric_diesel_reduction=wind.electric_diesel_reduction
                
                diesel_red = wind.reduction_diesel_used
                levelized_cost = wind.levelized_cost_of_energy
                break_even = wind.break_even_cost
                eff = wind.cd["diesel generation efficiency"]
                
            except AttributeError:
                offset = 0
                net_gen_wind = 0
                decbb = 0
                electric_diesel_reduction=0
                loss_heat = 0
                
                diesel_red = 0
                levelized_cost = 0
                break_even = 0
                eff = wind.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_wind / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            l = [name,  
                start_yr,
                phase,
                wind_class, 
                average_load, 
                proposed_load,
                existing_load,
                existing_solar,
                cap_fac,
                net_gen_wind,
                decbb, 
                loss_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                eff,
                diesel_price,
                break_even,
                levelized_cost,
                wind.get_NPV_benefits(),
                wind.get_NPV_costs(),
                wind.get_NPV_net_benefit(),
                wind.irr,
                wind.get_BC_ratio(),
                wind.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Start Year',
            'Project phase',
            'Assumed Wind Class',
            'Average Diesel Load [kW]',
            'Wind Capacity Proposed [kW]',
            'Existing Wind Capacity [kW]',
            'Existing Solar Capacity [kW]',
            'Assumed Wind Class Capacity Factor [%]',
            'Net Proposed Wind Generation [kWh]',
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption [gal]',
            'Wind Power Reduction in Utility Diesel Consumed per year [gal]',
            'Diesel Generator Efficiency','Diesel Price - year 1 [$/gal]',
            'Breakeven Diesel Price [$/gal]',
            'Levelized Cost Of Energy [$/kWh]',
            'Wind NPV benefits [$]',
            'Wind NPV Costs [$]',
            'Wind NPV Net benefit [$]',
            'Wind Internal Rate of Return',
            'Wind Benefit-cost ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# wind summary\n" 
        '# Breakdown by community of potential wind power improvements'
        '# \n'
        '# Community: ' + definitions.COMMUNITY + '\n'
        '# Start Year: ' + definitions.START_YEAR + '\n'
        '# Project phase: '+ definitions.PHASE + '\n'
        '# Assumed Wind Class: Wind power density class\n'
        '# Average Diesel Load [kW]: ' + definitions.DIESEL_LOAD +'\n'
        '# Wind Capacity Proposed [kW]: Proposed additional capacity for wind'
            ' generation in kilowatts.\n'
        '# Existing Wind Capacity [kW]: Existing wind generation capacity'
            ' in kilowatts.\n'
        '# Existing Solar Capacity [kW]: Existing solar generation capacity'
            ' in kilowatts.\n'
        '# Assumed Wind Class Capacity Factor [%]:\n'
        '# Net Proposed Wind Generation [kWh]: Proposed wind net generation'
            ' in kilowatt-hours.\n'
        '# Heating Oil Equivalent Captured by Secondary Load [gal]: \n'
        '# Loss of Recovered Heat from Genset [gal]: \n'
        '# Heat Recovery Operational: ' + definitions.HR_OP + '\n'
        '# Net in Heating Oil Consumption [gal]: \n'
        '# Wind Power Reduction in Utility Diesel Consumed per year [gal]: Estimated '
            'Reduction in utility diesel if wind power system is '
            'installed/upgraded. In gallons per year\n'
        '# Diesel Generator Efficiency: '+ definitions.GEN_EFF + ' \n'
        '# Diesel Price - year 1 [$\gal]: ' + definitions.PRICE_DIESEL + '\n'
        '# Breakeven Diesel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_DIESEL + '\n'
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
       
        displaced_fuel = \
            round(comp.electric_diesel_reduction,0) if bc_ratio else 0

        if (results[c]['community data'].intertie == 'child' or c.find('+') != -1) and not c.find('wind') != -1:
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
    
