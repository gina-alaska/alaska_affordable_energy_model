"""
common web functions

"""
import os.path
import numpy as np
from pandas import DataFrame
import aaem.constants as constants
from aaem.components import comp_order

def get_projects (web_object, community, comp, tag):
    """
    get a communities projects for a provided copoonent
    
    inputs:
        web_opject: an aaem.web.WebSummary object
        community: a community <string>
        comp: name of component <string>
        tag: tag used in results directory to indicate it is a project for the 
            provided component
            
    outputs:
        returns: projects, a dictioanry of communites projects for the 
        component, start_year: eariliest start year in projects. end_year,
        latest actual end year in projects
    """
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
    
    inputs:
        community: <string>
        comp: componet name <string>
        projects: dictioany of projects
        base_cost: dataframe with base cost for all years needed as index
                    Base Cost
            2011    1200
            ...
            2015    1400
        directory: directory where web outputs are beign saved
    
    outputs:    
        returns plotting_table, a table that can be used to make a google chart
    """
    costs_table = DataFrame(base_cost)
    costs_table['year'] = costs_table.index
    names = []
    for p in projects:
        project = projects[p]
        ##print project.comp_specs['project details']
        try:
            name = project.comp_specs['name']
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        if name is None:
            name = p
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
    costs_table.columns = ['year','Base case cost'] + [ n[0].upper() +n[1:].lower() for n in names] 
    fname = community + "_" + comp.replace(' ','_').lower() + "_" + 'costs.csv'
    
    try:
        os.makedirs(os.path.join(directory,community.replace("'",""),'csv'))
    except OSError:
        pass
    costs_table.to_csv(os.path.join(directory,community.replace("'",""),'csv', fname),
                        index=False)
    #~ ## make list from of table
    plotting_table = costs_table.\
                    round().values.tolist()
                    
    header = []
    for name in ['year','Current projection'] + [ n[0].upper() +n[1:].lower() for n in names] :
        header.append("{label: '"+name+"', type: 'number'}")
    plotting_table.insert(0,header)
    return plotting_table
    
def make_consumption_table (community, comp, projects, base_con, 
                            directory, savings_attribute):
    """
    make a table
    
    inputs:
        community: <string>
        comp: componet name <string>
        projects: dictioany of projects
        base_con: dataframe with base cost for all years needed as index
                    Base Consumption
            2011    1200
            ...
            2015    1400
        directory: directory where web outputs are beign saved
        savings_attribute: string representing the savings attribute/ function 
            in the current component
    
    outputs:    
        returns plotting_table, a table that can be used to make a google chart
    """
    cons_table = DataFrame(base_con)
    cons_table['year'] = cons_table.index
    names = []
    for p in projects:
        project = projects[p]
        ##print project.comp_specs['project details']
        try:
            name = project.comp_specs['name']
        except KeyError:
            name = 'nan'
        if name == 'nan':
            name = p.replace('+', ' ').replace('_',' ')
        if name is None:
            name = p
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
    cons_table.columns = ['year','Base case diesel consumed'] + [ n[0].upper() +n[1:].lower() for n in names] 
    fname = community + "_" + comp.replace(' ','_').lower() +\
            "_" + 'consumption.csv'
    try:
        os.makedirs(os.path.join(directory,community.replace("'",""),'csv'))
    except OSError:
        pass
    cons_table.to_csv(os.path.join(directory,community.replace("'",""),'csv', fname),index=False)
    #~ ## make list from of table
    plotting_table = cons_table.round().values.tolist()
    
    header = []
    for name in ['year','Current projection'] + [ n[0].upper() +n[1:].lower() for n in names] :
        header.append("{label: '"+name+"', type: 'number'}")
    plotting_table.insert(0,header)
    return plotting_table

def correct_dates (start, s1, end, e1):
    """ 
        takes start and end years from the modeled projcet and other prjects 
    and finds the start and end year to use
    
    inputs:
        start: modeled start year <int>
        s1: pojects start year <int>
        end: modeled end year <int>
        e1: pojects end year <int>
        
    outputs: 
        returns start_year, end_year
    """
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

def create_electric_system_summary (web_object, community ):
    """
    creates a summary of the corrent electrical systems
    
    inputs:
        community_results the results for a given community
        
    returns a list of items to use with the html template
    """
    community_results = web_object.results[community]
    fc = community_results['forecast']
    hydro = community_results['Hydropower']
    solar = community_results['Solar Power']
    wind = community_results['Wind Power']
    
    expected_wind_total = wind.cd['wind generation limit']
    expected_hydro_total = hydro.cd['hydro generation limit']
                                        
                                        
    expected_solar_total = \
        '{:,.0f} kWh/year'.format(solar.generation_proposed[0])
    
    
    
    total_gen = \
        fc.cd.get_item('community','utility info')['net generation'].iloc[-1:]
    #~ print 
    total_load = float(total_gen)/constants.hours_per_year
    year = int(total_gen.index[0])
    
    
    h_gen = float(fc.cd.get_item('community',
            'utility info')['generation hydro'].iloc[-1:])
    w_gen = float(fc.cd.get_item('community',
            'utility info')['generation wind'].iloc[-1:])
    s_gen = float(fc.cd.get_item('community',
            'utility info')['generation solar'].iloc[-1:])
    
    current = [
        {'words':'Average community load (' + str(year) +')',
         'value': '{:,.0f} kW'.format(total_load)},
        {'words':'Average generation (' + str(year) +')' , 
         'value': '{:,.0f} kWh/year'.format(float(total_gen))},
        {'words':'Peak load', 'value': 'Unknown'},
        {'words':'Existing nameplate wind capacity', 
         'value': 
             '{:,.0f} kW'.format(
             float(wind.cd['wind capacity']))},
        {'words':'Existing wind generation (' + str(year) +')',
         'value': '{:,.0f} kWh/year'.format(w_gen).replace('nan','0')},
        {'words':'Estimated proposed wind generation',
         'value': '{:,.0f} kWh/year'.format(expected_wind_total)},
        {'words':'Existing nameplate solar capacity', 
         'value': 
             '{:,.0f} kW'.format(
             float(solar.cd['solar capacity']))},
        {'words':'Existing solar generation (' + str(year) +')', 
         'value': '{:,.0f} kWh/year'.format(s_gen).replace('nan','0')},
        {'words':'Estimated proposed solar generation',
         'value': expected_solar_total},
        {'words':'Existing nameplate hydro capacity ', 
         'value': 
             '{:,.0f} kW'.format(
             float(fc.cd.get_item('community','hydro capacity')))},
        {'words':'Existing hydro generation (' + str(year) +')', 
         'value': '{:,.0f} kWh/year'.format(h_gen).replace('nan','0')},
        {'words':'Estimated proposed hydro generation',
         'value': '{:,.0f} kWh/year'.format(expected_hydro_total)}
    ]
    return current
