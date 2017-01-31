"""
outputs.py

    ouputs functions for Hydropower component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME, DESCRIPTION
import aaem.constants as constants
import aaem.web_lib as wl
from aaem.components import comp_order

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
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik'
            l = [name,  
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
            'Hydro Benefit-cost ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')

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
            round(comp.generation_diesel_reduction,0) if bc_ratio else 0

        if not c.find('hydro') != -1:
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
            
    try:
        summary = DataFrame(regions).T[['Number of communities/interties in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects ($)',
                        'Net benefit of cost-effective projects ($)',
                    'Generation diesel displaced by cost-effective projects (gallons)']]
    except KeyError:
        summary = DataFrame(columns = ['Number of communities/interties in region',
                        'Number of communities with cost effective projects',
                        'Investment needed for cost-effective projects ($)',
                        'Net benefit of cost-effective projects ($)',
                    'Generation diesel displaced by cost-effective projects (gallons)'])
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
        #~ print name
            
    
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

    cost = project.comp_specs['project details']['generation capital cost'] +\
           project.comp_specs['project details']['transmission capital cost'] 
    
    pen = project.comp_specs['project details']['proposed generation']/\
          float(project.forecast.cd.get_item('community',
                                                'generation').iloc[-1:])
    pen *= 100
    
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
        {'words':'Proposed nameplate capacity', 
            'value': 
            '{:,.0f} kW'.format(project.comp_specs['project details']\
            ['proposed capacity'])},
        {'words':'Expected yearly generation', 
         'value': 
         '{:,.0f} kWh/year'.format(project.comp_specs['project details']\
                                ['proposed generation'])},
        {'words':'Phase', 
         'value': project.comp_specs['project details']['phase']},
        {'words':'Total capital cost', 
            'value': '${:,.0f}'.format(cost)},
        {'words':'Estimated hydro penetration level', 
            'value': '{:,.2f}%'.format(pen)},
        {'words':'source', 
            'value': source},
            ]

