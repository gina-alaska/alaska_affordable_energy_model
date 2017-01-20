************
Installation
************

instructions for installation

AAEM installation instructions
Step 1: Get the repos. 
https://github.com/gina-alaska/alaska_affordable_energy_model
https://github.com/gina-alaska/alaska_affordable_energy_model-data

	Note: repos are currently private 
Step 2: Install dependencies 
	Can be done using pip or an anaconda virtual environment 

	Open a Command Line Interface, and navigate to the location of the alaska_affordable_energy_model folder.
2a: using pip
	Be sure python(2.7) is installed then us pip:
	pip install --user -r requirements.txt
2b:  using Anaconda
	Install the conda pacage manager for python(2.7) http://conda.pydata.org/miniconda.html

	Set up the environment from file:
	conda env create -f environment.ymal

	Activate the environment. Be sure to do this each time you want to use the project. 
	linux/mac: source activate AAEM_env
windows: activate AAEM_env

To deactivate the environment when finished.
	linux/mac: source deactivate AAEM_env
windows: deactivate AAEM_env



Step 3: Install AAEM package
	From the alaska-affordable-energy-model directory 
3a: development installation/uninstallation 
	The the development version  will allow the package to be modified without reinstalling it during development. 
Development install:python setup.py develop --user
Development uninstall: python setup.py develop -u
3b: regular installation
	Install: python setup.py install --user
	
4: add utility to path
For linux/mac:
From your home directory open .bash_profile in a text editor, and add the aaem bin directory to the path.

Add something similar to this:
export PATH="<path to aaem repo>/alaska_affordable_energy_model/bin/:$PATH"
	
5: perform initial setup 
This will set up the model and add run it:

	aaem setup <path to setup location> <path to data repo>

	See the AAEM CLI document from more information on the aaem command line interface commands including the setup command.
