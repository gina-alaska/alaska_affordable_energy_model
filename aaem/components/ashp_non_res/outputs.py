"""
Air Source Heat Pump Non-residential Outputs
---------------------

output functions for Air Source Heat Pump Non-residential component

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
    """Saves the summary by: community non_residential_ashp_summary.csv
    
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
                tcr = ashp.total_cap_required
                price =  float(ashp.electricity_prices.ix[ashp.start_year])
                #~ print float(ashp.electricity_prices.ix[ashp.start_year])
            except AttributeError:
                price = 0
                tcr = 0

            try:
                intertie = coms[c]['community data'].parent
            except AttributeError:
                intertie = c
               
            try:
                break_even = ashp.break_even_cost
            except AttributeError:
                break_even = 0
               
            
            try:
                levelized_cost = ashp.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
                
            ashp.get_diesel_prices()
            diesel_price = float(ashp.diesel_prices[0].round(2))
            hf_price =  diesel_price + ashp.cd['heating fuel premium'] 
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name, 
                 ashp.average_cop,
                 ashp.heat_displaced_sqft,
                 tcr,
                 price,
                 ashp.electric_consumption,
                 kw_exess,
                 ashp.heating_oil_saved,
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
            #~ print e
            pass
    
    cols = ['Community',
            "ASHP Non-Residential Average Coefficient of Performance (COP)",
            'Heat Displacement square footage [Sqft]',
            'ASHP Non-Residential Total Nameplate Capacity Needed',
            'Electricity Price [$/kWh]',
            'ASHP Non-Residential kWh consumed per year',
            "ASHP Non-Residential Excess Generation Capacity"
                                        " Needed for Peak Monthly Load (kW)",
            "ASHP Non-Residential Displaced Heating Oil [Gal]",
            "Diesel Price - year 1 [$/gal]",
            "Heating Fuel Price - year 1 [$/gal]",
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost Of Energy [$/MMBtu]',
            'ASHP Non-Residential NPV benefits [$]',
            'ASHP Non-Residential NPV Costs [$]',
            'ASHP Non-Residential NPV Net benefit [$]',
            'ASHP Non-Residential Internal Rate of Return',
            'ASHP Non-Residential Benefit-cost ratio',
            'Intertie',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(" ","_") + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
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
    """Saves the summary by region:  __regional_non_residential_ashp_summary.csv
    
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
    
def generate_web_summary (web_object, community):
    """generate html summary for a community. 
    generates web_object.directory/community/ashp_non_residential.html and 
    associated csv files.
    
    Parameters
    ----------
    web_object: WebSummary
        a WebSummary object
    community: str
        community name
            
    See also
    --------
    aaem.web : 
        WebSummary object definition
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

    fuel_consumed = \
        fc.heating_fuel_dataframe['heating_fuel_total_consumed [gallons/year]']\
        .ix[start_year:end_year]
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1) + \
                        web_object.results[community]['community data'].\
                            get_item('community','heating fuel premium')
           
    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']
    
    
    
    ## get generation fuel costs per year (modeled)
    base_cost = fuel_consumed  * diesel_price
    base_cost.name = 'Base Cost'
    
    
    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)
    
    
    ## get generation fule used (modeled)
    base_con = fuel_consumed
    base_con.name = 'Base Consumption'
    table2 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'get_fuel_total_saved()')
    
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled non-residential air source heat pump project',
                          'info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Costs',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Heating Fuel Consumed for non-residential heating',
         'type': "'other'",'plot': True,}
            ]
        
    ## generate html
    ## generate html
    msg = None
    if community in web_object.bad_data_coms:
        msg = web_object.bad_data_msg
    
    pth = os.path.join(web_object.directory, community.replace("'",''),
                    COMPONENT_NAME.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME, 
                                    com = community.replace("'",'') ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),
                                    
                                    description =  DESCRIPTION,
                                    metadata = web_object.metadata,
                                    message = msg
                                    ))





def create_project_details_list (project):
    """makes a projects details section for the html
    
    Parameters
    ----------
    projcet: HeatRecovery
        A HeatRecovery object thats run function has been called
            
    Returns
    -------
        A dictionary with values used by summary
    """
    try:
        costs = '${:,.0f}'.format(project.get_NPV_costs())
    except ValueError:
        costs = project.get_NPV_costs()
        
    try:
        benefits = '${:,.0f}'.format(project.get_NPV_benefits())
    except ValueError:
        benefits = project.get_NPV_benefits()
        
    try:
        net_benefits = '${:,.0f}'.format(project.get_NPV_net_benefit())
    except ValueError:
        net_benefits = project.get_NPV_net_benefit()
       
    try:
        BC = '{:,.1f}'.format(project.get_BC_ratio())
    except ValueError:
        BC = project.get_BC_ratio()
    
    return [
        {'words':'Capital cost ($)', 
            'value': costs},
        {'words':'Lifetime savings ($)', 
            'value': benefits},
        {'words':'Net lifetime savings ($)', 
            'value': net_benefits},
        {'words':'Benefit-cost ratio', 
            'value': BC},
        #~ {'words':"btu/hrs", 
            #~ 'value': project.comp_specs['btu/hrs'] },
        #~ {'words':"Cost per btu/hrs", 
            #~ 'value': project.comp_specs['cost per btu/hrs'] },
            ]

