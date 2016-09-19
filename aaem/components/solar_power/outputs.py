"""
outputs.py

    ouputs functions for Solar Power component
"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants

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
            solar = coms[c]['solar power']

            start_yr = solar.comp_specs['start year']
            solar.get_diesel_prices()
            diesel_price = float(solar.diesel_prices[0].round(2))
            assumed_out = solar.comp_specs['data']['Output per 10kW Solar PV']
            average_load = solar.average_load
            proposed_capacity = solar.proposed_load + 0
            existing_capacity = solar.comp_specs['data']['Installed Capacity']
            wind_capacity = solar.comp_specs['data']['Wind Capacity']
           
            try:
                net_gen = solar.generation_proposed [0]
                loss_heat = solar.fuel_displaced[0]
                hr_op = solar.cd['heat recovery operational']
                net_heating =   -1* loss_heat
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = solar.generation_fuel_used[0]
            except AttributeError:
                net_gen = 0
                loss_heat = 0
                hr_op = solar.cd['heat recovery operational']
                net_heating = 0
                eff = solar.cd["diesel generation efficiency"]
                red_per_year = 0
                
            try:
                levelized_cost = solar.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0

            try:
                break_even = solar.break_even_cost
            except AttributeError:
                break_even = 0
            
            l = [c, assumed_out, average_load, proposed_capacity, 
                 existing_capacity, wind_capacity, net_gen, loss_heat, hr_op,
                 net_heating, red_per_year, eff, diesel_price,
                 break_even,
                 levelized_cost,
                 solar.get_NPV_benefits(),
                 solar.get_NPV_costs(),
                 solar.get_NPV_net_benefit(),
                 solar.get_BC_ratio(),
                 solar.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    
    
    cols = ['Community',
            'Assumed  Output per 10kW Solar PV Array',
            'Average Diesel Load [kw]',
            'Solar Capacity Proposed [kW]',
            'Existing Solar Capacity [kW]',
            'Existing Wind Capacity [kW]',
            'Net Proposed Solar Generation [kWh]',
            'Loss of Recovered Heat from Proposed Solar [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption from Proposed Solar [gal]',
            'Proposed Solar Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Solar NPV benefits [$]',
            'Solar NPV Costs [$]',
            'Solar NPV Net benefit [$]',
            'Solar Benefit Cost Ratio',
            'notes']
    
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                'solar_power_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# solar summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.env.get_template('component.html')
    
    ## get the component (the modelded one)
  
    comp_no_project = web_object.results[community]['solar power']
    start_year = comp_no_project.start_year
    end_year = comp_no_project.actual_end_year
    
    ## get forecast stuff (consumption, generation, etc)
    fc = comp_no_project.forecast
    try:
        generation = fc.generation_by_type['generation_diesel [kWh/year]'].\
                                        ix[start_year:end_year]
    except KeyError:
        generation = fc.generation_by_type['generation diesel'].\
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
    


    ## format table
    costs_table = costs_table[['year','Base Cost', 
                                    'Estimated Proposed Generation']]
    costs_table.columns = ['year','Current Cost', 'Cost With Solar']
    costs_table.to_csv(os.path.join(web_object.directory,'csv',
                        community + "_" + "Solar_Power" + "_" + 'costs.csv'),
                        index=False)
    ## make list from of table
    table1 = costs_table.\
                    round().values.tolist()
    table1.insert(0,['year','Current Projection', 'Modeled Solar'])
    
    
    ## get generation fule used (modeled)
    base_con = generation/eff 
    base_con.name = 'Base Consumption'
    cons_table = DataFrame(base_con)
    cons_table['year'] = cons_table.index
    
    ## find reduction 
    reduction = DataFrame([range(comp_no_project.start_year,
                            comp_no_project.actual_end_year+1)],['Year']).T
    reduction['savings'] = comp_no_project.generation_fuel_used\
                                        [:comp_no_project.actual_project_life]
    reduction = reduction.set_index('Year')
    reduction.index = reduction.index.astype(int)
    
    ## add savings
    cons_table['Est. Diesel Consumed'] = \
                cons_table['Base Consumption'] - reduction['savings']
    
    
    ## format table
    cons_table = cons_table[['year','Base Consumption', 'Est. Diesel Consumed']]
    
    cons_table.columns = ['year','Current Projection Diesel Consumed',
                                        'Solar Diesel Consumed']
    ## save to csv
    cons_table.to_csv(os.path.join(web_object.directory,'csv', 
                community + "_" + "Solar_Power" + "_" + 'consumption.csv'),
                index=False)
    
    ## make list form
    table2  = cons_table.\
                    round().values.tolist()
    table2.insert(0,['year', 'Current Projection',
                      'Modeled Solar'])
    
    
    ## info for modled
    info = [
        {'words':'Benefit Cost Ratio', 
            'value': '{:,.3f}'.format(comp_no_project.get_BC_ratio())},
        {'words':'Investments Needed', 
            'value': '${:,.0f}'.format(comp_no_project.get_NPV_costs())},
        {'words':'Net Lifetime Savings', 
            'value': '${:,.0f}'.format(comp_no_project.get_NPV_benefits())},
        {'words':'Proposed Capacity(kW)', 
            'value': 
                '{:,.0f}'.format(comp_no_project.proposed_load)},
        {'words':'Output per 10kW Solar PV', 
            'value': comp_no_project.comp_specs['data']\
                                         ['Output per 10kW Solar PV']},
        {'words':'Existing Wind', 
            'value': 
               comp_no_project.comp_specs['data']['Wind Capacity'],
            'units': 'kW'},
        {'words':'Existing Solar',
            'value': 
              comp_no_project.comp_specs['data']['Installed Capacity'], 
            'units' :'kW'},
            ]
         
    ## info table (list to send to template)
    info_for_projects = [{'name':'Modeled Wind Project','info':info}]
            
    
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
    pth = os.path.join(web_object.directory, community +'_solar_summary.html')
    with open(pth, 'w') as html:
        html.write(template.render( info = info_for_projects,
                                    type = "Solar Power", 
                                    com = community ,
                                    charts = charts ))
    
