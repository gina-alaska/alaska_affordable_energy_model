"""
Get API
-------

tools for geting data from Alaska Energy Data Gateway API

"""
import urllib2
import ssl
import json
from pandas import DataFrame



URL_RT = 'https://akenergygateway.alaska.edu/api/models/'

def get_api_data(name, show = True):
    """Get data from api as pandas DataFrame. Will get data starting from page
    1 of table, and the each page in response['next'] until response['next'] is
    None. 
    
    Parameters
    ----------
    name : string
        name of table on api (i.e. 'pcedata')
    
    Returns
    -------
    pandas.DataFrame
        Data from API table in name.
    
    """
    data = []
    context = ssl._create_unverified_context()
    # "https://akenergygateway.alaska.edu/api/models/pcedata/?format=api"
    url = URL_RT + name + '/?format=json'
    
    
    while True:
        content = urllib2.urlopen(url, context=context).read()
        temp = json.loads(content)
        data += temp['results']
        url = temp['next']
        if show:
            print url
        if url is None:
            break
    
    return DataFrame(data)
    
