"""
outputs.py

    ouputs functions for Residential Building Efficiency component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order
import aaem.web_lib as wl

def component_summary (coms, res_dir):
    """
    creates a log for the residental component outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "residential_summary.csv" log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            res = coms[c][COMPONENT_NAME]
            out.append([c,
                res.get_NPV_benefits(),res.get_NPV_costs(),
                res.get_NPV_net_benefit(),res.irr,res.get_BC_ratio(),
                res.hoil_price[0], res.init_HH, res.opportunity_HH,
                res.break_even_cost, res.levelized_cost_of_energy,
                res.baseline_fuel_Hoil_consumption[0]/constants.mmbtu_to_gal_HF,
                (res.baseline_fuel_Hoil_consumption[0] - \
                    res.proposed_fuel_Hoil_consumption[0])/\
                        constants.mmbtu_to_gal_HF,
                round(float(res.fuel_oil_percent)*100,2),
                res.baseline_HF_consumption[0],
                res.baseline_HF_consumption[0] - \
                        res.proposed_HF_consumption[0],
                ])
        except (KeyError,AttributeError) as e :
            #~ print e
            pass
            
    cols = ['community',
           'Residential Efficiency NPV Benefit',
           'Residential Efficiency NPV Cost', 
           'Residential Efficiency NPV Net Benefit',
           
           'Residential Internal Rate of Return',
           'Residential Efficiency B/C Ratio',
           'Heating Oil Price - year 1',
           'Occupied Houses', 
           'Houses to Retrofit', 
           'Break Even Heating Fuel Price [$/gal heating oil equiv.]',
           'Levelized Cost of Energy [$/MMBtu]',
           'Residential Heating Oil Consumed(mmbtu) - year 1',
           'Residential Efficiency Heating Oil Saved(mmbtu/year)',
           'Residential Heating Oil as percent of Total Heating Fuels',
           'Total Residentital Heating Fuels (mmbtu) - year 1',
           'Residential Efficiency Total Heating Fuels Saved (mmbtu/year)',
            ]
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# residental building component summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')


def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.env.get_template('component.html')
    
    ## get the component (the modelded one)
  
    modeled = web_object.results[community][COMPONENT_NAME]
    start_year = modeled.start_year
    end_year = modeled.actual_end_year
    
    ## for make table functions
    projects = {'Modeled ' + COMPONENT_NAME:  modeled}
    
    ## get forecast stuff (consumption, generation, etc)
    fc = modeled.forecast

    generation = fc.generation_by_type['generation diesel'].\
                                        ix[start_year:end_year]
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1)
           
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
    #~ base_con['Base Consumption'] = modeled.baseline_kWh_consumption
    #~ table2 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    #~ projects, base_con,
                                    #~ web_object.directory,
                                    #~ 'proposed_kWh_consumption')
                                    

    base_con['Base Consumption'] = modeled.baseline_fuel_Hoil_consumption[:modeled.actual_project_life]
    table3 = wl.make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'savings_HF')
    #~ table3[0][-1]
    
    current = [{}]
    ## info for modeled
    info = create_project_details_list (modeled)
        
         
    ## info table (list to send to template)
    info_for_projects = [#{'name': 'Current System', 'info':current},
                            {'name':'Modeled Efficiency Project','info':info}]
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Fuel + Electricity Costs',
         'type': "'$'", 'plot': True,},
        #~ {'name':'E_consumption', 'data': str(table2).replace('nan','null'), 
         #~ 'title':'Electricity Consumed',
         #~ 'type': "'other'",'plot': True,},
        {'name':'H_consumption', 'data': str(table3).replace('nan','null'), 
         'title':'Heating Oil Consumed',
         'type': "'other'", 'plot': True,}
            ]
        
    ## generate html
    ## generate html
    pth = os.path.join(web_object.directory, community,
                    COMPONENT_NAME.replace(' ','_').lower() + '.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = COMPONENT_NAME, 
                                    com = community ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = web_object.get_summary_pages(),
                                    communities = web_object.get_all_coms(),
                                    metadata = web_object.metadata,
                                    ))
    





def create_project_details_list (project):
    """
    makes a projects details section for the html
    """
   
    return [
        {'words':'Capital Cost ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit Cost Ratio', 
            'value': '{:,.3f}'.format(project.get_BC_ratio())},
        #~ {'words':'Proposed Nameplate Capacity(kW)', 
            #~ 'value': '{:,.0f}'.format(project.proposed_load)},
        #~ {'words':'Expected Yearly Generation (kWh/year)', 
         #~ 'value': 
                #~ '{:,.0f}'.format(project.proposed_load *\
                                 #~ constants.hours_per_year)},

        #~ {'words':'Output per 10kW Solar PV', 
            #~ 'value': project.comp_specs['data']\
                                         #~ ['Output per 10kW Solar PV']},
            ]
