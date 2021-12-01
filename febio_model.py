import subprocess, time, platform
import numpy as np

def createRunFile(runFileName, outFileName, p, inparams, outparam):
    fp = open(runFileName, 'w')
    fp.write('<?xml version="1.0"?>\n')
    fp.write('<febio_run version="1.0">\n')
    fp.write('    <Parameters>\n')
    for i in range(p.shape[0]):
        fp.write('          <param name="');fp.write(inparams[i]);fp.write('">'); fp.write(str(p[i])); fp.write('</param>\n')
    fp.write('    </Parameters>\n')
    fp.write('    <Output>\n')
    fp.write('      <file>');fp.write(outFileName);fp.write('</file>\n')
    fp.write(f'      <param name="{outparam}"/>\n')
    fp.write('    </Output>\n')
    fp.write('</febio_run>\n')
    fp.close()

# process output file and return output value
def get_febio_output(outFileName):
    of = open(outFileName, 'r')
    line = of.readline()
    v = np.empty([1])
    v[0] = float(line)
    return v

# This function calls FEBio with the given values for the parameters p
def febio_function(p, febioFile, runFileName, outFileName, inparams, outparam):

    # prepare the parameter run file
    createRunFile(runFileName, outFileName, p, inparams, outparam)

    # run febio
    print('calling febio ...', str(p))
    subprocess.run(['febio3', '-i', febioFile, '-task=param_run', runFileName, '-silent'])

    # read the output file
    v = get_febio_output(outFileName)
    print(v[0], 'done\n')

    return v

# write model output to a file
def write_model_output(model_output, fileName):
    M = model_output.shape[0]
    fp = open('pceresults.txt', 'w')
    for ind in range(M):
        fp.write(str(model_output[ind, 0])); fp.write('\n')
    fp.close()

# Generate the FEBio output from the provided samples
def febio_output(samples, febioFile, inparams, outparam):
    # get sample size and dimensions
    M = samples.shape[0]

    # create empty output array
    model_output = np.empty([M, 1])
    
    for ind in range(M):
        model_output[ind, :] = febio_function(samples[ind, :], febioFile, 'run.feb', 'out.txt', inparams, outparam)

    # store all results to a file
    write_model_output(model_output, 'pceresults.txt')

    return model_output

# read the FEBio model output
def read_model_output(outFilename):
    of = open(outFilename, 'r')
    lines = of.readlines()
    v = np.empty([len(lines), 1])
    i = 0
    for line in lines:
        v[i, 0] = float(line)
        i += 1
    return v

# Calls FEBio in parallel. 
def febio_output_parallel(samples, febioFile, inparams, outparam, numParallelJobs, numThreadsPerJob):
    
    # get sample size
    totalJobs = samples.shape[0]

    # create empty output array
    model_output = np.empty([totalJobs, 1])
    
    # find febio3 full path for use in Popen
    febio3 = "febio3"
    if platform.system() != "Windows":
        out = subprocess.run(['which', 'febio3'], capture_output=True)
        febio3 = out.stdout.decode('utf8').strip()

    # This will store the processes
    jobs = {}

    # start all jobs
    current = 0
    while True:
        while (current < totalJobs) and (len(jobs) < numParallelJobs):

            currentString = str(current)
            runFileName = 'run' + currentString + '.feb'
            outFileName = 'out' + currentString + '.txt'

            # create the run file
            createRunFile(runFileName, outFileName, samples[current, :], inparams, outparam)

            # start FEBio
            command = [febio3, '-i', febioFile, '-task=param_run', runFileName, '-silent']
            jobs[currentString] = subprocess.Popen(command, env={"OMP_NUM_THREADS": str(numThreadsPerJob)}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            current += 1

        # if there are no more jobs running, we're done
        if (len(jobs) == 0):
            break

        # find all finished jobs
        finished = []
        for jobId in jobs:
            if jobs[jobId].poll() != None:
                finished.append(jobId)
        
        # process all finished jobs
        for jobId in finished:
            outFileName = 'out' + jobId + '.txt'
            v = get_febio_output(outFileName)

            id = int(jobId)
            model_output[id, :] = v

            print(jobId, 'done')

            # cleanup
            del jobs[jobId]

        # take a little nap
        time.sleep(0.001)

    # write model output to file
    write_model_output(model_output, 'pceresults.txt')

    # All done, so return 
    return model_output

