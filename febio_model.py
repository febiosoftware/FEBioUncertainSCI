import subprocess
import numpy as np

# This function calls FEBio with the given values for the parameters p
def febio_function(p):

    # TODO: Set this to the FEBio input model file name
    febioFile = 'Model1.feb'

    # prepare the parameter run file
    # TODO: Update this code so that the correct model input and output parameters are used
    #       The number of input parameters defined here must match the number of parameters
    #       defined in the febio_uncertainSCI file. 
    fp = open('run.feb', 'w')
    fp.write('<?xml version="1.0"?>\n')
    fp.write('<febio_run version="1.0">\n')
    fp.write('    <Parameters>\n')
    fp.write('          <param name="fem.material[0].E">'); fp.write(str(p[0])); fp.write('</param>\n')
    fp.write('          <param name="fem.material[0].v">'); fp.write(str(p[1])); fp.write('</param>\n')
    fp.write('    </Parameters>\n')
    fp.write('    <Output>\n')
    fp.write('      <file>out.txt</file>\n')
    fp.write('      <param name="fem.rigidbody(\'rigid\').Fx"/>\n')
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
