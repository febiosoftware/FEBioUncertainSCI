# FEBioUncertainSCI
This project aims to couple FEBio with the UncertainSCI package for uncertainty quantification. 

Disclaimer: This is a work in progress and at this point very rudimentary. Use at your own risk! 

## Prerequisites
To run this tool, you will need:
- The latest development version of FEBio. (You can update to the latest development version from FEBio Studio: Go to menu Options\Tools, find the Auto-update settings, and click the "Update to development version" button.)
- A python version (this has been tested on 3.8.10)
- The UncertainSCI package (https://www.sci.utah.edu/cibc-software/uncertainsci.html). Note that this package does not work with Python 3.10 (last checked on Nov 2021). 

## Instructions
To run this tool, you will need to prepare two files: 

- first, you need a FEBio model file. A test model file (Model1.feb) is provided. 
- second, you need to create the parameter control file, which lists the input parameters that you wish to test, as well as min and max value, and the output parameters that define the dependent variables. A sample control file (control.json) is provided. Note that the control file uses a JSON structure. 

With the two files prepared, you can run the analysis with the following command line:

python febio_uncertainSCI.py Model1.feb control.json

The tool generates two files: 
- run.feb : This is an intermediate file that is used to run FEBio with the provided model parameters. 
- out.txt : This file contains the output of the FEBio analysis and will be read back into the tool. 
Both files will be overwritten multiple times while the tool runs. Do not delete or try to change these files while the tool is running. 
Once the tool completes, you may delete these files. 

If all goes well, you will see a box plot, generated from sampling the PCE, and a pie chart that lists the global sensitivities for the different parameters and their interactions.

Good luck!
