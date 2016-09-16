"""
outputs.py

    ouputs functions for Wind Power component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

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
            wind = coms[c]['wind power']
            
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
                'wind_power_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# wind summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.env.get_template('wind.html')
    
    ## get the component (the modelded one)
  
    comp_no_project = web_object.results[community]['wind power']
    start_year = comp_no_project.start_year
    end_year = comp_no_project.actual_end_year
    
    ## get the component (for projects)
    ## also figure out the needed start/end years
    projects = {}
    for i in [i for i in sorted(web_object.results.keys()) \
         if i.find(community) != -1 and i.find('wind') != -1]:
             
        start_year = min(start_year, web_object.results[i]['wind power'].start_year)
        end_year = max(end_year, web_object.results[i]['wind power'].actual_end_year)
        projects[i] = web_object.results[i]['wind power']
             

    ## get forecast stuff (consumption, generation, etc)
    fc = comp_no_project.forecast
    generation = fc.generation_by_type['generation_diesel [kWh/year]'].\
                                        ix[start_year:end_year]
    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1)
           
    ## get diesel generator efficiency
    eff = comp_no_project.cd['diesel generation efficiency']
    
    ## get generation fuel costs per year (modeled)
    base_cost = generation/eff * diesel_price
    base_cost.name = 'Base Cost'
    costs_table = DataFrame(base_cost)

    ### find savings
    net_benefit = DataFrame([range(comp_no_project.start_year,
                                   comp_no_project.actual_end_year+1),
                             comp_no_project.get_net_beneft()\
                                   [:comp_no_project.actual_project_life].\
                                   tolist()],
                             ['Year', 'savings']).T.set_index('Year')
    net_benefit.index = net_benefit.index.astype(int)
    
    ## add post cost to table
    costs_table['Estimated Proposed Generation'] = \
                    costs_table['Base Cost'] - net_benefit['savings']
    costs_table['year'] = costs_table.index
    
    
    ## get generation fuel costs per year (projects)
    names = []
    for p in projects:
        project = projects[p]
        name = project.comp_specs['project details']['name']
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        net_benefit = DataFrame([range(project.start_year,
                                       project.actual_end_year+1),
                                 project.get_net_beneft()\
                                        [:project.actual_project_life].\
                                        tolist()],
                                 ['Year', 'savings']).T.set_index('Year')
        net_benefit.index = net_benefit.index.astype(int)
        costs_table[name] = \
                costs_table['Base Cost'] - net_benefit['savings']
        names.append(name)

    ## format table
    costs_table = costs_table[['year','Base Cost',
                                'Estimated Proposed Generation'] + names]
    costs_table.columns = ['year','Base Case Cost', 
                                                'Cost With Wind'] + names
    costs_table.to_csv(os.path.join(web_object.directory,'csv',
                        community + "_" + "Wind_Power" + "_" + 'costs.csv'),
                        index=False)
    ## make list from of table
    table1 = costs_table.\
                    round().values.tolist()
    table1.insert(0,['year','Base Case Cost', 'Modeled Wind'] + names)
    
    
    ## get generation fule used (modeled)
    base_con = generation/eff 
    base_con.name = 'Base Consumption'
    cons_table = DataFrame(base_con)
    cons_table['year'] = cons_table.index
    
    ## find reduction 
    reduction = DataFrame([range(comp_no_project.start_year,
                            comp_no_project.actual_end_year+1)],['Year']).T
    reduction['savings'] = comp_no_project.electric_diesel_reduction
    reduction = reduction.set_index('Year')
    reduction.index = reduction.index.astype(int)
    
    ## add savings
    cons_table['Est. Diesel Consumed'] = \
                cons_table['Base Consumption'] - reduction['savings']
    
    ## get generation fule used (projects)
    names = []
    for p in projects:
        project = projects[p]
        name = project.comp_specs['project details']['name']
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        reduction = DataFrame([range(project.start_year,
                                project.actual_end_year+1)],['Year']).T
        reduction['savings'] = project.electric_diesel_reduction
        reduction = reduction.set_index('Year')
        reduction.index = reduction.index.astype(int)
        cons_table[name] = \
                    cons_table['Base Consumption'] - reduction['savings']
        names.append(name)
    
    
    ## format table
    cons_table = cons_table[['year','Base Consumption', 
                                'Est. Diesel Consumed'] + names]
    
    cons_table.columns = ['year','Base Case Diesel Consumed',
                                        'Wind Diesel Consumed']+names
    ## save to csv
    cons_table.to_csv(os.path.join(web_object.directory,'csv', 
                community + "_" + "Wind_Power" + "_" + 'consumption.csv'),
                index=False)
    
    ## make list form
    table2  = cons_table.\
                    round().values.tolist()
    table2.insert(0,['year', 'Base Case Diesel Consumed',
                      'Modeled Wind']+names)
    
    
    ## info for modled
    info = [
        {'words':'Investments Needed', 
            'value': '${:,.0f}'.format(comp_no_project.get_NPV_costs())},
        {'words':'Net Lifetime Savings', 
            'value': '${:,.0f}'.format(comp_no_project.get_NPV_benefits())},
        {'words':'Expected kWh/year', 
            'value': 
                '{:,.0f}'.format(comp_no_project.load_offset_proposed*8760)},
        {'words':'Proposed Capacity(kW)', 
            'value': 
                '{:,.0f}'.format(comp_no_project.load_offset_proposed)},
        {'words':'Assumed Wind Class', 
            'value': int(float(comp_no_project.comp_specs['resource data']\
                                            ['Assumed Wind Class']))},
        {'words':'Assumed Capacity Factor', 
            'value': comp_no_project.comp_specs['resource data']\
                                         ['assumed capacity factor']},
        {'words':'Existing Wind', 
            'value': 
               comp_no_project.comp_specs['resource data']['existing wind'],
            'units': 'kW'},
        {'words':'Existing Solar',
            'value': 
              comp_no_project.comp_specs['resource data']['existing solar'], 
            'units' :'kW'},
            ]
         
    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled Wind Project','info':info}]
    
    ## get info for projects (updates info_for_projects )
    for p in projects:
        project = projects[p]
        name = project.comp_specs['project details']['name']
        info = [
            {'words':'Investments Needed', 
                'value': '${:,.0f}'.format(project.get_NPV_costs())},
            {'words':'Net Lifetime Savings', 
                'value': '${:,.0f}'.format(project.get_NPV_benefits())},
            {'words':'Expected kWh/year', 
                'value': '{:,.0f}'.format(project.load_offset_proposed*8760)},
            {'words':'Proposed Capacity(kW)', 
                'value': '{:,.0f}'.format(project.load_offset_proposed)},
            {'words':'Assumed Wind Class', 
                'value': int(float(project.comp_specs['resource data']\
                                                ['Assumed Wind Class']))},
            {'words':'Assumed Capacity Factor', 
                'value': project.comp_specs['resource data']\
                                             ['assumed capacity factor']},
            {'words':'Existing Wind', 
                'value': project.comp_specs['resource data']['existing wind'],
                'units': 'kW'},
            {'words':'Existing Solar',
                'value': project.comp_specs['resource data']['existing solar'], 
                'units' :'kW'},
            ]
            
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
    pth = os.path.join(web_object.directory, community +'_wind_summary.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = "Wind Power", 
                                    com = community ,
                                    charts = charts ))
