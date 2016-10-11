"""
outputs.py

    ouputs functions for Heat Recovery component
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
            
            comp = coms[c][COMPONENT_NAME]
            
            comp.get_diesel_prices()
            diesel_price = float(comp.diesel_prices[0].round(2))
            hfp = comp.cd['heating fuel premium']
            
            propsed_hr = comp.proposed_heat_recovery
            #~ eff = comp.cd["diesel generation efficiency"]
            
            try:
                break_even_cost = comp.break_even_cost
                levelized_cost_of_energy = comp.levelized_cost_of_energy
            except AttributeError:
                break_even_cost = np.nan
                levelized_cost_of_energy = np.nan
            
            l = [c, 
                 
                 
                 propsed_hr,
                 diesel_price,
                 hfp,
                 diesel_price + hfp,
                 #~ eff,
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
            #~ print e
            pass
    
    cols = ['Community',
        
            'Proposed Heat Recovery [gallons]',
            'Diesel price - year 1 [$/gal]',
            'Heating Fuel Premimum [$/gal]',
            'Heating Fuel Price - year 1 [$/gal]',
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Heat Recovery NPV benefits [$]',
            'Heat Recovery NPV Costs [$]',
            'Heat Recovery NPV Net benefit [$]',
            'Heat Recovery Internal Rate of Return',
            'Heat Recovery Benefit Cost Ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
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
    
    
    
    ## get the component (for projects)
    ## also figure out the needed start/end years
    projects = {}
    #~ print community
    projects, s1, e1 = wl.get_projects(web_object, community, 
                                       COMPONENT_NAME, 'heat_recovery')
    if np.isnan(modeled.get_net_benefit()).all() and projects == {}:
        raise RuntimeError, "no projects or modeling info" 
    
    sy = modeled.start_year
    ey = modeled.actual_end_year
    if np.isnan(modeled.get_net_benefit()).all() :
        sy = np.nan
        ey = np.nan

    start_year, end_year = wl.correct_dates (sy, s1, ey, e1)
    
    order = projects.keys()
    if not np.isnan(modeled.get_net_benefit()).all():
        projects['Modeled ' + COMPONENT_NAME] = modeled
        order = ['Modeled ' + COMPONENT_NAME] + order

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
           
    
    ## get generation fuel costs per year (modeled)
    base_cost = fuel_consumed  * diesel_price
    base_cost.name = 'Base Cost'
    
    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)
    
    
    #~ ## get generation fule used (modeled)
    base_con = fuel_consumed
    base_con.name = 'Base Consumption'
    table2 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'proposed_heat_recovery')
    
    
    ## info for modeled
   
        
    ests = modeled.comp_specs['estimate data']
    current = [
        {'words':'Waste Heat Recovery Operational', 
         'value': ests['Waste Heat Recovery Opperational']},
        {'words':'Add waste heat Avail', 'value': ests['Add waste heat Avail']},
        {'words':'Est. current annual heating fuel gallons displaced', 
         'value': ests['Est. current annual heating fuel gallons displaced']},
        {'words':'Est. potential annual heating fuel gallons displaced', 
         'value': ests['Est. potential annual heating fuel gallons displaced']},
    ]
        
    
    info = create_project_details_list(modeled)
         
    ## info table (list to send to template)
    
    info_for_projects = [{'name': 'Current System', 'info':current}]
    
    if not np.isnan(modeled.get_net_benefit()).all():
        info_for_projects.append({'name': 
                                    'Modeled '+ COMPONENT_NAME + ' Project',
                                  'info': info})
    
    ## get info for projects (updates info_for_projects )
    for p in order:
        project = projects[p]
        name = project.comp_specs['project details']['name']
        info = create_project_details_list(project)
            
        info_for_projects.append({'name':name,'info':info})
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Fuel Costs',
         'type': "'$'"},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Heating Fuel Consumed',
         'type': "'other'"}
            ]
        
    ## generate html
    pth = os.path.join(web_object.directory, community + '_' +\
                    COMPONENT_NAME.replace(' ','_').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME, 
                                    com = community ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),
                                    communities = web_object.get_all_coms()
                                    ))
                                    
                                    
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
        {'words':'Capital Cost ($)', 
            'value': costs},
        {'words':'Lifetime Savings ($)', 
            'value': benefits},
        {'words':'Net Lifetime Savings ($)', 
            'value': net_benefits},
        {'words':'Benefit Cost Ratio', 
            'value': BC},
            ]
