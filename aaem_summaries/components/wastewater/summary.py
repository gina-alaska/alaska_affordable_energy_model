"""
Water Wastewater Outputs
------------------------

output functions for Water Wastewater component

"""
import os.path
import aaem.constants as constants
from aaem.components import comp_order
import aaem_summaries.web_lib as wl

from pandas import DataFrame
import numpy as np

COMPONENT_NAME = 'Water and Wastewater Efficiency'

DESCRIPTION = """
    This component calculates the potential reduction in Electricty and Heating Oil by improving the efficiency of the water-wastewater system
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
    
    ## get the component (the modelded one)
  
    modeled = web_object.results[community][COMPONENT_NAME]
    start_year = modeled.start_year
    end_year = modeled.actual_end_year
    
    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}
    
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
    base_cost = DataFrame(base_cost) 
    base_cost['Base Cost'] = (modeled.baseline_HF_cost + modeled.baseline_kWh_cost)[:modeled.actual_project_life]
    table1 = wl.make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)
    
    ## get generation fule used (modeled)
    base_con = generation/eff 
    base_con.name = 'Base Consumption'
    base_con = DataFrame(base_con)
    base_con['Base Consumption'] = modeled.baseline_kWh_consumption[:modeled.actual_project_life]
    table2 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'savings_kWh_consumption')
                                    

    base_con['Base Consumption'] = modeled.baseline_fuel_Hoil_consumption[:modeled.actual_project_life]
    table3 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'savings_fuel_Hoil_consumption')
    table3[0][-1]
    
    
    
    current = [
        {'words':'System type', 
            "value":str(modeled.comp_specs['data']['System Type'])},
        {'words':'Current system heating fuels', 
            "value": 'Modeled' \
            if np.isnan(float(modeled.comp_specs['data']['HF Used']))\
            else 'Reported'},
        {'words':'Current system electicity reported', 
            "value": 'Modeled' \
            if np.isnan(float(modeled.comp_specs['data']['kWh/yr']))\
            else 'Reported'},
        
        {'words':'Uses biomass', 
            "value":'Yes' if modeled.comp_specs['data']['Biomass'] else 'No'},
        {'words':'Uses recovered heat', 
        "value":'Yes' if modeled.comp_specs['data']['HR Installed'] else 'No'},
            ]
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                            {'name':'Modeled Efficiency Project','info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Fuel + Electricity Costs for water/wastewater sector',
         'type': "'$'",'plot': True,},
        {'name':'E_consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Electricity Consumed by water/wastewater sector',
         'type': "'other'",'plot': True,},
        {'name':'H_consumption', 'data': str(table3).replace('nan','null'), 
         'title':'Heating Oil Consumed by water/wastewater sector',
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
    projcet: WaterWastewaterSystems
        A WaterWastewaterSystems object thats run function has been called
            
    Returns
    -------
        A dictionary with values used by summary
    """
   
    ex_h_savings = (1 - \
        (
        project.proposed_HF_consumption / project.baseline_HF_consumption
        )[0])*100
   
    ex_e_savings = (1 - \
        (
        project.proposed_kWh_consumption / project.baseline_kWh_consumption
        )[0])*100
   
    return [
        {'words':'Capital cost', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Capital cost', 
            "value": 'Estimated' \
            if np.isnan(float(project.comp_specs['data']['kWh/yr']))\
            else 'From audit'},
        {'words':'Lifetime energy cost savings', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net lifetime savings', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit-cost ratio', 
            'value': '{:,.1f}'.format(project.get_BC_ratio())},
        
        {'words':'Expected space heating savings ', 
            'value': '{:,.2f}%'.format(ex_h_savings)},
        {'words':'Expected electrical savings ', 
            'value': '{:,.2f}%'.format(ex_e_savings)},
            ]

