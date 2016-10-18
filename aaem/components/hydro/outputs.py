"""
outputs.py

    ouputs functions for Hydropower component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
import aaem.web_lib as wl
from aaem.components import comp_order

## component summary
def component_summary (coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            hydro = coms[c]['Hydropower']
            
            start_yr = hydro.comp_specs['start year']
            hydro.get_diesel_prices()
            diesel_price = float(hydro.diesel_prices[0].round(2))
            #~ print hydro.diesel_prices[0]
            if not hydro.comp_specs["project details"] is None:
                phase = hydro.comp_specs["project details"]['phase']
            else:
                phase = "Reconnaissance"

            name = hydro.comp_specs["project details"]['name']
            
            average_load = hydro.average_load
            proposed_load =  hydro.load_offset_proposed
            
            
            heat_rec_opp = hydro.cd['heat recovery operational']
            
           
            net_gen_hydro = hydro.net_generation_proposed
            
            captured_energy = hydro.captured_energy
            
            
            lost_heat = hydro.lost_heat_recovery
            electric_diesel_reduction= hydro.generation_diesel_reduction
            
            diesel_red = hydro.captured_energy - hydro.lost_heat_recovery
            
            eff = hydro.cd["diesel generation efficiency"]
            
            levelized_cost = hydro.levelized_cost_of_energy
            break_even = hydro.break_even_cost
            #~ except AttributeError:
                #~ offset = 0
                #~ net_gen_hydro = 0
                #~ decbb = 0
                #~ electric_diesel_reduction=0
                #~ loss_heat = 0
                
                #~ diesel_red = 0
                #~ eff = hydro.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_hydro / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            l = [c, 
                name,
                start_yr,
                phase,

                average_load, 
                proposed_load,
                net_gen_hydro,
                
                captured_energy, 
                lost_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                
                eff,
                diesel_price,
                break_even,
                levelized_cost,
                hydro.get_NPV_benefits(),
                hydro.get_NPV_costs(),
                hydro.get_NPV_net_benefit(),
                hydro.irr,
                hydro.get_BC_ratio(),
                hydro.reason
            ]
            out.append(l)
        except (KeyError,AttributeError,TypeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Project Name',
            'Start Year',
            'project phase',
            
            'Average Diesel Load [kw]',
            'Wind Capacity Proposed [kW]',
            'Net Proposed Hydro Generation [kWh]',
            
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net Reduction in Heating Oil Consumption [gal]',
            'Hydro Power Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Hydro NPV benefits [$]',
            'Hydro NPV Costs [$]',
            'Hydro NPV Net benefit [$]',
            'Hydro Internal Rate of Return',
            'Hydro Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')

    data.to_csv(f_name, mode='w')
    
def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.env.get_template('component.html')
    
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
   
        
    
    current = wl.create_electric_system_summary(web_object.results[community])

        
    
    #~ info = create_project_details_list(modeled)
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current}]
                         #~ {'name': 'Modeled Wind Project', 'info': info}]
    
    ## get info for projects (updates info_for_projects )
    for p in order:
        project = projects[p]
        try:
            name = project.comp_specs['project details']['name'].decode('unicode_escape').encode('ascii','ignore')
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        info = create_project_details_list(project)
            
        info_for_projects.append({'name':name,'info':info})
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Electricity Generation Fuel Costs per Year',
         'type': "'$'"},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Electricity Generation ',
         'type': "'other'"}
            ]
        
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
                                    communities = web_object.get_all_coms()
                                    ))
 

                                    
def create_project_details_list (project):
    """
    makes a projects details section for the html
    """

    cost = project.comp_specs['project details']['generation capital cost'] +\
           project.comp_specs['project details']['transmission capital cost'] 
    
    pen = project.comp_specs['project details']['proposed generation']/\
          float(project.forecast.cd.get_item('community',
                                                'generation').iloc[-1:])
    pen *= 100
    return [
        {'words':'Capital Cost ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_costs())},
        {'words':'Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_benefits())},
        {'words':'Net Lifetime Savings ($)', 
            'value': '${:,.0f}'.format(project.get_NPV_net_benefit())},
        {'words':'Benefit Cost Ratio', 
            'value': '{:,.3f}'.format(project.get_BC_ratio())},
        {'words':'Proposed Nameplate Capacity(kW)', 
            'value': 
            '{:,.0f}'.format(project.comp_specs['project details']\
            ['proposed capacity'])},
        {'words':'Expected Yearly Generation (kWh/year)', 
         'value': 
         '{:,.0f}'.format(project.comp_specs['project details']\
                                ['proposed generation'])},
        {'words':'Phase', 
         'value': project.comp_specs['project details']['phase']},
        {'words':'Total Capital Cost', 
            'value': '${:,.0f}'.format(cost)},
        {'words':'Estimated Hydro Penetration Level (%)', 
            'value': '{:,.2f}%'.format(pen)},
            ]

