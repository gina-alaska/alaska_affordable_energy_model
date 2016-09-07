from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat

env = Environment(loader=PackageLoader('aaem','templates/'))

template = env.get_template('wind.html')


model = driver.Driver('model/m0.19.0_d0.19.0/')
results = model.load_results()
wp = results['Shishmaref']['wind power']

generation = wp.forecast.generation_by_type['generation_diesel [kWh/year]'].\
                                            ix[wp.start_year:wp.actual_end_year]
                                            
eff = wp.cd['diesel generation efficiency']
diesel_price = wp.diesel_prices[:wp.actual_project_life]

net_benefit = wp.get_net_beneft()[:wp.actual_project_life]

base_cost = generation/eff * diesel_price
prop_cost = base_cost - net_benefit
costs_table = concat([base_cost,prop_cost],axis = 1)
costs_table['year'] = costs_table.index

table1 = costs_table[['year','generation_diesel [kWh/year]']].\
                astype(int).values.tolist()
table1.insert(0,['year','Base Case Cost', 'Cost With Wind'])


base_con = generation/eff 
cons_table = concat([base_con,base_con+wp.electric_diesel_reduction],axis=1)

cons_table['year'] = cons_table.index

table2  = cons_table[['year','generation_diesel [kWh/year]']].\
                astype(int).values.tolist()
table2.insert(0,['year',
                 'Base Case Diesel Consumed',
                 'Wind Diesel Consumed'])

with open('Wind_Summary_Sishmaref_example.html', 'w') as html:
    html.write(template.render( ##costs= str(table1), 
                                #~ consumption = str(table2), 
                                capital = wp.get_NPV_costs(), 
                                savings = wp.get_NPV_benefits(), 
                                capicity= wp.load_offset_proposed,
                                kWh = wp.load_offset_proposed*8760,
                                wind_class = int(wp.comp_specs['resource data']\
                                                        ['Assumed Wind Class']),
                                cap_factor = wp.comp_specs['resource data']\
                                                    ['assumed capacity factor'],
                                wind = wp.comp_specs['resource data']\
                                                              ['existing wind'],
                                solar = wp.comp_specs['resource data']\
                                                             ['existing solar'],
                                type = "Wind Power", 
                                com = "Shismaref" ,
                                charts = [{'name':'costs', 'data': table1, 'title': 'Estimated Electricity Generation Fuel Costs'},
                                          {'name':'consumption', 'data': table2, 'title':'Diesel Consumed for Generation Electricity'}] ))
    
