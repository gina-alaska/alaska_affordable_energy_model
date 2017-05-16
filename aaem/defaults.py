"""
defaults.py

for generating default config structures
"""


from pandas import DataFrame



base_structure = {
    'community': {
        'model electricity': bool,
        'file id': str,
    
        'name': str,
        'alternate name': str,
        'region': str,
        'GNIS ID': int,
        'FIPS ID': int,
        'senate district': list,
        'house district': list,
        'population': DataFrame,
        'intertie': [list, str], 
        'heating degree days': float,
        'heating fuel premium': float,
        'on road system': bool,
        
        'diesel prices': DataFrame,
        'electric non-fuel prices': DataFrame,
        
        'residential non-PCE electric price': float,
        'electric non-fuel price': float,
        'propane price': float,
        'cordwood price': float,
        'pellet price': float,
        'natural gas price': float,
        
        
        'utility info': DataFrame,
        'precent diesel generation': float,
        'line losses': float,
        'diesel generation efficiency': float,
        'heat recovery operational': bool,
        'switchgear suatable for renewables': bool,
        
        'hydro generation limit': float,
        'solar generation limit': float,
        'wind generation limit': float,
        'hydro capacity': float,
        'solar capacity': float,
        'wind capacity': float,
        
        'max wind generation precent': float,
    }

}


base_comments = {
    'community': {
        'name': str,
        'alternate name': str,
        'region': str,
        'GNIS ID': int,
        'FIPS ID': int,
        'senate district': list,
        'house district': list,
        'population': DataFrame,
        'intertie': [list, str], 
        'heating degree days': float,
        'heating fuel premium': float,
        'on road system': bool,
        
        'diesel prices': DataFrame,
        'electric non-fuel prices': DataFrame,
        
        'electric non-fuel price': float,
        'propane price': float,
        'cordwood price': float,
        'pellet price': float,
        'natural gas price': float,
        
        
        'untility info': DataFrame,
        'precent diesel generation': float,
        'line losses': float,
        'diesel generation efficiency': float,
        'heat recovery operational': bool,
        'switchgear suatable for renewables': bool,
        
        'hydro generation limit': float,
        'solar generation limit': float,
        'wind generation limit': float,
        'hydro capacity': float,
        'solar capacity': float,
        'wind capacity': float,
    }

}
