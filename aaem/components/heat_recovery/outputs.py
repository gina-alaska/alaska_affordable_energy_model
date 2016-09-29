"""
outputs.py

    ouputs functions for Heat Recovery component
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
    """
    out = []
    for c in sorted(coms.keys()):
        #~ it = coms[c]['community data'].intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
            comp = coms[c][COMPONENT_NAME]
            
            comp.get_diesel_prices()
            diesel_price = float(comp.diesel_prices[0].round(2))
            hfp = comp.cd['heating fuel premium']
            
            propsed_hr = comp.proposed_heat_recovery
            #~ eff = comp.cd["diesel generation efficiency"]
            
            try:
                break_even_cost = comp.break_even_cost
                levelized_cost_of_energy = comp.levelized_cost_of_energy
            except AttributeError:
                break_even_cost = np.nan
                levelized_cost_of_energy = np.nan
            
            l = [c, 
                 
                 
                 propsed_hr,
                 diesel_price,
                 hfp,
                 diesel_price + hfp,
                 #~ eff,
                 break_even_cost,
                 levelized_cost_of_energy,
                 comp.get_NPV_benefits(),
                 comp.get_NPV_costs(),
                 comp.get_NPV_net_benefit(),
                 comp.get_BC_ratio(),
                 comp.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    cols = ['Community',
        
            'Proposed Heat Recovery [gallons]',
            'Diesel price - year 1 [$/gal]',
            'Heating Fuel Premimum [$/gal]',
            'Heating Fuel Price - year 1 [$/gal]',
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Heat Recovery NPV benefits [$]',
            'Heat Recovery NPV Costs [$]',
            'Heat Recovery NPV Net benefit [$]',
            'Heat Recovery Benefit Cost Ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_").lower() + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
    
    
def generate_web_summary (web_object, community):
    """
    """
    ## get the template
    template = web_object.env.get_template('component.html')
    
    
    
    ## get the component (the modelded one)
  
    comp_no_project = web_object.results[community][COMPONENT_NAME]
    
    if np.isnan(comp_no_project.get_net_benefit()).all():
        start_year = np.nan
        end_year = np.nan
    else:
        start_year = comp_no_project.start_year
        end_year = comp_no_project.actual_end_year
    
    ## get the component (for projects)
    ## also figure out the needed start/end years
    projects = {}
    #~ print community
    for i in [i for i in sorted(web_object.results.keys()) \
         if i.find(community.replace(' ','_')) != -1 and i.find('heat_recovery') != -1]:
        print 'Found' ,community
        
        if np.isnan(start_year):
            start_year = web_object.results[i][COMPONENT_NAME].start_year
            
        if np.isnan(end_year):
            end_year = web_object.results[i][COMPONENT_NAME].actual_end_year
            
        start_year = min(start_year, 
                        web_object.results[i][COMPONENT_NAME].start_year)
        end_year = max(end_year, 
                        web_object.results[i][COMPONENT_NAME].actual_end_year)
        projects[i] = web_object.results[i][COMPONENT_NAME]
             
    ## do i need to do any thing
    if np.isnan(comp_no_project.get_net_benefit()).all() and projects == {}:
        raise StandardError, "no projects or modeling info" 


    ## get forecast stuff (consumption, generation, etc)
    fc = comp_no_project.forecast

    fuel_consumed = fc.heating_fuel_dataframe['heating_fuel_total_consumed [gallons/year]'].ix[start_year:end_year]

    
    ## get the diesel prices
    diesel_price = web_object.results[community]['community data'].\
                            get_item('community','diesel prices').\
                            get_projected_prices(start_year, end_year+1) + \
                        web_object.results[community]['community data'].\
                            get_item('community','heating fuel premium')
           
    
    ## get generation fuel costs per year (modeled)
    base_cost = fuel_consumed  * diesel_price
    base_cost.name = 'Base Cost'
    costs_table = DataFrame(base_cost)

    ### find savings    
    net_benefit = DataFrame([range(comp_no_project.start_year,
                                   comp_no_project.actual_end_year+1),
                             comp_no_project.get_net_benefit()\
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
        #~ print project.comp_specs['project details']
        name = project.comp_specs['project details']['name']
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

    ## format table
    if np.isnan(comp_no_project.get_net_benefit()).all():
        costs_table = costs_table[['year','Base Cost'] + names]
        costs_table.columns = ['year','Base Case Cost'] + names
    else:
        costs_table = costs_table[['year','Base Cost',
                                'Estimated Proposed Generation'] + names]
        costs_table.columns = ['year','Base Case Cost', 
                                            'Cost With Heat Recovery'] + names
                                                
                                                
    costs_table.to_csv(os.path.join(web_object.directory,'csv',
                        community + "_" + COMPONENT_NAME.replace(' ','_').lower() + "_" + 'costs.csv'),
                        index=False)
    ## make list from of table
    table1 = costs_table.\
                    round().values.tolist()
                    
    if np.isnan(comp_no_project.get_net_benefit()).all():
        table1.insert(0,['year','Current Projection'] + names)
    else:
        table1.insert(0,['year','Current Projection', 'Modeled Wind'] + names)
    
    
    #~ ## get generation fule used (modeled)
    base_con = fuel_consumed
    base_con.name = 'Base Consumption'
    cons_table = DataFrame(base_con)
    cons_table['year'] = cons_table.index
    
    ## find reduction 
    reduction = DataFrame([range(comp_no_project.start_year,
                            comp_no_project.actual_end_year+1)],['Year']).T
    reduction['savings'] = comp_no_project.proposed_heat_recovery
    reduction = reduction.set_index('Year')
    reduction.index = reduction.index.astype(int)
    
    #~ ## add savings
    cons_table['Est. Heating Fuel Consumed'] = \
                cons_table['Base Consumption'] - reduction['savings']
    
    ## get generation fule used (projects)
    names = []
    for p in projects:
        project = projects[p]
        ##print project.comp_specs['project details']
        name = 'nan' #project.comp_specs['project details']['name']
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        reduction = DataFrame([range(project.start_year,
                                project.actual_end_year+1)],['Year']).T
        reduction['savings'] = project.proposed_heat_recovery
        reduction = reduction.set_index('Year')
        reduction.index = reduction.index.astype(int)
        cons_table[name] = \
                    cons_table['Base Consumption'] - reduction['savings']
        names.append(name)
    
    
    ## format table
    if np.isnan(comp_no_project.get_net_benefit()).all():
        cons_table = cons_table[['year','Base Consumption'] + names]
    
        cons_table.columns = ['year','Base Case Diesel Consumed'] + names
        
    else:
        cons_table = cons_table[['year','Base Consumption', 
                                'Est. Heating Fuel Consumed'] + names]
    
        cons_table.columns = ['year','Base Case Diesel Consumed',
                                        'Modled Heating Fuel Consumed'] + names
    ## save to csv
    cons_table.to_csv(os.path.join(web_object.directory,'csv', 
                community + "_" + COMPONENT_NAME.replace(' ','_').lower() + "_" + 'consumption.csv'),
                index=False)
    
    ## make list form
    table2  = cons_table.\
                    round().values.tolist()
                    
    if np.isnan(comp_no_project.get_net_benefit()).all():
        table2.insert(0,['year', 'Current Projection'] + names)
    else:
        table2.insert(0,['year', 'Current Projection',
                      'Modeled Wind']+names)
    
    
    ## info for modled
   
        
    ests = comp_no_project.comp_specs['estimate data']
    current = [
        {'words':'Waste Heat Recovery Opperational', 'value': ests['Waste Heat Recovery Opperational']},
        {'words':'Add waste heat Avail', 'value': ests['Add waste heat Avail']},
        {'words':'Est. current annual heating fuel gallons displaced', 'value': ests['Est. current annual heating fuel gallons displaced']},
        {'words':'Est. potential annual heating fuel gallons displaced', 'value': ests['Est. potential annual heating fuel gallons displaced']},
    ]
        
    
    info = create_project_details_list(comp_no_project)
         
    ## info table (list to send to template)
    
    info_for_projects = [{'name': 'Current System', 'info':current}]
    
    if not np.isnan(comp_no_project.get_net_benefit()).all():
        info_for_projects.append({'name': 
                                    'Modeled '+ COMPONENT_NAME + ' Project',
                                  'info': info})
    
    ## get info for projects (updates info_for_projects )
    for p in projects:
        project = projects[p]
        name = project.comp_specs['project details']['name']
        info = create_project_details_list(project)
            
        info_for_projects.append({'name':name,'info':info})
            
    
    ## create list of charts
    charts = [
        {'name':'costs', 'data': str(table1).replace('nan','null'), 
         'title': 'Estimated Heating Fuel costs per year',
         'type': "'$'"},
        {'name':'consumption', 'data': str(table2).replace('nan','null'), 
         'title':'Heating Fuel Consumed gallons per year',
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
                                    
                                    
def create_project_details_list (project):
    """
    makes a projects details section for the html
    """
    try:
        costs = '${:,.0f}'.format(project.get_NPV_costs())
    except ValueError:
        costs = project.get_NPV_costs()
        
    try:
        benefits = '${:,.0f}'.format(project.get_NPV_benefits())
    except ValueError:
        benefits = project.get_NPV_benefits()
        
    try:
        net_benefits = '${:,.0f}'.format(project.get_NPV_net_benefit())
    except ValueError:
        net_benefits = project.get_NPV_net_benefit()
       
    try:
        BC = '{:,.2f}'.format(project.get_BC_ratio())
    except ValueError:
        BC = project.get_BC_ratio()
    
    return [
        {'words':'Captial Cost ($)', 
            'value': costs},
        {'words':'Lifetime Savings ($)', 
            'value': benefits},
        {'words':'Net Lifetime Savings ($)', 
            'value': net_benefits},
        {'words':'Benefit Cost Ratio', 
            'value': BC},
            ]
