.. _scripts:

**************************
Running AAEM from a script
**************************

The Alaska Affordable Energy Model supports the option to run from a script file. This allows communities to be modeled with a variety of different configurations or sets of scalers applied. When the model is run frim a script file the results are stored together, even if the same community is being run multiple times.

The model may be run from a script as follows:

.. code-block:: bash

    aaem run script.yaml

The script file is simply a yaml file with the following format:

.. code-block:: yaml

    global:
      root: <PATH TO MODEL>
      global config: <PATH TO ALTERNATE GLOBAL CONFIG>
      results tag: <TAG NAME FOR RESULTS FOLDER>
      
    communities:
      - community: <COMMUNITY NAME>
        ID: <ID TO USE WHEN SAVING RESULTS [1]>
        config: <PATH TO CONFIGURATION FILE, optional [2]>
        scalers: <SCALERS TO USE, optional [3]>
          diesel price: <FLOAT>
         diesel price adder: <FLOAT>
          capital costs: <FLOAT>
          kWh consumption: <FLOAT>
    
      - community: <COMMUNITY NAME>
        ID: <ID TO USE WHEN SAVING RESULTS [1]>
      
      .
      .
      .
    
      - community: <COMMUNITY NAME>
        ID: <ID TO USE WHEN SAVING RESULTS [1]>

    
.. [1] required if same community is being run multiple times. Each time the community is run in the same script it should have a unique ID
.. [2] if not provided will use configuration located at <root>/config/<community>.yaml
.. [3] any of the scalers listed here may be used, see below for descriptions. 

The format above two sections: global and communities. The global section defines the file setup for the model to run and the global configuration. The communities section has a list of communities to run.

The global section contains three attributes: root, global config, and results tag. 
    * root: defines path to model setup, relative to where the command was run, or absolute. The model setup should contain a config directory with all configuration yaml files for communities listed to run without explicitly specified configurations  
    * global config: a configuration yaml file. This file can contain all default values that are used by every community run. Remember that these values will be over written by values in the community configuration files if same attributes are supplied. 
    * results tag: This is the tag for the results folder. If ABC is the results tag, the results of this script will be stored in <root>/results_ABC.

The community section has a list of communities to run. Each list item should contain the community attribute, and may contain the ID, config, and scalers attributes.
    * community: default name of community. Should match the name of a configuration yaml file in <root>/config unless the config attribute specifies a configuration file to use
    * ID: an ID to save the results under. This field is required if the same community is listed multiple times. Each ID field should be unique. The symbol + should not be used in ID.
    * config: path to a yaml configuration file, optional
    * scalers: set of scalers to modify a community’s behavior in the model, optional. See scalers section for details on scalars that may be used 


Scalers modify the behavior of the AAEM for a community. The scalers available are diesel price, diesel price added, capital costs, and kWh consumption.
    * diesel price: the diesel prices are multiplied by this value when it is loaded in to the model. Will also modify the electric non-fuel prices. Can be used with diesel price adder [4]_. 
    * diesel price added: the diesel prices are added to this value when it is loaded in to the model. Will also modify the electric non-fuel prices. Can be used with diesel price [4]_. 
    * capital costs: the capital costs for all projects are multiplied by this value right before the annual costs are determined.
    * kWh consumption: the known electric consumption is multiplied by this value before consumption is forecasted.

.. [4] If diesel price and diesel price adder are used together the following behavior is achieved: [diesel prices] = diesel price * [diesel prices] + diesel price adder


Example script: 

.. code-block:: yaml
    
    global:
      root: ./model/script_example 
      results tag: adak_capital_costs
      
    communities:
      - community: Adak
        ID: Adak base
        scalers: 
          capital costs: 1.0
    
      - community: Adak
        ID: Adak plus 10 %
        scalers: 
          capital costs: 1.1
    
      - community: Adak
        ID: Adak plus 20 %
        scalers: 
          capital costs: 1.2
    
      - community: Adak
        ID: Adak plus 30 %
        scalers: 
          capital costs: 1.3
    
    
    
    
    
