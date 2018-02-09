import os
import subprocess
from pathlib import Path

def create_environment_variables(variables):
    """Create bash env variables from dict"""
    if variables is not None:
        return "\n".join("export {}={}".format(k,v) for k,v in variables.items())

def run_command(cmd):
    try:
        return subprocess.run(cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True, timeout=60, encoding="utf-8")
    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)
        raise

def scp(source, dest):
    proc = run_command(["scp"] + source + [dest])
    print(proc.stdout)
    return proc

class Cluster:

    basepath = Path("~/nbsubmit")
    local_base_path = Path("./nbsubmit")

    def __init__(self, name, host, singularity_image, bind,
            ram_per_node_gb, cores_per_node, queue, shared_queue):
        self.name = name
        self.host = host
        self.singularity_image = singularity_image
        self.bind = bind
        self.ram_per_node_gb = ram_per_node_gb
        self.cores_per_node = cores_per_node
        self.queue = queue
        self.shared_queue = shared_queue

        print("Test connection")
        try:
            self.remote_username = self.ssh_command(["whoami"]).stdout.strip()
        except:
            print(f"SSH connection to {self.host} failed, you need to setup"
                   "either passwordless SSH or ControlMaster and login from a terminal")
            raise

    def print_available_resources(self):
        for i in range(1, 1+self.cores_per_node):
            print(i, "cores:", "{:.1f} GB RAM".format(self.ram_per_node_gb / self.cores_per_node * i))

    def put(self, filenames, job_name):
        remote_job_folder = self.basepath / job_name
        self.ssh_command(["mkdir", "-p", remote_job_folder])
        scp(filenames, f"{self.host}:{remote_job_folder}")

    def get(self, filenames, job_name):
        filenames_string = " ".join(filenames)
        local_job_folder = self.local_base_path / job_name
        scp([f"{self.host}:{self.basepath}/{job_name}/{filenames_string}"], local_job_folder)

    def ssh_command(self, cmd):
        called_process = run_command(["ssh", self.host] + cmd)
        return called_process

    def launch_job(self, job_name, notebook, environment=None, cores=1, hours=1, singularity_image=None, additional_files=[]):

        local_job_folder = self.local_base_path / job_name
        os.makedirs(local_job_folder, exist_ok=True)
        job_cmd_path = local_job_folder / "job.cmd"
        if singularity_image is None:
            singularity_image = self.singularity_image
        with open(job_cmd_path, "w") as job_file:
            job_file.write(
                self.job_template.format(notebook_filename=notebook.split("/")[-1],
                                         job_name=job_name,
                                         cores=cores,
                                         queue=self.shared_queue if cores < self.cores_per_node else self.queue,
                                         minutes=int(hours*60+1),
                                         environment=create_environment_variables(environment),
                                         singularity_image=singularity_image,
                                         bind=self.bind)
            )

        self.put([notebook, job_cmd_path] + additional_files, job_name)

        remote_job_folder = f"{self.basepath}/{job_name}"

        submit_call = self.ssh_command(["cd", remote_job_folder + ";"] + \
                          self.submit + ["job.cmd"])
        job_id = submit_call.stdout.strip().split()[-1]
        print(f"Submitted job {job_name} to {self.name}")
        with open(local_job_folder / "LAST_JOB_ID", "w") as f:
            f.write(job_id)

    def check_job(self, job_name):
        job_id_file = self.local_base_path / job_name / "LAST_JOB_ID"
        with open(job_id_file, "r") as f:
            job_id = f.read().strip()
        check_call = self.ssh_command(self.monitor + [job_id])
        return check_call.stdout.strip().split("\n")[0].strip()

    def retrieve_results(self, job_name):
        self.get("*", job_name)


class SlurmCluster(Cluster):

    job_template = \
"""#!/bin/bash
#SBATCH --job-name="nbsubmit-{job_name}"
#SBATCH --output="{job_name}.%j.out"
#SBATCH --partition={queue}
#SBATCH --nodes=1
#SBATCH --ntasks-per-node={cores}
#SBATCH --export=ALL
#SBATCH --time=00:{minutes}:00

module load singularity

NOTEBOOK_FILENAME="{notebook_filename}"
OUTPUT_FILENAME=executed_$SLURM_JOB_ID
OUTPUT_FILENAME+=_$NOTEBOOK_FILENAME

{environment}

SINGULARITY_IMAGE="{singularity_image}"
COMMAND="/opt/conda/bin/jupyter nbconvert --execute --to notebook --output $OUTPUT_FILENAME $NOTEBOOK_FILENAME"
export SINGULARITY_BINDPATH="{bind}"

singularity exec $SINGULARITY_IMAGE $COMMAND
"""
    submit = ["sbatch"]
    monitor = ["sacct", "--noheader", "--format", "State", "--jobs"]

clusters = dict(
comet = SlurmCluster(
            name = "Comet",
            host = "comet.sdsc.edu",
            singularity_image = "/oasis/scratch/comet/zonca/temp_project/ubuntu_anaconda.img",
            bind = "/oasis",
            ram_per_node_gb=128,
            cores_per_node=24,
            queue="compute",
            shared_queue="shared"
        )
)
