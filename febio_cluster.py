import os, time, febio_model, getpass, json
import numpy as np
from paramiko import SSHClient, SFTPClient, Transport, AutoAddPolicy
from cluster_settings import *

class JobFile:
    
    def __init__(self, febFile, localID):
        self.localID = int(localID)
        workingDir = os.path.dirname(febFile)
        # if this isn't empy, add an ending slash
        if workingDir:
            workingDir += "/"
        
        febName = os.path.basename(febFile)
        self.runFile = "run" + localID + ".feb"
        outFile = "out" + localID + ".txt"
        scriptFile = "script" + localID + ".sh"
        
        self.localFeb = workingDir + febName
        self.localRunFile = workingDir + self.runFile
        self.localOutFile = workingDir + outFile
        self.localScript = workingDir + scriptFile
        
        self.remoteFeb = REMOTEDIR + febName
        self.remoteRunFile = REMOTEDIR + self.runFile
        self.remoteOutFile = REMOTEDIR + outFile
        self.remoteScript = REMOTEDIR + scriptFile
        
        self.jobID = 0
        self.status = "PD"
        
        
    def makeBatchScript(self):
        with open(self.localScript, "w", newline='\n') as f:
            script = SCRIPT
            script += REMOTEFEBIO + " -i " + self.remoteFeb + " -task=param_run " + self.remoteRunFile + " -silent"
            
            f.write(script)
            
    def update(self, ssh, sftp):
        self.checkStatus(ssh)
        
        if self.status == "R":
            return False
        elif self.status == "PD":
            return False
        elif self.status == "CF":
            return False
        else:
            self.getFiles(sftp)
            
            return True
            
    def putFiles(self, sftp):
        sftp.put(self.localRunFile, self.remoteRunFile)
        sftp.put(self.localScript, self.remoteScript)
        
    def getFiles(self, sftp):
        try:
            sftp.get(self.remoteOutFile, self.localOutFile)
        except:
            print("Remote file " + self.remoteOutFile + " does not exist")
            quit()
        
    def cleanFiles(self, ssh):
        ssh.exec_command("rm " + self.remoteOutFile + " " + self.remoteScript + " " + self.remoteRunFile)
        os.remove(self.localRunFile)
        os.remove(self.localScript)
        
    def queueJob(self, ssh):
        command = SBATCH + " -o /dev/null -e /dev/null " + self.remoteScript
        
        stdin, stdout, stderr = ssh.exec_command("cd " + REMOTEDIR + "; " + command)
        
        out = stdout.read().decode("utf8")
        err = stderr.read().decode("utf8")
        
        if "Submitted batch job " in out:
            self.jobID = int(out.replace("Submitted batch job ", ""))
            print(self.runFile + " succesfully submitted. Job ID: " + str(self.jobID))
        else:
            print("Failed to submit " + self.runFile + ". STDERR: " + err)
    
    def checkStatus(self, ssh):
        command = SQUEUE + ' -h -o "%t" -j ' + str(self.jobID)
        
        stdin, stdout, stderr = ssh.exec_command(command)
        
        self.status = stdout.read().decode("utf8").strip()
        
def missingVar(var):
    print("Please set the " + var + " variable in cluster_settings.py")

def startClient():
    ssh = SSHClient()
    
    password = getpass.getpass()
    
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(HOSTNAME, username=USERNAME, password=password)
    
    sftp = ssh.open_sftp()
    
    return ssh, sftp

def queueJobs(samples, febioFile, inparams, outparams, ssh = None, sftp = None):
    closeSSH = False
    if ssh is None:
        ssh, sftp = startClient()
        closeSSH = True
        
    # convert to absolute path
    febioFile = os.path.abspath(febioFile)
    
    sftp.put(febioFile, REMOTEDIR + os.path.basename(febioFile))
    
    # get sample size
    totalJobs = samples.shape[0]
    
    # This will store the processes
    jobs = {}
    # start all jobs
    current = 0
    while (current < totalJobs):
        currentString = str(current)
        
        jobs[current] = JobFile(febioFile, currentString)
        jobs[current].makeBatchScript()
        
        febio_model.createRunFile(jobs[current].localRunFile, jobs[current].remoteOutFile, samples[current, :], inparams, outparams)
        
        current += 1
    
    # Build info dictionary to write info to json file
    info = {}
    info["REMOTEDIR"] = REMOTEDIR
    info["JOBS"] = []
    
    for key in jobs:
        jobs[key].putFiles(sftp)
        jobs[key].queueJob(ssh)
        
        jobInfo = {}
        jobInfo["ID"] = jobs[key].localID
        jobInfo["remoteID"] = jobs[key].jobID
        info["JOBS"].append(jobInfo)
        
    infoFile = os.path.splitext(os.path.basename(febioFile))[0] + ".info"
    with open(infoFile, "w") as f:
        f.write(json.dumps(info))
    
    
    if closeSSH:
        sftp.close()
        ssh.close()
    
    return jobs

def get_cluster_output(samples, febioFile, inparams, outparams):
    infoFile = os.path.splitext(os.path.basename(febioFile))[0] + ".info"
    
    jobInfo = {}
    with open(infoFile, "r") as f:
        jobInfo = json.load(f)    
    
    # Overwrite the REMOTEDIR variable defined in cluster_settings.py
    # with the one stored when the model was started.
    global REMOTEDIR
    REMOTEDIR = jobInfo["REMOTEDIR"]
    
    jobs = {}
    for job in jobInfo["JOBS"]:
        jobID = job["ID"]
            
        jobs[jobID] = JobFile(febioFile, str(jobID))
    
    ssh, sftp = startClient()
    
    model_output = np.empty([len(outparams), samples.shape[0], 1])
    
    for jobID in jobs:
        jobs[jobID].getFiles(sftp)
        
        v = febio_model.get_febio_output(jobs[jobID].localOutFile)

        for i in range(len(outparams)):
            model_output[i, jobID, :] = v[i]

        print(jobID, 'read')

    # only cleanup after everything is read properly. 
    for jobID in jobs:
        jobs[jobID].cleanFiles(ssh)
    
    
    sftp.close()
    ssh.close()
    
    # All done, so return 
    return model_output
    

def febio_output_cluster(samples, febioFile, inparams, outparams):
    
    missing = False
    if HOSTNAME == "":
        missingVar("HOSTNAME")
        missing = True
        
    if USERNAME == "":
        missingVar("USERNAME")
        missing = True
        
    if REMOTEDIR == "":
        missingVar("REMOTEDIR")
        missing = True
        
    if REMOTEFEBIO == "":
        missingVar("REMOTEFEBIO")
        missing = True
        
    if missing:
        quit()

    ssh, sftp = startClient()    
    
    # This will store the processes
    jobs = queueJobs(samples, febioFile, inparams, outparams, ssh, sftp)
    
    # create empty output array
    model_output = np.empty([len(outparams), samples.shape[0], 1])
    
    while True:
        finished = []
        for jobID in jobs:
            if jobs[jobID].update(ssh, sftp):
                finished.append(jobID)
            
            
        # process all finished jobs
        for jobID in finished:
            v = febio_model.get_febio_output(jobs[jobID].localOutFile)

            for i in range(len(outparams)):
                model_output[i, jobID, :] = v[i]

            print(jobID, 'done')

            # cleanup
            jobs[jobID].cleanFiles(ssh)
            del jobs[jobID]
            
        # if there are no more jobs running, we're done
        if (len(jobs) == 0):
            break
            
        time.sleep(1)

    
    sftp.close()
    ssh.close()
    
    # All done, so return 
    return model_output
