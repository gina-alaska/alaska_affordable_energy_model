"""
Yaml DataFrame conversion tools
-------------------------------

Tools for coverting DataFrames to sinppets of yaml files and dictionarys
loaded from those snippes back to DataFrames

"""
from pandas import DataFrame

def dataframe_to_dict(dataframe):
    """Convert a DataFrame to a dictioanry that is eaisly convertable back to
    a data frame. Each column key value pair in the
    dict {"column name": list of values}. The index is added to the dict as
    {index name: list of index values}. Finaly 'INDEX' and 'ORDER' keys
    are addded to dict with the Index name(str) and order of columns (list) as
    values.

    Parameters
    ----------
    dataframe: Pandas.DataFrame
        the data frame to convert

    Returns
    -------
    dict
        the converted data frame
    """
    index = [f for f in dataframe.index.tolist()]
    vals = [index] + dataframe.values.T.tolist()

    cols = [dataframe.index.name] + dataframe.columns.tolist()
    dictionary ={}
    for i in range(len(cols)):
        dictionary[cols[i]] = vals[i]

    dictionary['INDEX'] = dataframe.index.name
    dictionary['ORDER'] = list(dataframe.columns)
    return dictionary

def get_metadata_and_data (dictionary):
    """Seperate and return the data and meta data from a dataframe dictionary

    Parameters
    ----------
    dictionary : dict
        dictionary with keys INDEX, ORDER, and the values of INDEX and ORDER

    Returns
    -------
    Index: str
        the index key
    Order: list
        the order of columns
    Data: dict
        the data and index values
    """
    index = dictionary['INDEX']
    order = dictionary['ORDER']
    temp = {k: dictionary[k] for k in dictionary if not k in ['INDEX', 'ORDER']}
    return index, order, temp

def dict_to_dataframe (dictionary):
    """Convert a DataFrame dictionary back to a DataFrame

    Parameters
    ----------
    dictionary : dict
        dictionary with keys INDEX, ORDER, and the values of INDEX and ORDER

    Returns
    -------
    DataFrame
        the DataFrame created from the dictionary
    """
    index, order, temp = get_metadata_and_data(dictionary)
    return DataFrame( temp ).set_index(index)[order]


def dict_to_yaml_snippet (dictionary, indent = '  ', level = 2, newline = '\n'):
    """Convert a dataframe Dictionary to a formated yaml snippet

    Parameters
    ----------
    dictionary : dict
        dictionary with keys INDEX, ORDER, and the values of INDEX and ORDER
    indent : str, optional
    level : int , optional
    newline: str, optional

    Returns
    -------
    string
        a fromated string in the yaml style

    """
    index, order, temp = get_metadata_and_data(dictionary)
    text = ""
    #add metadata
    text += indent * level + 'INDEX' +': ' + index + newline
    text += indent * level + 'ORDER' +': ' + str(order) + newline
    # add data
    for row in [index] + order:
        as_str = str(temp[row])
        text += indent * level + row +': ' + as_str + newline

    return text


def dataframe_to_yaml_snippet (dataframe,
        indent = '  ', level = 2, newline = '\n'):
    """Converts a DataFrame to a formatted yaml snippet

    Parameters
    ----------
    dataframe: Pandas.DataFrame
        the data frame to convert
    indent : str, optional
    level : int , optional
    newline: str, optional

    Returns
    -------
    string
        a fromated string in the yaml style
    """
    dictionary = dataframe_to_dict(dataframe)
    return dict_to_yaml_snippet(dictionary, indent, level, newline)

