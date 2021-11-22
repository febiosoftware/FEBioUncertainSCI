import sys, time
import numpy as np
from matplotlib import pyplot as plt
from itertools import chain, combinations

from febio_model import febio_function, febio_output, febio_output_parallel
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
if (len(sys.argv) != 3) and (len(sys.argv) != 4)and (len(sys.argv) != 5):
    print('Usage: python febio_uncertainSCI.py <FEBio input file> <parameter file> [parallelJobs [threadsPerJob]]')
    quit()

# first argument is FEBio input file name
febioFile = sys.argv[1]
print('FEBio input file: ', febioFile)

# second argument is parameter control file
controlFile = sys.argv[2]
print('Control file: ', controlFile)

cluster = False
if sys.argv[3] == "--cluster":
    cluster = True

# read the control file
f = open(controlFile, 'rt')
lines = f.readlines()
f.close()

if not cluster:

    numParallelJobs = 1
    if (len(sys.argv) >= 4):
        numParallelJobs = int(sys.argv[3])

    numThreadsPerJob = 1
    if (len(sys.argv) == 5):
        numThreadsPerJob = int(sys.argv[4])

###################### SETUP ###############################

# the number of parameters is one less than the number of lines
parameters = len(lines) - 1
print(f'parameters = {parameters}')

vars = []
dists = []
for i in range(parameters):
    items = lines[i].split(',')
    print(items)
    vars.append(items[0])
    fmin = float(items[1])
    fmax = float(items[2])
    bounds = np.array([[fmin], [fmax]])
    print(bounds)

    # Create a distribution for each parameter
    p1 = BetaDistribution(alpha=1, beta=1, domain=bounds)

    dists.append(p1)

print(vars)

outparam = lines[parameters].rstrip()
print(outparam)

# Add all parameter distributions to this variable
p = TensorialDistribution(distributions=dists)

# TODO: set the order of the PCE
order = 4

############################ Build PCE #############################

index_set = TotalDegreeSet(dim=parameters, order=order)
pce = PolynomialChaosExpansion(distribution=p, index_set=index_set)

# first generate the sampels
pce.generate_samples()
print(pce.samples)

# we're going to time the calls to FEBio
tic = time.time()

# evaluate model output. This will call FEBio for all samples
if cluster:
    if clusterErr:
        print("Could not import febio_cluster.py. Error message: ")
        print(clusterErr)
        quit()
        
    model_output = febio_cluster.febio_output_cluster(pce.samples, febioFile, vars, outparam)
else:
    if (numParallelJobs == 1):
        model_output = febio_output(pce.samples, febioFile, vars, outparam)
    else:
        print('Calling FEBio in parallel:')
        model_output = febio_output_parallel(pce.samples, febioFile, vars, outparam, numParallelJobs, numThreadsPerJob)

# report time
toc = time.time()
    
# Calculate time it took to run suite
hours, remainder = divmod(int(toc-tic), 3600)
minutes, seconds = divmod(remainder, 60)

elapsedTime = '%s:%s:%s' % (hours, minutes, seconds)
    
print("Time elapsed:" + elapsedTime)

print(model_output)



# do the uncertainsci stuff
pce.build_pce_wafp(model_output=model_output)

################################### Statistics ##########################
mean = pce.mean()
stdev = pce.stdev()
print("Mean   = ", mean)
print("St.dev.= ", stdev)

variable_interactions = list(chain.from_iterable(combinations(range(parameters), r) for r in range(1, parameters+1)))

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
tick_labels = ['UncertainSCI\n{1:d} samples\norder {0:d}'.format(order, pce.samples.shape[0])]
tick_labels.append('Monte Carlo\n{0:1.1e} samples'.format(ensemble_size))
plt.xticks(ticks=tick_locations, labels=tick_labels)
plt.title(outparam)

# Sensitivity pie chart, averaged over all model degrees of freedom
plt.subplot(122)
average_global_SI = np.sum(global_sensitivity, axis=1)

labels = ['[' + ' '.join(str(elem) for elem in [i+1 for i in item]) + ']' for item in variable_interactions]
plt.pie(average_global_SI*100, labels=labels, autopct='%1.1f%%', startangle=90)

plt.title('Global Sensitivity')
plt.show()
