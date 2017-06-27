"""
Air Source Heat Pump Residential Outputs
----------------------------------------

output functions for Air Source Heat Pump Residential component

"""
import os.path
from pandas import DataFrame
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

COMPONENT_NAME = "Residential ASHP"

DESCRIPTION = """
    This component calculates the potential change in heating oil usage from the installation of new air source heat pumps in residential buildings. 
"""

def generate_web_summary (web_object, community):
    """generate html summary for a community.
    generates web_object.directory/community/ashp_residential.html and
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
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}

    ## get forecast stuff (consumption, generation, etc)
    r_comp = web_object.results[community]["Residential Energy Efficiency"]
    fuel_consumed = DataFrame(
        r_comp.baseline_HF_consumption,
        columns=['fuel consumed'],
        index = range(r_comp.start_year, r_comp.end_year+1)
    )['fuel consumed'].ix[start_year:end_year]

    fuel_consumed = fuel_consumed * constants.mmbtu_to_gal_HF

    ## get the diesel prices
    diesel_price = \
        modeled.cd['diesel prices'] + modeled.cd['heating fuel premium']
    #~ print diesel_price
    diesel_price = diesel_price[diesel_price.columns[0]].ix[start_year:end_year]

    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']


    ## get generation fuel costs per year (modeled)
    #~ print diesel_price
    base_cost = fuel_consumed  * diesel_price
    base_cost.name = 'Base Cost'


    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)


    ## get generation fuel used (modeled)
    base_con = (base_cost - base_cost) + fuel_consumed
    base_con.name = 'Base Consumption'
    table2 = wl.make_consumption_table(community, COMPONENT_NAME,
                                    projects, base_con,
                                    web_object.directory,
                                    'get_fuel_total_saved()')

    ## info for modeled
    info = create_project_details_list (modeled)


    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled residential air source heat pump project',
                            'info':info}]


    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'),
         'title': 'Estimated Heating Fuel Costs for residential sector',
         'type': "'$'",'plot': True,},
        {'name':'consumption', 'data': str(table2).replace('nan','null'),
         'title':'Heating Fuel Consumed by residential sector',
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
    project: HeatRecovery
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
        {'words':'Lifetime energy cost savings',
            'value': benefits},
        {'words':'Net lifetime savings',
            'value': net_benefits},
        {'words':'Benefit-cost ratio',
            'value': BC},
        {'words': 'Number of homes',
            'value': int(project.num_houses)},
        {'words': 'Average proposed capacity per residence (Btu/hr)',
            'value': '{:,.0f} Btu/hr'.format(project.peak_monthly_btu_hr_hh)},
        {'words': 'Excess generation capacity needed (kW)',
            'value': '{:,.0f} kW'.format(
                project.monthly_value_table['kWh consumed'].max()/(24 * 31))},
        {'words': 'Expected average coefficient of performance (COP)',
            'value': '{:,.2f}'.format(project.average_cop)},
        #~ {'words':"Btu/hrs",
            #~ 'value': project.comp_specs['btu/hrs'] },
        #~ {'words':"Cost per btu/hrs",
            #~ 'value': project.comp_specs['cost per btu/hrs'] },
            ]
