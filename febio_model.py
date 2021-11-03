import subprocess
import numpy as np

# This function calls FEBio with the given values for the parameters p
def febio_function(p, febioFile, inparams, outparam):

    # prepare the parameter run file
    fp = open('run.feb', 'w')
    fp.write('<?xml version="1.0"?>\n')
    fp.write('<febio_run version="1.0">\n')
    fp.write('    <Parameters>\n')
    for i in range(p.shape[0]):
        fp.write('          <param name="');fp.write(inparams[i]);fp.write('">'); fp.write(str(p[i])); fp.write('</param>\n')
    fp.write('    </Parameters>\n')
    fp.write('    <Output>\n')
    fp.write('      <file>out.txt</file>\n')
    fp.write(f'      <param name="{outparam}"/>\n')
    fp.write('    </Output>\n')
    fp.write('</febio_run>\n')
    fp.close()

    # run febio
    print('calling febio ...', str(p))
    subprocess.run(['febio3', '-i', febioFile, '-task=param_run', 'run.feb', '-silent'])
    # read the output file
    of = open('out.txt', 'r')
    line = of.readline()

    v = np.empty([1])
    v[0] = float(line)

    print(v[0], 'done\n')

    return v

# Generate the FEBio output from the provided samples
def febio_output(samples, febioFile, inparams, outparam):
    # get sample size and dimensions
    M = samples.shape[0]

    # create empty output array
    model_output = np.empty([M, 1])
    
    for ind in range(samples.shape[0]):
        model_output[ind, :] = febio_function(samples[ind, :], febioFile, inparams, outparam)

    return model_output
