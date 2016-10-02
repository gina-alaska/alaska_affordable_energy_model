import os.path
import numpy as np
from pandas import DataFrame
import aaem.constants as constants
from aaem.components import comp_order

def get_projects (web_object, community, comp, tag):
    projects = {}
    start_year = np.nan
    end_year = np.nan
    for i in [i for i in sorted(web_object.results.keys()) \
         if i.find(community) != -1 and i.find(tag) != -1]:
        
        if np.isnan(start_year):
            start_year = web_object.results[i][comp].start_year
            
        if np.isnan(end_year):
            end_year = web_object.results[i][comp].actual_end_year
             
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
    
def make_consumption_table (community, comp, projects, base_con, 
                            directory, savings_attribute):
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
    fname = community + "_" + comp.replace(' ','_').lower() +\
            "_" + 'consumption.csv'
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

def create_electric_system_summary (community_results):
    
    fc = community_results['forecast']
    hydro = community_results['Hydropower']
    solar = community_results['Solar Power']
    wind = community_results['Wind Power']
    
    total_gen = fc.cd.get_item('community','generation').iloc[-1:]
    total_load = float(total_gen)/constants.hours_per_year
    year = int(total_gen.index[0])
    
    
    h_gen = float(fc.cd.get_item('community',
            'generation numbers')['generation hydro'].iloc[-1:])
    w_gen = float(fc.cd.get_item('community',
            'generation numbers')['generation wind'].iloc[-1:])
    s_gen = float(fc.cd.get_item('community',
            'generation numbers')['generation solar'].iloc[-1:])
    
    current = [
        {'words':'Average Community Load (kW)(' + str(year) +')',
         'value': '{:,.0f}'.format(total_load)},
        {'words':'Average kWh/year' + str(year) +')' , 
         'value': '{:,.0f}'.format(float(total_gen))},
        {'words':'Peak Load', 'value': 'Unknown'},
        {'words':'Existing nameplate wind capacity (kW)', 
         'value': wind.comp_specs['resource data']['existing wind']},
        {'words':'Existing wind generation (kWh/year)(' + str(year) +')',
         'value': '{:,.0f}'.format(w_gen).replace('nan','0')},
        {'words':'Existing nameplate solar capacity (kW)', 
         'value': solar.comp_specs['data']['Installed Capacity']},
        {'words':'Existing solar generation (kWh/year)(' + str(year) +')', 
         'value': '{:,.0f}'.format(s_gen).replace('nan','0')},
        {'words':'Existing nameplate hydro capacity (kW)', 
         'value': fc.cd.get_item('community','hydro generation limit')},
        {'words':'Existing hydro generation (kWh/year)(' + str(year) +')', 
         'value': '{:,.0f}'.format(h_gen).replace('nan','0')},
    ]
    return current
                                    
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
