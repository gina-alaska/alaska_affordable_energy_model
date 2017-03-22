"""
Biomass cordwood outputs
------------------------

output functions for Biomass Cordwood component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem.web_lib as wl

COMPONENT_NAME = "Biomass for Heat (Cordwood)"
DESCRIPTION = """
    This component calculates the potential heating oil offset by installing new cordwood boilers for 30% of non-residential square footage. 
"""

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
    """Saves the summary by: community biomass_cordwood_summary.csv
    
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
            
           
            biomass = coms[c][COMPONENT_NAME]
            
            
            
            biomass.get_diesel_prices()
            diesel_price = float(biomass.diesel_prices[0].round(2))
            hf_price = diesel_price + biomass.cd['heating fuel premium']   
            
            try:
                break_even = biomass.break_even_cost
            except AttributeError:
                break_even = 0
               
            
            try:
                levelized_cost = biomass.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name,  
                 biomass.max_boiler_output,
                 biomass.heat_displaced_sqft,
                 biomass.biomass_fuel_consumed,
                 biomass.fuel_price_per_unit,
                 biomass.comp_specs['energy density'],
                 biomass.heat_diesel_displaced,
                 hf_price,
                 break_even,
                 levelized_cost,
                 biomass.get_NPV_benefits(),
                 biomass.get_NPV_costs(),
                 biomass.get_NPV_net_benefit(),
                 biomass.irr,
                 biomass.get_BC_ratio(),
                 biomass.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    try:
        cols = ['Community',
            'Maximum Biomass Boiler Output [Btu/hr]',
            'Biomass Heat Displacement square footage [Sqft]',
            'Proposed ' + biomass.biomass_type + \
                            " Consumed [" + biomass.units +"]",
            'Price [$/' + biomass.units + ']',
            "Energy Density [Btu/" + biomass.units + "]",
            'Displaced Heating Oil by Biomass [Gal]',
            "Heating Fuel Price - year 1 [$/gal]",
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost Of Energy [$/MMBtu]',
            'Bioimass Cordwood NPV benefits [$]',
            'Biomass Cordwood NPV Costs [$]',
            'Biomass Cordwood NPV Net benefit [$]',
            'Biomass Cordwood Internal Rate of Return',
            'Biomass Cordwood Benefit-cost ratio',
            'notes'
                ]
    except UnboundLocalError:
        return
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
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
        displaced_hoil = round(comp.heat_diesel_displaced,0)  if bc_ratio else 0
        
        
        
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
    

    
def generate_web_summary (web_object, community):
    """generate html summary for a community. 
    generates web_object.directory/community/biomass_pellet.html and 
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
    template = web_object.env.get_template('component.html')
    
    ## get the component (the modelded one)
  
    modeled = web_object.results[community][COMPONENT_NAME]
    if modeled.reason != 'OK':
        raise RuntimeError, modeled.reason
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
                                    'heat_diesel_displaced')
    
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled biomass cordwood Project','info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Fuel Costs by non-residential sector',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Heating Fuel Consumed for non-residential sector',
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
        {'words':'Capital cost', 
            'value': costs},
        {'words':'Lifetime savings', 
            'value': benefits},
        {'words':'Net lifetime savings', 
            'value': net_benefits},
        {'words':'Benefit-cost ratio', 
            'value': BC},
        #~ {'words':"Energy density [Btu/" + project.units + "]", 
            #~ 'value': project.comp_specs['energy density'] },
        #~ {'words':"Capacity factor", 
            #~ 'value': 
            #~ '{:,.2f}%'.format(project.comp_specs['data']['Capacity Factor']) },
            ]
