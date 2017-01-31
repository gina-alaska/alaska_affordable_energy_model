"""
outputs.py

    ouputs functions for Wind Power component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME, DESCRIPTION
import aaem.constants as constants
from aaem.components import comp_order
import aaem.web_lib as wl

from datetime import datetime

## component summary
def component_summary (results, res_dir):
    """ 
    creats the regional and communites summary for the component 
    
    inputs:
        results: results from the model
        res_dir: location to save file
    
    outputs:
        saves a summaries in res-dir
    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
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
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name,  
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
            'Wind Benefit-cost ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# wind summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def create_regional_summary (results):
    """
    create the regional summary for this component
    
    inputs:
        results: results from the model
       
    outputs:
        returns summary as a data frame
    """
    #~ print "start"
    regions = {}
    for c in results:
        c_region = results[c]['community data'].get_item('community','region')
        comp = results[c][COMPONENT_NAME]
        #~ print comp
        bc_ratio = comp.get_BC_ratio()
        bc_ratio = (not type(bc_ratio) is str) and (not np.isinf(bc_ratio))\
                                              and (bc_ratio > 1)
        #~ print bc_ratio ,comp.get_BC_ratio()
        #~ return
        capex = round(comp.get_NPV_costs(),0)  if bc_ratio else 0
        net_benefit = round(comp.get_NPV_net_benefit(),0)  if bc_ratio else 0
       
        displaced_fuel = \
            round(comp.electric_diesel_reduction,0) if bc_ratio else 0

        if (results[c]['community data'].intertie == 'child' or c.find('+') != -1) and not c.find('wind') != -1:
            #~ print c
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities/interties in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] += capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] += net_benefit
            k = 'Generation diesel displaced by cost-effective projects (gallons)'
            regions[c_region][k] += displaced_fuel
            
        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex 
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Generation diesel displaced by cost-effective projects (gallons)'
            regions[c_region][k] = displaced_fuel
            
    cols = ['Number of communities/interties in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Generation diesel displaced by cost-effective projects (gallons)']
    
    try:        
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)
   
    summary.ix['All Regions'] = summary.sum()                 
    #~ print summary
    return summary
    
def save_regional_summary (summary, res_dir):
    """ 
    inputs:
        summary: summary dataframe
        res_dir: location to save file
    
    outputs:
        save a regional summary in res-dir
    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
    
def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.component_html
    
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
    """
    makes a projects details section for the html
    """
    try:
        wind_class = int(float(project.comp_specs['resource data']\
                                            ['Assumed Wind Class']))
    except ValueError:
        wind_class = 0
    
    pen = project.generation_wind_proposed/\
          float(project.forecast.cd.get_item('community',
                                                'generation').iloc[-1:])
    pen *= 100  
    
    try:
        notes = project.comp_specs['project details']['notes']
    except:
        notes = ''
    
    try:
        source = "<a href='" + \
            project.comp_specs['project details']['source'] + "'> link </a>"
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
            'value': '{:,.3f}'.format(project.get_BC_ratio())},
        {'words':'Proposed mameplate Capacity', 
            'value': '{:,.0f} kW'.format(project.load_offset_proposed)},
        {'words':'Expected Yearly Generation', 
         'value': 
                '{:,.0f} kWh/year'.format(project.load_offset_proposed *\
                                 constants.hours_per_year)},

        {'words':'Estimated wind lass', 'value': wind_class},
        {'words':'Estimated Capacity Factor', 
            'value': 
                project.comp_specs['resource data']['assumed capacity factor']},
        {'words':'Estimated wind penetration level', 
            'value': '{:,.2f}%'.format(pen)},
        {'words':'notes', 
            'value':  notes},
        {'words':'source', 
            'value': source},
            ]
