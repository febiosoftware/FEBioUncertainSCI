import numpy as np
from matplotlib import pyplot as plt

from febio_model import febio_function
from UncertainSCI.distributions import BetaDistribution, TensorialDistribution
from UncertainSCI.pce import PolynomialChaosExpansion
from UncertainSCI.indexing import TotalDegreeSet

## Set up model
# Parameters for function
# TODO: you will need to modifiy the code of this function to make sure the correct
#       model parameters are used. 
f = febio_function

## Set up parameter distributions
## TODO: Create a bounds variable for each parameter
boundsE = np.array([[0.1], [2.0]])
boundsv = np.array([[0.0], [0.495]])

# TODO: Create a distribution for each parameter
p1 = BetaDistribution(alpha=1, beta=1, domain=boundsE)
p2 = BetaDistribution(alpha=1, beta=1, domain=boundsv)

# TODO: Add all parameter distributions to this variable
p = TensorialDistribution(distributions=[p1, p2])

## Build PCE's for various polynomial orders
ensemble_size = int(1e6)
orders = [3, 4]
pces = []
ensembles = []

for order in orders:
    index_set = TotalDegreeSet(dim=2, order=order)
    pce = PolynomialChaosExpansion(distribution=p, index_set=index_set)
    pce.build(model=f)
    pces.append(pce)

    # Post-processing: sample the PCE emulator
    pvals = p.MC_samples(M=ensemble_size)
    ensembles.append(pce.pce_eval(pvals))

## Compute MC statistics (for comparison)
#pvals = p.MC_samples(M=ensemble_size)
#oracle_ensemble = np.zeros(ensemble_size)
#for i in range(ensemble_size):
#    oracle_ensemble[i] = f(pvals[i,:])
#ensembles.append(oracle_ensemble)

# Box plots require 1D arrays as input
for i in range(len(ensembles)):
    ensembles[i] = ensembles[i].flatten()

## Construct boxplots
plt.figure()
plt.boxplot(ensembles)
tick_locations = [1 + i for i in range(len(ensembles))]
tick_labels = ['UncertainSCI\n{1:d} samples\norder {0:d}'.format(orders[i], pces[i].samples.shape[0]) for i in range(len(pces))]
tick_labels.append('Monte Carlo\n{0:1.1e} samples'.format(ensemble_size))
plt.xticks(ticks=tick_locations, labels=tick_labels)
plt.title('FEBio model boxplots')
plt.show()
