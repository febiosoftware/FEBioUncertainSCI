# FEBioUncertainSCI
This project aims to couple FEBio with the UncertainSCI package for uncertainty quantification. 

Disclaimer: This is a work in progress and at this point very rudimentary. Use at your own risk! 

## Prerequisites
To run this tool, you will need:
- The latest development version of FEBio. (You can update to the latest development version from FEBio Studio: Go to menu Options\Tools, find the Auto-update settings, and click the "Update to development version" button.)
- A python version (this has been tested on 3.8.10)
- The UncertainSCI package (https://www.sci.utah.edu/cibc-software/uncertainsci.html). Note that this package does not work with Python 3.10 (last checked on Nov 2021). 

## Instructions
To run this tool, you will first need a FEBio model file. A test model file (Model1.feb) is provided. 

Then, decide which model parameters of the model you wish to use in uncertainty quantification. 
The code is currently setup to use the E and v parameters of the test model's material. 

You will need to make changes to the following files: 
- febio_model.py: where you will enter the model parameters
- febio_uncertainSCI.py: where you will update the code to make sure the correct number of variables are used. 

There are additional instructions in these files (look for comments that start with TODO).

Once all changed are made, you can run the tool using the following command:
python febio_uncertainSCI.py

The tool generates two files: 
- run.feb : This is an intermediate file that is used to run FEBio with the provided model parameters. 
- out.txt : This file contains the output of the FEBio analysis and will be read back into the tool. 
Both files will be overwritten multiple times while the tool runs. Do not delete or try to change these files while the tool is running. 
Once the tool completes, you may delete these files. 

If all goes well, you will see a box plot.

Good luck!
