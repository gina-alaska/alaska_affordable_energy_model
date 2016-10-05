"""
outputs.py

    ouputs functions for Biomass - Pellet component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order
import aaem.web_lib as wl

## component summary
def component_summary (coms, res_dir):
    """
    save thes the summary for biomass pellet
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
            
            
            l = [c, 
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
                 biomass.get_BC_ratio(),
                 biomass.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    try:
        cols = ['Community',
            'Biomass Pellet Maximum Boiler Output [Btu/hr]',
            'Biomass Pellet Heat Displacement square footage [Sqft]',
            'Proposed ' + biomass.biomass_type + " Consumed [" + \
                                                    biomass.units +"]",
            'Price [$/' + biomass.units + ']',
            "Energy Density [Btu/" + biomass.units + "]",
            'Biomass Pellet Displaced Heating Oil [Gal]',
            "Heating Fuel Price - year 1 [$/gal]",
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost Of Energy [$/MMBtu]',
            'biomass Pellet NPV benefits [$]',
            'Biomass Pellet NPV Costs [$]',
            'Biomass Pellet NPV Net benefit [$]',
            'Biomass Pellet Benefit Cost Ratio',
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
    
def generate_web_summary (web_object, community):
    """
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
    projects = {'Modled ' + COMPONENT_NAME:  modeled}
    
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
    
    ## info for modled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled biomass Project','info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Fuel costs per year',
         'type': "'$'"},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Heating Fuel Consumed gallons per year',
         'type': "'other'"}
            ]
        
    ## generate html
    ## generate html
    pth = os.path.join(web_object.directory, community + '_' +\
                    COMPONENT_NAME.replace(' ','_').replace(' ','_').replace('(','').replace(')','').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME, 
                                    com = community ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ))
    





def create_project_details_list (project):
    """
    makes a projects details section for the html
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
        BC = '{:,.2f}'.format(project.get_BC_ratio())
    except ValueError:
        BC = project.get_BC_ratio()
    
    return [
        {'words':'Captial Cost ($)', 
            'value': costs},
        {'words':'Lifetime Savings ($)', 
            'value': benefits},
        {'words':'Net Lifetime Savings ($)', 
            'value': net_benefits},
        {'words':'Benefit Cost Ratio', 
            'value': BC},
        {'words':"Energy Density [Btu/" + project.units + "]", 
            'value': project.comp_specs['energy density'] },
        {'words':"Capacity Factor", 
            'value': project.comp_specs['data']['Capacity Factor'] },
            ]


