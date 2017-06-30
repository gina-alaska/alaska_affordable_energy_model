"""
Solar Power Outputs
-------------------

output functions for Solar Power component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

COMPONENT_NAME = "Solar Power"
DESCRIPTION = """
    This component calculates the potential cost savings through changes in the amount of diesel fuel used for electricity generation from the installation of new solar panel infrastructure.
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
    start_year = modeled.start_year
    end_year = modeled.actual_end_year

    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME + ' (PV)':  modeled}

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
                                    'get_fuel_total_saved()')



    current = wl.create_electric_system_summary(web_object, community)

    ## info for modeled
    info = create_project_details_list (modeled)


    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                            {'name':'Modeled Solar Project','info':info}]


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
    project: SolarPower
        A SolarPower object thats run function has been called

    Returns
    -------
        A dictionary with values used by summary
    """
    pen = project.generation_proposed/\
          float(project.forecast.cd.get_item('community',
        'utility info')['net generation'].iloc[-1:])
    pen *= 100
    pen = pen[0]

    return [
        {'words':'Capital cost (total)',
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Capital cost (cost per kW)',
            'value': '${:,.0f}/kW'.format(project.comp_specs['cost per kW'])},
        {'words':'Lifetime energy cost savings',
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net lifetime savings',
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit-cost ratio',
            'value': '{:,.1f}'.format(project.get_BC_ratio())},
        {'words':'Proposed nameplate capacity',
            'value': '{:,.0f} kW'.format(project.proposed_load)},
        {'words':'Expected yearly generation',
         'value':
                '{:,.0f} kWh/year'.format(project.generation_proposed[0])},

        {'words':'Output per 10kW solar PV',
            'value': '{:,.0f} kWh/year'.format(project.comp_specs\
                                         ['output per 10kW solar PV'])},
        {'words':'Estimated solar penetration level',
            'value': '{:,.0f}%'.format(pen)},
            ]
