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
    projects, s1, e1 = get_projects(web_object,community,COMPONENT_NAME,'wind')
      
    start_year, end_year = correct_dates(modeled.start_year, s1,
                                         modeled.actual_end_year, e1)
    
    order = projects.keys()
    projects['Modled ' + COMPONENT_NAME] = modeled
    order = ['Modled ' + COMPONENT_NAME] + order
    
        
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

    
    table1 = make_costs_table(community, COMPONENT_NAME, projects, base_cost,
                              web_object.directory)
    
    
    
    ## get generation fule used (modeled)
    base_con = generation/eff 
    base_con.name = 'Base Consumption'
    
    table2 = make_consumption_table(community, COMPONENT_NAME, 
                                    projects, base_con,
                                    web_object.directory,
                                    'electric_diesel_reduction')
    ## info for modled
   
        
    
    current = [
        {'words':'Average Community Load (kW)', 'value': 'TBD'},
        {'words':'Average kWh/year', 'value': 'TBD'},
        {'words':'Peak Load', 'value': 'TBD'},
        {'words':'Existing nameplate wind capacity (kW)', 
         'value': modeled.comp_specs['resource data']['existing wind']},
        {'words':'Existing wind generation (kWh/year)', 'value': 'TBD'},
        {'words':'Existing nameplate solar capacity (kW)', 
         'value': modeled.comp_specs['resource data']['existing solar']},
        {'words':'Existing solar generation (kWh/year)', 'value': 'TBD'},
        {'words':'Existing nameplate hydro capacity (kW)', 
         'value': 'TBD'},
        {'words':'Existing hydro generation (kWh/year)', 'value': 'TBD'},
        
    
    ]
        
    
    info = create_project_details_list(modeled)
         
    ## info table (list to send to template)
    info_for_projects = [{'name': 'Current System', 'info':current},
                         {'name': 'Modeled Wind Project', 'info': info}]
    
    ## get info for projects (updates info_for_projects )
    for p in projects:
        project = projects[p]
        try:
            name = project.comp_specs['project details']['name']
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        try:
            wind_class = int(float(project.comp_specs['resource data']\
                                                ['Assumed Wind Class']))
        except ValueError:
            wind_class = 0
        info = create_project_details_list(project)
            
        info_for_projects.append({'name':name,'info':info})
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Electricity Generation Fuel Costs per Year',
         'type': "'$'"},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Diesel Consumed for Generation Electricity per Year',
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
                                    summary_pages = ['Summary'] + comp_order ))
 
 
def get_projects (web_object, community, comp, tag):
    projects = {}
    start_year = np.nan
    end_year = np.nan
    for i in [i for i in sorted(web_object.results.keys()) \
         if i.find(community) != -1 and i.find(tag) != -1]:
        
        if np.isnan(start_year):
            start_year = web_object.results[i][COMPONENT_NAME].start_year
            
        if np.isnan(end_year):
            end_year = web_object.results[i][COMPONENT_NAME].actual_end_year
             
        start_year = min(start_year, 
                        web_object.results[i][comp].start_year)
        end_year = max(end_year, 
                        web_object.results[i][comp].actual_end_year)
        projects[i] = web_object.results[i][comp]
    return projects, start_year, end_year
    
def make_costs_table (community, comp, projects, base_cost, directory):
    """
    make a table
    
    base_cost: dataframe with base cost for all years needed
    """
    costs_table = DataFrame(base_cost)
    costs_table['year'] = costs_table.index
    names = []
    for p in projects:
        project = projects[p]
        ##print project.comp_specs['project details']
        try:
            name = project.comp_specs['project details']['name']
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        net_benefit = DataFrame([range(project.start_year,
                                       project.actual_end_year+1),
                                 project.get_net_benefit()\
                                        [:project.actual_project_life].\
                                        tolist()],
                                 ['Year', 'savings']).T.set_index('Year')
        net_benefit.index = net_benefit.index.astype(int)
        costs_table[name] = \
                costs_table['Base Cost'] - net_benefit['savings']
        names.append(name)
    #~ print costs_table
    ## format table
    costs_table = costs_table[['year','Base Cost'] + names]
    costs_table.columns = ['year','Base Case Cost'] + names
    fname = community + "_" + comp.replace(' ','_').lower() + "_" + 'costs.csv'
    costs_table.to_csv(os.path.join(directory,'csv', fname),
                        index=False)
    #~ ## make list from of table
    plotting_table = costs_table.\
                    round().values.tolist()
    plotting_table.insert(0,['year','Current Projection'] + names)
    return plotting_table
    
def make_consumption_table (community, comp, projects, base_con, directory, savings_attribute):
    """
    """
    cons_table = DataFrame(base_con)
    cons_table['year'] = cons_table.index
    names = []
    for p in projects:
        project = projects[p]
        ##print project.comp_specs['project details']
        try:
            name = project.comp_specs['project details']['name']
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        reduction = DataFrame([range(project.start_year,
                                project.actual_end_year+1)],['Year']).T
                                
        s_c = "reduction['savings'] = project." + savings_attribute
        try:
            exec(s_c)
        except ValueError:
            s_c += '[:project.actual_project_life]'
            exec(s_c)
        reduction = reduction.set_index('Year')
        reduction.index = reduction.index.astype(int)
        cons_table[name] = \
                    cons_table['Base Consumption'] - reduction['savings']
        names.append(name)
    ## format table
    cons_table = cons_table[['year','Base Consumption'] + names]
    cons_table.columns = ['year','Base Case Diesel Consumed'] + names
    fname = community + "_" + comp.replace(' ','_').lower() + "_" + 'consumption.csv'
    cons_table.to_csv(os.path.join(directory,'csv', fname),index=False)
    #~ ## make list from of table
    plotting_table = cons_table.round().values.tolist()
    plotting_table.insert(0,['year','Current Projection'] + names)
    return plotting_table

def correct_dates (start, s1, end, e1):
    """ Function doc """
    if np.isnan(start) and  np.isnan(s1) and  np.isnan(end) and np.isnan(e1):
        raise StandardError, "Bad start and end years"
    if not np.isnan(s1) and np.isnan(start):
        start_year = s1
    elif not np.isnan(s1):
        start_year = min(start, s1)
    else:
        start_year = start
    if not np.isnan(e1) and np.isnan(end):
        end_year = e1
    elif not np.isnan(e1):
        end_year = max(end, e1)
    else:
        end_year = end
    #~ print start_year,end_year
    return start_year, end_year

                                    
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
        {'words':'Captial Cost ($)', 
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
