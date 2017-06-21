"""
Heat Recovery Outputs
---------------------

output functions for Heat Recovery component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

import numpy as np

COMPONENT_NAME = "Heat Recovery"

DESCRIPTION = """
    This component calculates the potential heating oil offset by installing a new heat recovery System. Requires that at least a reconnaissance-level heat recovery study has been completed for the community to be run.
"""

def generate_web_summary (web_object, community):
    """generate html summary for a community. 
    generates web_object.directory/community/heat_recovery.html and 
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
    
    
    
    ## get the component (for projects)
    ## also figure out the needed start/end years
    projects = {}
    #~ print community
    projects, s1, e1 = wl.get_projects(web_object, community, 
                                       COMPONENT_NAME, 'heat_recovery')
    
    #~ print projects

    if projects == {}:
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

    try:
        fuel_consumed = \
        fc.heating_fuel_dataframe['heating_fuel_non-residential_consumed [gallons/year]']\
        .ix[start_year:end_year]
    except:
        fuel_consumed = \
        fc.heating_fuel_dataframe['heating_fuel_total_consumed [gallons/year]']\
        .ix[start_year:end_year] 
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            ix[start_year: end_year] + \
                        web_object.results[community]['community data'].\
                            get_item('community','heating fuel premium')
           
    diesel_price = diesel_price[diesel_price.columns[0]]
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
    try:
        current_hr = float(
            ests['Est. current annual heating fuel gallons displaced'])
        if not ests['Waste Heat Recovery Opperational'].lower == 'no' and\
           not np.isnan(current_hr):
            current_hr = '{:,.0f}'.format(
                ests['Est. current annual heating fuel gallons displaced'])
        elif ests['Waste Heat Recovery Opperational'].lower == 'no':
            current_hr = 0
        else:
            current_hr = "unknown"
    except ValueError:
        current_hr = "unknown"
        
    try:
        potential_hr = '{:,.0f}'.format(float(
            ests['Est. potential annual heating fuel gallons displaced']))
    except ValueError:
        potential_hr =\
            ests['Est. potential annual heating fuel gallons displaced']
        
    
    current = [
        {'words':'Waste Heat Recovery Operational', 
         'value': ests['Waste Heat Recovery Opperational']},
        {'words':'Identified as priority by HR working group', 
         'value': ests['Identified as priority by HR working group']},
        {'words':'Est. current annual heating fuel gallons displaced', 
         'value': current_hr},
        {'words':'Est. potential annual heating fuel gallons displaced', 
         'value': potential_hr},
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
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Heating Fuel Consumed for community',
         'type': "'other'",'plot': True,}
            ]
        
    ## generate html
    msg = None
    if community in web_object.bad_data_coms:
        msg = web_object.bad_data_msg
    
    pth = os.path.join(web_object.directory, community.replace("'",''),
                    COMPONENT_NAME.replace(' ','_').lower() + '.html')
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
    dict
        with values used by summary
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
        
    try:
        source = "<a href='" + \
            project.comp_specs['project details']['link'] + "'> link </a>"
    except StandardError as e:
        source = "unknown"
        
    try:
        notes = project.comp_specs['project details']['notes'] 
    except StandardError as e:
        notes = "N/a"
    
    
    return [
        {'words':'Capital cost', 
            'value': costs},
        {'words':'Lifetime energy cost savings', 
            'value': benefits},
        {'words':'Net lifetime savings', 
            'value': net_benefits},
        {'words':'Benefit-cost ratio', 
            'value': BC},
        {'words':'Source', 
            'value': source},
        {'words':'Notes', 
            'value': notes},
            ]
