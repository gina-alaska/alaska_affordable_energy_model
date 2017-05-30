"""
Hydropower outputs
------------------

output functions for Hydropower component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

import numpy as np

COMPONENT_NAME = "Hydropower"

DESCRIPTION = """
    This component calculates the potential electricity generation from diesel that could be offset by installing new Hydropower generation infrastructure. Requires that at least a reconnaissance-level heat recovery study has been completed for the community to be run. 
"""

def generate_web_summary (web_object, community):
    """generate html summary for a community. 
    generates web_object.directory/community/hydropower.html and 
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
  
    projects, s1, e1 = wl.get_projects(web_object, community, 
                                       COMPONENT_NAME, 'hydro')
                        
    if projects == {}:
        raise RuntimeError, "no projects or modeling info" 
    
    order = projects.keys()
    sy = np.nan
    ey = np.nan
    start_year, end_year = wl.correct_dates (sy, s1, ey, e1)
        
    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast
   
    
    generation = fc.generation_by_type['generation diesel'].\
                                        ix[start_year:end_year]
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1)#values

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
                                    'generation_diesel_reduction')
    ## info for modeled
   
        
    
    current = wl.create_electric_system_summary(web_object, community)

        
    
    #~ info = create_project_details_list(modeled)
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current}]
                         #~ {'name': 'Modeled Wind Project', 'info': info}]
    
    ## get info for projects (updates info_for_projects )
    for p in order:
        project = projects[p]
        try:
            name = project.comp_specs['name'].decode('unicode_escape').encode('ascii','ignore')
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        info = create_project_details_list(project)
            
        info_for_projects.append({'name':name,'info':info})
        #~ print name
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Electricity Generation Costs per Year',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Electricity Generation ',
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
    projcet: Hydropower
        A Hydropower object thats run function has been called
            
    Returns
    -------
        A dictionary with values used by summary
    """

    cost = project.comp_specs['generation capital cost'] +\
           project.comp_specs['transmission capital cost'] 
    
    pen = project.comp_specs['proposed generation']/\
          float(project.forecast.cd.get_item('community',
                                                'generation').iloc[-1:])
    pen *= 100
    
    try:
        source = "<a href='" + \
            project.comp_specs['source'] + "'> link </a>"
    except StandardError as e:
        source = "unknown"
    
    return [
        {'words':'Capital cost', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime savings', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net lifetime savings', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit-cost ratio', 
            'value': '{:,.1f}'.format(project.get_BC_ratio())},
        {'words':'Proposed nameplate capacity', 
            'value': 
            '{:,.0f} kW'.format(project.comp_specs['proposed capacity'])},
        {'words':'Expected yearly generation', 
         'value': 
         '{:,.0f} kWh/year'.format(project.comp_specs['proposed generation'])},
        {'words':'Phase', 
         'value': project.comp_specs['phase']},
        {'words':'Total capital cost', 
            'value': '${:,.0f}'.format(cost)},
        {'words':'Estimated hydro penetration level', 
            'value': '{:,.2f}%'.format(pen)},
        {'words':'source', 
            'value': source},
            ]

