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

