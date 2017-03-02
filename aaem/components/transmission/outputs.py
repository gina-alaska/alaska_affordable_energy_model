"""
Transmission Outputs
--------------------

output functions for Transmission component

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
    """Saves the component summary by community
    
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
            # ??? NPV or year one
            it = coms[c][COMPONENT_NAME]
            connect_to = it.comp_specs['nearest community']\
                        ['Nearest Community with Lower Price Power']
                
            if it.reason == 'Not a transmission project.':
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
                
            
                
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name,  
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
                it.irr,
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
            'Transmission Internal Rate of Return',
            'Transmission Benefit-cost ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community to connect')
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
   
    fd = open(f_name, 'w')
    fd.write(("# Transmission component summary by community\n"
        '# Community to connect: name of main community.\n'
        '# Community/Intertie to connect to: name of secondary community.\n'
        '# Start Year: ' + definitions.START_YEAR + '\n'
        '# project phase: '+ definitions.PHASE + '\n'
        '# Miles of Transmission Line:'
            ' Distance transmission line needs to be.\n'
        '# Generation Displaced in community to connect [kWh]: Diesel '
            'generation displaced in community\n'
        '# Electricity Generated, Conserved, or transmitted [kWh]: \n'
        '# Loss of Recovered Heat from Genset in community to connect [gal]: \n'
        '# Heat Recovery Operational in community to connect: \n'
        '# Diesel Generator Efficiency in community to connect: Estimated '
            'efficiency of diesel generator in community in killowatt '
            'hours per gallon.\n'
        '# Diesel Generator Efficiency in community to connect to: Estimated'
            ' efficiency of diesel generator in community connected '
            'to in killowatt hours per gallon.\n'
        '# Diesel Price - year 1 [$/gal] in community to connect: '
            'Diesel fuel price in the community durning the frist year'
            ' of project operation.\n'
        '# Diesel Price - year 1 [$/gal] in community to connect to: '
            'Diesel fuel price in the community to connect to'
            ' durning the frist year of project operation.\n'
        '# Break Even Diesel Price [$/gal]: ' + definitions.BREAK_EVEN_COST_DIESEL + '\n'
        '# Annual Transmission loss percentage: Estimated transmission loss pecent.\n'
        '# Levelized Cost Of Energy [$/kWh]:' + definitions.LCOE + '\n'
        '# Status Quo generation Cost (Year 1): Estimated cost of generation in community if nothing changes\n'
        '# Proposed generation cost (Year 1):  Estimated cost of generation in community with improvments\n'
        '# Benefit from reduced generation cost (year 1): Difference in base and proposed cost of generation \n'
        '# Transmission NPV benefits [$]: '+ definitions.NPV_BENEFITS + '\n'
        '# Transmission NPV Costs [$]: ' + definitions.NPV_COSTS + '\n'
        '# Transmission NPV Net benefit [$]: ' + definitions.NPV_NET_BENEFITS + '\n'
        '# Transmission Internal Rate of Return: ' + definitions.IRR +'\n'
        '# vTransmission Benefit-cost ratio: ' + definitions.NPV_BC_RATIO +'\n'
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
            round(comp.pre_intertie_generation_fuel_used[0] - comp.intertie_offset_generation_fuel_used[0] ,0) if bc_ratio else 0

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
    
