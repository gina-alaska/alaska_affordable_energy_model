"""
outputs.py

    ouputs functions for Wind Power component
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
    save the component summary for wind
    
    pre:
        res_dir is a directory
    post:
        file is written in res_dir
    """
    #~ return
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['community data'].intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            wind = coms[c][COMPONENT_NAME]
            
            start_yr = wind.comp_specs['start year']
            wind.get_diesel_prices()
            diesel_price = float(wind.diesel_prices[0].round(2))
            phase = wind.comp_specs["project details"]['phase']
            average_load = wind.average_load
            existing_load = wind.comp_specs['resource data']\
                                            ['existing wind']
            existing_solar = wind.comp_specs['resource data']['existing solar']
            wind_class = float(wind.comp_specs['resource data']\
                                                ['Assumed Wind Class']) 
            proposed_load =  wind.load_offset_proposed
            cap_fac = float(wind.comp_specs['resource data']\
                                            ['assumed capacity factor'])
            heat_rec_opp = wind.cd['heat recovery operational']
            try:
                #~ offset = wind.load_offset_proposed
                net_gen_wind = wind.net_generation_wind
                decbb = wind.diesel_equiv_captured
                
                
                loss_heat = wind.loss_heat_recovery
                electric_diesel_reduction=wind.electric_diesel_reduction
                
                diesel_red = wind.reduction_diesel_used
                levelized_cost = wind.levelized_cost_of_energy
                break_even = wind.break_even_cost
                eff = wind.cd["diesel generation efficiency"]
                
            except AttributeError:
                offset = 0
                net_gen_wind = 0
                decbb = 0
                electric_diesel_reduction=0
                loss_heat = 0
                
                diesel_red = 0
                levelized_cost = 0
                break_even = 0
                eff = wind.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_wind / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            l = [c, 
                start_yr,
                phase,
                wind_class, 
                average_load, 
                proposed_load,
                existing_load,
                existing_solar,
                cap_fac,
                net_gen_wind,
                decbb, 
                loss_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                eff,
                diesel_price,
                break_even,
                levelized_cost,
                wind.get_NPV_benefits(),
                wind.get_NPV_costs(),
                wind.get_NPV_net_benefit(),
                wind.irr,
                wind.get_BC_ratio(),
                wind.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Start Year',
            'project phase',
            'Assumed Wind Class',
            'Average Diesel Load [kw]',
            'Wind Capacity Proposed [kW]',
            'Existing Wind Capacity [kW]',
            'Existing Solar Capacity [kW]',
            'Assumed Wind Class Capacity Factor [%]',
            'Net Proposed Wind Generation [kWh]',
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption [gal]',
            'Wind Power Reduction in Utility Diesel Consumed per year',
            'Diesel Denerator Efficiency','Diesel Price - year 1 [$\gal]',
            'Break Even Diesel Price [$/gal]',
            'Levelized Cost Of Energy [$/kWh]',
            'Wind NPV benefits [$]',
            'Wind NPV Costs [$]',
            'Wind NPV Net benefit [$]',
            'Wind Internal Rate of Return',
            'Wind Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# wind summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.env.get_template('component.html')
    
    ## get the component (the modelded one)
  
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
                                    'electric_diesel_reduction')
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
         'title': 'Estimated Electricity Generation Fuel Costs per Year',
         'type': "'$'"},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Electricity Generation ',
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
        wind_class = int(float(project.comp_specs['resource data']\
                                            ['Assumed Wind Class']))
    except ValueError:
        wind_class = 0
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
            'value': '{:,.0f}'.format(project.load_offset_proposed)},
        {'words':'Expected Yearly Generation (kWh/year)', 
         'value': 
                '{:,.0f}'.format(project.load_offset_proposed *\
                                 constants.hours_per_year)},

        {'words':'Estimated Wind Class', 'value': wind_class},
        {'words':'Estimated Capacity Factor', 
            'value': 
                project.comp_specs['resource data']['assumed capacity factor']},
        {'words':'Estimated Wind Penetration Level (%)', 'value': 'TBD'},
            ]
