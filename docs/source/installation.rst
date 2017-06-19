************
Installation
************



Step 1: Get the repos
======================

Get these repositories:

https://github.com/gina-alaska/alaska_affordable_energy_model

https://github.com/gina-alaska/alaska_affordable_energy_model-data

Step 2: Install dependencies 
============================

Installation can be done using pip or an anaconda virtual environment. See :ref:`software` for infromation on software used.


Open a Command Line Interface, and navigate to the location of the alaska_affordable_energy_model folder.

2a: using pip
~~~~~~~~~~~~~
	
Be sure python(2.7) is installed then us pip:

.. code-block:: bash

    pip install --user -r requirements.txt
    

2b: using Anaconda
~~~~~~~~~~~~~~~~~~
Install the conda pacage manager for python(2.7) http://conda.pydata.org/miniconda.html

Set up the environment from file:

.. code-block:: bash

    conda env create -f environment.ymal


Activate the environment. Be sure to do this each time you want to use the project. 

linux/mac: 

.. code-block:: bash

    source activate AAEM_env

windows:

.. code-block:: bash

    activate AAEM_env

To deactivate the environment when finished.

linux/mac: 

.. code-block:: bash

    source deactivate AAEM_env

windows: 

.. code-block:: bash

    deactivate AAEM_env


Step 3: Install AAEM package
============================

From the alaska-affordable-energy-model directory 

3a: regular installation
~~~~~~~~~~~~~~~~~~~~~~~~

Install:
 
.. code-block:: bash

    python setup.py install --user

3b: development installation/uninstallation 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The the development version  will allow the package to be modified without reinstalling it during development. 

Development install: 

.. code-block:: bash

    python setup.py develop --user

Development uninstall: 

.. code-block:: bash

    python setup.py develop -u

	
Step 4: add utility to path
===========================

For linux/mac:
~~~~~~~~~~~~~~

From your home directory open .bash_profile in a text editor, and add the aaem bin directory to the path.

Add something similar to this:

.. code-block:: bash

    export PATH="<path to aaem repo>/alaska_affordable_energy_model/bin/:$PATH"
    
For windows
~~~~~~~~~~~

Add the python27 and aaem/bin directory to your path using a powershell profile. 

Follow the first few setps here to create a power shell profile here if nessary:
https://www.howtogeek.com/50236/customizing-your-powershell-profile/

add python and aaem/bin directory like this

.. code-block:: bash
    
    $env:path += ";C:\Python27;C:\Users\user\alaska_affordable_energy_model\bin"
    
    

	
Step 5: perform initial setup 
=============================

This will set up the model and add run it:

.. code-block:: bash

    aaem setup <path to setup location> <path to data repo>

See :ref:`CLI` documentation from more information on the aaem command line interface commands including the setup command.
