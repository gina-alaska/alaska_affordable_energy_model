"""
Biomass Pellet outputs
----------------------

output functions for Biomass Pellet component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

from pandas import DataFrame

COMPONENT_NAME = "Biomass for Heat (Pellet)"

DESCRIPTION = """
    This component calculates the potential change in heating oil usage from the installation of new biomass pellet boilers in non-residential buildings (assumed to heat 30% of non-residential square footage).
"""

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

    ## get the component (the modeled one)

    modeled = web_object.results[community][COMPONENT_NAME]
    if modeled.reason != 'OK':
        raise RuntimeError, modeled.reason
    start_year = modeled.start_year
    end_year = modeled.actual_end_year

    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}

    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast

    #~ ires = web_object.results[community]['Residential Energy Efficiency']
    icom = web_object.results[community]['Non-residential Energy Efficiency']
    #~ iwat = web_object.results[community]['Water and Wastewater Efficiency']

    data =  DataFrame(fc.population['population'])
    #~ df = DataFrame(ires.baseline_fuel_Hoil_consumption,
        #~ columns =['col'],
         #~ index = range(ires.start_year, ires.end_year+1))
    #~ data['heating_fuel_residential_consumed [gallons/year]'] = \
        #~ df['col'].round()

    df = DataFrame(
        icom.baseline_HF_consumption * constants.mmbtu_to_gal_HF,
        columns =['col'],
         index = range(icom.start_year, icom.end_year+1))
    data['heating_fuel_non-residential_consumed [gallons/year]'] = \
        df['col'].round()

    #~ df = DataFrame(
        #~ iwat.baseline_HF_consumption * constants.mmbtu_to_gal_HF,
        #~ columns =['col'],
         #~ index = range(iwat.start_year, iwat.end_year+1))
    #~ data['heating_fuel_water-wastewater_consumed [gallons/year]'] = \
        #~ df['col'].round()

    data['heating_fuel_total_consumed [gallons/year]'] = \
        data[[
            #~ 'heating_fuel_residential_consumed [gallons/year]',
            'heating_fuel_non-residential_consumed [gallons/year]',
            #~ 'heating_fuel_water-wastewater_consumed [gallons/year]',
        ]].sum(1)


    fuel_consumed = data['heating_fuel_total_consumed [gallons/year]']\
        .ix[start_year:end_year]
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            ix[start_year: end_year] + \
                        web_object.results[community]['community data'].\
                            get_item('community','heating fuel premium')
    diesel_price = diesel_price[diesel_price.columns[0]]
    ## get diesel generator efficiency
    eff = modeled.cd['diesel generation efficiency']



    ## get generation fuel costs per year (modeled)
    base_cost = fuel_consumed  * diesel_price
    base_cost.name = 'Base Cost'


    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)


    ## get generation fuel used (modeled)
    base_con = fuel_consumed
    base_con.name = 'Base Consumption'
    table2 = wl.make_consumption_table(community, COMPONENT_NAME,
                                    projects, base_con,
                                    web_object.directory,
                                    'heat_diesel_displaced')

    ## info for modeled
    info = create_project_details_list (modeled)


    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled biomass pellet project','info':info}]


    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'),
         'title': 'Estimated Heating Fuel Costs for non-residential sector',
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
                    COMPONENT_NAME.replace(' ','_').replace(' ','_').replace('(','').replace(')','').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME,
                                    com = community.replace("'",'') ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),


                                    message = msg ,
                                    description =  DESCRIPTION,
                                    metadata = web_object.metadata,

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
        {'words':'Proposed max capacity',
            'value': '{:,.0f} mmbtu/hr'.format(project.max_boiler_output)},
        {'words':'Area heated',
            'value': '{:,.0f} sqft'.format(project.heat_displaced_sqft)},
        {'words':'Fuel consumed per year',
            'value': '{:,.0f} tons of pellets'.\
            format(project.biomass_fuel_consumed )},

            ]
