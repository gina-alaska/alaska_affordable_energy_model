import aaem.driver as driver
import numpy as np
from pandas import DataFrame

from jinja2 import Environment, PackageLoader
import os

def generate_scenario_table ( root = 'model/', tag = 'diesel_price_scenario'):
    
    m = driver.Driver(root)
    results = m.load_results( tag )
    data = {}
    coms = []
    i = 0
    bases = []
    for k in sorted(results.keys()):
        
        temp = {}
        if results[k]['community data'].get_item('community','diesel prices').scaler_used == 1:
            bases.append(i)
        temp[results[k]['wind power'].cd['name']] = results[k]['wind power'].get_BC_ratio()
        try:
            temp['Diesel Price'] =  np.npv(results[k]['wind power'].cd['discount rate'],results[k]['wind power'].diesel_prices[:results[k]['wind power'].actual_project_life])/results[k]['wind power'].actual_project_life
        except:
            continue
        data[k] = temp
        coms.append(results[k]['wind power'].cd['name'])
        i +=1 
    
    data = DataFrame(data).T
    data = data.round(2)
    
    coms = sorted(set(coms))
    data = data[['Diesel Price'] + coms]
    data['Minimum Viability'] = np.nan
    #~ data["""KEY"""] = np.nan
    #~ data["""KEY"""].iloc[bases] = 'point { size: 18; shape-type: star; fill-color: #a52714; }'
    #~ v = """{'type': 'string', 'role': 'style'}"""
    data = data.values.tolist()
    data.append([0]+ list(np.zeros(len(coms))+np.nan) + [1])#, np.nan])
    data.append([12]+ list(np.zeros(len(coms))+np.nan) + [1])#, np.nan])
    data.insert(0, ['Diesel Price'] + coms + ['Minimum Viability'])#,"'key'"])
    return str(data).replace('nan','null').replace('], ','],\n')#.replace("'key'", "{'type': 'string', 'role': 'style'}").replace('"','')
    


def save_html (directory):
    """ Function doc """
    env = Environment(loader=PackageLoader('aaem','templates/'))
    template = env.get_template('scenario.html')
    pth = os.path.join(directory, 'diesel_prices_scenario.html')
    
    table = generate_scenario_table()
    
    charts = [{'name':'D_PRICE', 'data': str(table).replace('nan','null'), 
                    'title': 'Wind Power: B/C Ratio vs. Average Diesel Price',
                    'type': "'$'"}]
    
    with open(pth, 'w') as html:
        html.write(template.render( title = "Diesel Prices Scenario",
                                    charts = charts ))

    
save_html("web")
#~ generate_scenario_table()
    
