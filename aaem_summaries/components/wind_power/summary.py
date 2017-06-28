"""
Wind Power Outputs
------------------

output functions for Wind Power component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

import numpy as np

COMPONENT_NAME = "Wind Power"
DESCRIPTION = """
    This component calculates the potential cost savings from changes in the amount of diesel fuel used for electricity generation from the installation of new wind power infrastructure. 
"""

def generate_web_summary (web_object, community):
    """generate html summary for a community.
    generates web_object.directory/community/<component>.html and
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

    ## get the component (the modeled one)

    modeled = web_object.results[community][COMPONENT_NAME]
    #~ start_year = modeled.start_year
    #~ end_year = modeled.actual_end_year

    ## get the component (for projects)
    ## also figure out the needed start/end years
    projects, s1, e1 = wl.get_projects(web_object, community,
                                       COMPONENT_NAME, 'wind')


    start_year, end_year = wl.correct_dates(modeled.start_year, s1,
                                         modeled.actual_end_year, e1)

    order = projects.keys()
    projects['Modeled ' + COMPONENT_NAME] = modeled
    order = ['Modeled ' + COMPONENT_NAME] + order


    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast


    generation = fc.generation['generation diesel'].\
                                        ix[start_year:end_year]

    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            ix[start_year: end_year]#values
    diesel_price = diesel_price[diesel_price.columns[0]]

    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']




    ## get generation fuel costs per year (modeled)
    base_cost = generation/eff * diesel_price
    base_cost.name = 'Base Cost'


    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)



    ## get generation fuel used (modeled)
    base_con = generation/eff
    base_con.name = 'Base Consumption'

    table2 = wl.make_consumption_table(community, COMPONENT_NAME,
                                    projects, base_con,
                                    web_object.directory,
                                    'electric_diesel_reduction')
    ## info for modeled

    #~ print web_object.results[community]
    current = wl.create_electric_system_summary(web_object, community)



    #~ info = create_project_details_list(modeled)

    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current}]
                         #~ {'name': 'Modeled Wind Project', 'info': info}]

    ## get info for projects (updates info_for_projects )
    for p in order:
        project = projects[p]
        try:
            name = project.comp_specs['project details']['name']
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        info = create_project_details_list(project)

        info_for_projects.append({'name':name,'info':info})


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
    project: WindPower
        A WindPower object thats run function has been called

    Returns
    -------
        A dictionary with values used by summary
    """
    try:
        wind_class = int(float(project.comp_specs['wind class']))
    except ValueError:
        wind_class = 0

    pen = project.generation_wind_proposed/\
          float(project.forecast.cd.get_item('community',
        'utility info')['net generation'].iloc[-1:])
    pen *= 100


    notes = project.comp_specs['notes']

    if type(notes) is float:
        notes = ''

    if type(project.comp_specs['source']) is str:
        source = "<a href='" + \
            project.comp_specs['source'] + "'> link </a>"
    else:
        source = "unknown"

    if not np.isnan(project.cost_per_kw):
        cost = '${:,.0f}/kW'.format(project.cost_per_kw)
    else:
        cost = 'Value not determined as capital cost of project was known'

    return [
        {'words':'Capital cost (total)',
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Capital cost (cost per kW)',
            'value': cost},
        {'words':'Lifetime energy cost savings',
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net lifetime savings',
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit-cost ratio',
            'value': '{:,.1f}'.format(project.get_BC_ratio())},
        {'words':'Proposed nameplate capacity',
            'value': '{:,.0f} kW'.format(project.load_offset_proposed)},
        {'words':'Expected yearly generation',
         'value':
                '{:,.0f} kWh/year'.format(project.load_offset_proposed *\
            constants.hours_per_year*\
                float(project.comp_specs['capacity factor']))},

        {'words':'Estimated wind class', 'value': wind_class},
        {'words':'Estimated capacity factor',
            'value':
                float(project.comp_specs['capacity factor'])},
        {'words':'Estimated wind penetration level',
            'value': '{:,.2f}%'.format(pen)},
        {'words':'Notes',
            'value':  notes},
        {'words':'source',
            'value': source},
            ]
