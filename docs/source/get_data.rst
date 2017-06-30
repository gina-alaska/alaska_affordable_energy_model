.. _get_data:

*********************************************************
Pulling updated data from the Alaska Energy Data Gateway.
*********************************************************

Some of the data sources used by the Alaska Affordable Energy Model are stored in the Alaska Energy Data Gateway(AEDG).  Data in the AEDG may be more current than that stored in the alaska_affordable_energy_model-data repo.  The get-data command allows for creation of a directory with the most current AEDG data, while still using the alaska_affordable_energy_model-data git repo for data not available in the AEDG.  Note: The data in the alaska_affordable_energy_model-data repo has been tested and is known to work.

To run the get-data command:

.. code-block:: bash

    aaem get-data path_to_repo path_to_new_data

* path_to_repo: is the path to a local copy of the alaska_affordable_energy_model-data repo
* path_to_new_data: is the path to where the new data will be put

Then the setup command can be used to set up the model with your new data:

.. code-block:: bash

    aaem setup path_to_setup_model path_to_new_data

or 

.. code-block:: bash

    aaem refresh path_to_setup_model path_to_new_data


* path_to_setup_model: is the path to create the model files
* path_to_new_data: same path as before, where the new data is

After completing these steps, the model may be run, and refreshed as normal. 

    
