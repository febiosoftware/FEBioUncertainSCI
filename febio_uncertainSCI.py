###################################################################################
#   FEBio-UncertainSCI
#=======================
# 
# This code applies the UncertainSCI library to FEBio. 
# The code allows users to evaluate uncertainty and sensitivity of FEBio model
# parameters on model output variables. 
#
# This code is distributed under the MIT license. See LICENSE file for details.
# Copyright 2021 - All rights reserved.
###################################################################################
import sys, time
import numpy as np
import json
from matplotlib import pyplot as plt
from itertools import chain, combinations

from febio_model import febio_function, febio_output, febio_output_parallel, read_model_output
from UncertainSCI.distributions import BetaDistribution, TensorialDistribution
from UncertainSCI.pce import PolynomialChaosExpansion
from UncertainSCI.indexing import TotalDegreeSet

try:
    import febio_cluster
    clusterErr = ""
except Exception as e:
    clusterErr = e

###################### COMMAND LINE PARSING ###############################

# Make sure we have three arguments
numArgs = len(sys.argv)
if (numArgs != 3) and (numArgs != 4)and (numArgs != 5):
    print('Usage: python febio_uncertainSCI.py <FEBio input file> <parameter file> [parallelJobs [threadsPerJob] | --cluster]')
    quit()

# first argument is FEBio input file name
febioFile = sys.argv[1]
print('FEBio input file: ', febioFile)

# second argument is parameter control file
controlFile = sys.argv[2]
print('Control file: ', controlFile)

# check for cluster flag
cluster = False
queueOnly = False
finalize = False
if "--cluster" in sys.argv:
    cluster = True
elif "--queue" in sys.argv:
    cluster = True
    queueOnly = True
elif "--finalize" in sys.argv:
    cluster = True
    finalize = True

# check for restart flag
restart = False
if "--restart"in sys.argv:
    restart = True

# check for parallel options
numParallelJobs = 1
numThreadsPerJob = 1
if (not cluster) and (not restart):

    if (len(sys.argv) >= 4):
        numParallelJobs = int(sys.argv[3])

    if (len(sys.argv) == 5):
        numThreadsPerJob = int(sys.argv[4])

###################### SETUP ###############################

# read the control file
f = open(controlFile)
data = json.load(f)

inParamCount = len(data['in'])
print(f'in parameters = {inParamCount}')

outParamCount = len(data['out'])
print(f'out parameters = {outParamCount}')

for i in data['in']:
    print(i)

for o in data['out']:
    print(o)

f.close()

# the number of parameters is one less than the number of lines
inparams = []
dists = []
for i in data['in']:
    inparams.append(i[0])
    fmin = float(i[1])
    fmax = float(i[2])
    bounds = np.array([[fmin], [fmax]])
    print(bounds)

    # Create a distribution for each parameter
    p1 = BetaDistribution(alpha=1, beta=1, domain=bounds)

    dists.append(p1)

print(inparams)

outparams = data['out']
print(outparams)

# Add all parameter distributions to this variable
p = TensorialDistribution(distributions=dists)

pceOrder = data['pce']['order']
print(f'PCE order = {pceOrder}')

############################ Build PCE #############################

index_set = TotalDegreeSet(dim=inParamCount, order=pceOrder)
pce = PolynomialChaosExpansion(distribution=p, index_set=index_set)

# first generate the samples
# if the restart flag was defined, we read the samples from the 'pcesamples.txt' file. 
if restart==False:
    pce.generate_samples()
    print(pce.samples)

    # write samples to file (for restart)
    fp = open('pcesamples.txt', 'w')
    for ind in range(pce.samples.shape[0]):
        v = pce.samples[ind, :]
        for d in v:
            fp.write(str(d)); fp.write(' ')
        fp.write('\n')
    fp.close()

if restart==True:
    # read samples from file
    fp = open('pcesamples.txt', 'r')
    allLines = fp.readlines()
    fp.close()
    M = len(allLines)
    print(M)
    newSamples = np.empty([M, inParamCount])
    i = 0
    for line in allLines:
        s = line.split(' ')
        for j in range(inParamCount):
            vj = float(s[j])
            newSamples[i, j] = vj
        i += 1
    print(newSamples)

    pce.samples = newSamples

# we're going to time the calls to FEBio
tic = time.time()

# evaluate model output. This will call FEBio for all samples
if cluster:
    if clusterErr:
        print("Could not import febio_cluster.py. Error message: ")
        print(clusterErr)
        quit()
    
    if queueOnly:
        febio_cluster.queueJobs(pce.samples, febioFile, inparams, outparams)
        quit()
    else:
        model_output = febio_cluster.febio_output_cluster(pce.samples, febioFile, inparams, outparams)
else:
    if restart==False:
        if (numParallelJobs == 1):
            model_output = febio_output(pce.samples, febioFile, inparams, outparams)
        else:
            print('Calling FEBio in parallel:')
            model_output = febio_output_parallel(pce.samples, febioFile, inparams, outparams, numParallelJobs, numThreadsPerJob)
    else:
        model_output = read_model_output('pceresults.txt')

# report time
toc = time.time()
    
# Calculate time it took to run suite
hours, remainder = divmod(int(toc-tic), 3600)
minutes, seconds = divmod(remainder, 60)

elapsedTime = '%s:%s:%s' % (hours, minutes, seconds)
    
print("Time elapsed:" + elapsedTime)

print(model_output)



################################### Statistics ##########################
for n in range(len(outparams)):
    outn = outparams[n]
    print(f'--- processing {outn} -----\n\n')

    # do the uncertainsci stuff
    outdata = model_output[n]
    pce.build_pce_wafp(model_output=outdata)

    mean = pce.mean()
    stdev = pce.stdev()
    print("Mean   = ", mean)
    print("St.dev.= ", stdev)

    variable_interactions = list(chain.from_iterable(combinations(range(inParamCount), r) for r in range(1, inParamCount+1)))

    global_sensitivity = pce.global_sensitivity(variable_interactions)

    print("Global sensitivities:")
    print(global_sensitivity)

    total_sensitivies = pce.total_sensitivity()
    print("Total sensitivities:")
    print(total_sensitivies)

    # Post-processing: sample the PCE emulator
    ensemble_size = int(1e6)
    ensembles = []
    pvals = p.MC_samples(M=ensemble_size)
    ensembles.append(pce.pce_eval(pvals))

    # Box plots require 1D arrays as input
    for i in range(len(ensembles)):
        ensembles[i] = ensembles[i].flatten()

    ## Construct boxplots
    plt.figure()
    plt.subplot(121)
    plt.boxplot(ensembles)
    tick_locations = [1 + i for i in range(len(ensembles))]
    tick_labels = ['UncertainSCI\n{1:d} samples\norder {0:d}'.format(pceOrder, pce.samples.shape[0])]
    tick_labels.append('Monte Carlo\n{0:1.1e} samples'.format(ensemble_size))
    plt.xticks(ticks=tick_locations, labels=tick_labels)
    plt.title(outn)

    # Sensitivity pie chart, averaged over all model degrees of freedom
    plt.subplot(122)
    average_global_SI = np.sum(global_sensitivity, axis=1)

    labels = ['[' + ' '.join(str(elem) for elem in [i+1 for i in item]) + ']' for item in variable_interactions]
    plt.pie(average_global_SI*100, labels=labels, autopct='%1.1f%%', startangle=90)

    plt.title('Global Sensitivity')
    
plt.show()
