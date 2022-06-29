# FEBioUncertainSCI
This project aims to couple FEBio with the UncertainSCI package for uncertainty quantification. 

**Disclaimer**: This is a work in progress and at this point very rudimentary. Use at your own risk! 

## 1. Prerequisites
To run this tool, you will need:
- FEBio version 3.7 or newer.
- A python version (this has been tested with Python 3.8.10) as well as the numpy library. 
- The UncertainSCI package (https://www.sci.utah.edu/cibc-software/uncertainsci.html). Note that this package does not work with Python 3.10 (last checked on Nov 2021). 

## 2. Instructions
To run this tool, you will need to prepare two files: 

- first, you need a FEBio model file. A test model file (Model1.feb) is provided. 
- second, you need to create the parameter control file, which lists the input parameters that you wish to test, as well as min and max value, and the output parameters that define the dependent variables. A sample control file (control.json) is provided. Note that the control file uses a JSON structure. Additional information on the structure and contents of the control file is described below. 

With the two files prepared, you can run the analysis with the following command line:

`python febio_uncertainSCI.py Model1.feb control.json`

The tool generates two files: 
- run.feb : This is an intermediate file that is used to run FEBio with the provided model parameters. 
- out.txt : This file contains the output of the FEBio analysis and will be read back into the tool. 
Both files will be overwritten multiple times while the tool runs. Do not delete or try to change these files while the tool is running. 
Once the tool completes, you may delete these files. 

If all goes well, you will see a box plot, generated from sampling the PCE, and a pie chart that lists the global sensitivities for the different parameters and their interactions.

Good luck!

## 3. Control file structure
The control file is a JSON file and lists all the necessary parameters for the uncertainty quantification. It contains the following blocks:

- pce: defines the control parameters for the UncertainSCI tool. 
- in : lists the FEBio model parameters for which the sensitivity will be evaluated. 
- out: lists the FEBio output parameters for the the uncertainty is calculated. 

### 3.1. the pce block
The pce block defines the control parameters that the UncertainSCI tool needs to run the analysis. The following parameters are supported: 

- order: The order of the pce
- oversamples: The number of additional samples that will be used in addition to the default samples determined by the UncertainSCI tool. 

### 3.2. the in block
The in block defines the list of FEBio model parameters for which UncertainSCI will determine the sensitity of. 
For each parameter, the name and a value range must be defined. For example,

```
["fem.material[0].E",  0.1, 2.0]
```

Notice that the parameter name must be inside quotes. The values define the min, and max value respectively of the domain that will be sampled. 
(Currently, the domain will be sampled uniformly. In the future other sampling methods will be added.) 

### 3.3. the out block
The out block defines the list of output parameters that will be used to evaluate the uncertainty of. The sensitivity of the input parameters with respect to these output parameters will be calculated. 

### 3.4. Example control file
The following control file uses a pce of order 4 and quantifies the sensitivity of two model input parameters (E, v) on the output parameter, the x-component of the rigid body reaction force. 

```
{
    "pce" :
    {
        "order" : 4
    },
    "in" : [
        ["fem.material[0].E",  0.1, 2.0],
        ["fem.material[0].v", 0.0, 0.495]
    ],
    "out" : [
        "fem.rigidbody('rigid').Fx"
    ]
}
```

## Advanced options
By default, the FEBioUncertainSCI will run locally and sequentially (FEBio may still run in parallel). Using the advanced options, the tool can be run in parallel, and even on a remote cluster. 

The full command line is:  
`python febio_uncertainSCI.py <FEBio input file> <control file> [parallelJobs [threadsPerJob] | --cluster]`

The options are:
- FEBio input file: The name of the FEBio input file
- parameter file: The name of the control file
- parallelJobs: The number of FEBio jobs that will be run in parallel
- threadsPerJob: The number of threads for each FEBio job
- cluster: Run the FEBio jobs on a remote cluster 

Note that if the parallelJobs is specified and the threadsPerJob omitted, each FEBio job will try to run with all avaialble processors (unless FEBio is configured differently), which may significantly degrade performance. 

### Running on a cluster
You can use FEBioUncertainSci to queue your jobs on a cluster that is using the SLURM queueing system. 

#### Setting your cluster settings
Before using FEBioUncertainSci to launch jobs on your cluster, you must first edit the cluster_settings.py script found in this repository. This script looks like this


```
HOSTNAME = ""
USERNAME = ""
REMOTEDIR = ""
REMOTEFEBIO = ""

SLURMDIR = ""
SBATCH = SLURMDIR + "sbatch"
SQUEUE = SLURMDIR + "squeue"

SCRIPT ='''#!/bin/bash
#SBATCH --nodes=1               # Run all processes on a single nodes
#SBATCH --ntasks=1              # Run a single task
#SBATCH --cpus-per-task=10     # Number of CPU cores per task
'''
```

Set the proper values for your cluster's hostname, your username on the cluster, the directory on the remote server to which you want the FEBio input files to be copied and in which FEBio will be run, and the full path to an FEBio exectuable located on your remote server. You can also set the SLURMDIR variable to the path containing your SLURM exectuables if you get errors saying that the system can't find your sbatch or squeue commands. 

FEBio cannot run on multiple nodes, but you can set the number of processors FEBio will use be eddting the cpus-per-task value in the script above. 


#### Queing the jobs
There are 2 ways to queue jobs onto your cluster using FEBioUncertainSci. 

The first is to pass the `--cluster` flag to FEBioUncertainSci. This will have FEBioUncertainSCi transfer the necessary files to your server, queue the jobs on your cluster, wait for the jobs to finish, transfer the output files back, and then run the uncertainty analysis on those files. 

If, however, you know that your jobs will take some time to run, and you dont' want to leave FEBioUncertainSci running on your local machine while you wait for the jobs to finish, you can simply queue the jobs using the `--queue` flag. This will just transfer the necessary files to your server, and queue the jobs on your cluster. Then, at a later time, when you are sure that all of those jobs have finished, your can rerun FEBioUncertainSci with both the `--cluster` and `--restart` flags (please note that you still have to pass it the FEBio input file, and the control file). This will connect to your server, transfer the output files back, and then run the uncertainty analysis on those files.
