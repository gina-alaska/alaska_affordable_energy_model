"""
outputs.py

ouputs for diesel_efficiency component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME, DESCRIPTION
import aaem.constants as constants
from aaem.components import comp_order
import aaem.web_lib as wl

## component summary
def component_summary (results, res_dir):
    """ 
    creats the regional and communites summary for the component 
    
    inputs:
        results: results from the model
        res_dir: location to save file
    
    outputs:
        saves a summaries in res-dir
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
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
            'Diesel Efficiency Benefit Cost Ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')

def create_regional_summary (results):
    """
    create the regional summary for this component
    
    inputs:
        results: results from the model
       
    outputs:
        returns summary as a data frame
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
            k = 'Investment needed for cost-effective projects'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects'
            regions[c_region][k] += net_benefit
            k = 'Generation diesel displaced by cost-effective projects'
            regions[c_region][k] += displaced_fuel
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects'
            regions[c_region][k] = net_benefit
            k = 'Generation diesel displaced by cost-effective projects'
            regions[c_region][k] = displaced_fuel
            
    summary = DataFrame(regions).T[['Number of communities/interties in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects',
                        'Net benefit of cost-effective projects',
                    'Generation diesel displaced by cost-effective projects']]
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """ 
    inputs:
        summary: summary dataframe
        res_dir: location to save file
    
    outputs:
        save a regional summary in res-dir
    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')

def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.component_html
    
    ## get the component (the modelded one)
  
    modeled = web_object.results[community][COMPONENT_NAME]
    start_year = modeled.start_year
    end_year = modeled.actual_end_year
    
    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}
    
    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast

    generation = fc.generation_by_type['generation diesel'].\
                                        ix[start_year:end_year]
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1)
           
    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']
    
    
    
    ## get generation fuel costs per year (modeled)
    base_cost = generation/eff * diesel_price
    base_cost.name = 'Base Cost'
    
    
    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)
    
    
    ## get generation fule used (modeled)
    base_con = generation/eff 
    base_con.name = 'Base Consumption'
    table2 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'get_fuel_total_saved()')
    
    
    
    current = wl.create_electric_system_summary (web_object.results[community])
    
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                         {'name':'Modeled Diesel Efficiency Project',
                          'info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Electricity Generation Fuel Costs',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Electricity Generation ',
         'type': "'other'",'plot': True,}
            ]
        
    ## generate html
    ## generate html
    msg = None
    if community in web_object.bad_data_coms:
        msg = web_object.bad_data_msg
    
    pth = os.path.join(web_object.directory, community.replace("'",''),
                    COMPONENT_NAME.replace(' ','_').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME, 
                                    com = community ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),
                                    communities = web_object.get_all_coms(),
                                    description =  DESCRIPTION,
                                    metadata = web_object.metadata,
                                    message = msg
                                    ))
                                    
                                    
def create_project_details_list (project):
    """
    makes a projects details section for the html
    """
    return [
       {'words':'Capital Cost ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit Cost Ratio', 
            'value': '{:,.3f}'.format(project.get_BC_ratio())},
        {'words':'Efficiency Improvment', 
            'value': '{:,.0f}%'.format(project.comp_specs\
            ['efficiency improvment'] * 100)},
        
            ]
