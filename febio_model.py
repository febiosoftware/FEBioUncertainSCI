import subprocess
import numpy as np

# This function calls FEBio with the given values for the parameters p
def febio_function(p):

    # prepare the parameter run file
    fp = open('pyrun.feb', 'w')
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
    subprocess.run(['febio3', '-i', 'Model1.feb', '-task=param_run', 'pyrun.feb', '-silent'])
    # read the output file
    of = open('out.txt', 'r')
    line = of.readline()

    v = np.empty([1])
    v[0] = float(line)

    print(v[0], 'done\n')

    return v
