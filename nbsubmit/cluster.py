import os
import subprocess
from pathlib import Path


def create_environment_variables(variables):
    """Create bash env variables from dict"""
    if variables is None:
        return ""
    else:
        return "\n".join("export {}={}".format(k, v) for k, v in variables.items())


def run_command(cmd):
    try:
        return subprocess.run(
            map(str, cmd),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True,
            timeout=60,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)
        raise


def scp(source, dest):
    proc = run_command(["scp"] + source + [dest])
    print(proc.stdout)
    return proc


class Cluster:

    local_base_path = Path("./nbsubmit")

    def __init__(
        self,
        name,
        host,
        singularity_image,
        bind,
        ram_per_node_gb,
        cores_per_node,
        queue,
        shared_queue,
        remote_filesystem_path,
    ):
        self.name = name
        assert " " not in self.name, "A cluster name should not contain spaces"
        self.host = host
        self.singularity_image = singularity_image
        self.bind = bind
        self.ram_per_node_gb = ram_per_node_gb
        self.cores_per_node = cores_per_node
        self.queue = queue
        self.shared_queue = shared_queue

        print("Test connection to {}".format(self.host))
        try:
            self.remote_username = self.ssh_command(["whoami"]).stdout.strip()
        except:
            print(
                "SSH connection to {} failed, you need to setup".format(self.host)
                + " either passwordless SSH or ControlMaster and login from a terminal"
            )
            raise
        print("Connection successful")

        # mount-related options
        self.remote_filesystem_path = Path(
            remote_filesystem_path.format(username=self.remote_username)
        )
        self.local_mount_point = Path.home() / self.name

    def print_available_resources(self):
        for i in range(1, 1 + self.cores_per_node):
            print(
                i,
                "core{}:".format("s" if i > 1 else ""),
                "{:.1f} GB RAM".format(self.ram_per_node_gb / self.cores_per_node * i),
            )

    def mount(self):
        if self.is_mounted():
            print(
                "Remote filesystem already mounted to {}".format(self.local_mount_point)
            )
        else:
            os.makedirs(self.local_mount_point, exist_ok=True)
            run_command(
                [
                    "sshfs",
                    "-o",
                    "reconnect",
                    "{}:{}".format(self.host, self.remote_filesystem_path),
                    self.local_mount_point,
                ]
            )
            print(
                "Mounted {}:{} to {}".format(
                    self.host, self.remote_filesystem_path, self.local_mount_point
                )
            )

    def is_mounted(self):
        return (
            str(Path.home()) in run_command(["mount", "-l", "-t", "fuse.sshfs"]).stdout
        )

    def unmount(self):
        if self.is_mounted():
            run_command(["fusermount", "-u", self.local_mount_point])
            print("Unmounted {}".format(self.local_mount_point))

    def remote_job_folder(self, job_name):
        return self.remote_filesystem_path / "nbsubmit" / job_name

    def put(self, filenames, job_name):
        remote_job_folder = self.remote_job_folder(job_name)
        self.ssh_command(["mkdir", "-p", remote_job_folder])
        scp(filenames, "{}:{}".format(self.host, remote_job_folder))

    def get(self, filenames, job_name):
        filenames_string = " ".join(filenames)
        local_job_folder = str(self.local_base_path / job_name)
        remote_job_folder = self.remote_job_folder(job_name)
        scp(
            ["{}:{}/{}".format(self.host, remote_job_folder, filenames_string)],
            local_job_folder,
        )

    def ssh_command(self, cmd):
        called_process = run_command(["ssh", self.host] + cmd)
        return called_process

    def launch_job(
        self,
        job_name,
        notebook,
        environment=None,
        cores=1,
        hours=1,
        singularity_image=None,
        additional_files=[],
    ):

        local_job_folder = self.local_base_path / job_name
        os.makedirs(local_job_folder, exist_ok=True)
        job_cmd_path = local_job_folder / "job.cmd"
        if singularity_image is None:
            singularity_image = self.singularity_image
        with open(job_cmd_path, "w") as job_file:
            job_file.write(
                self.job_template.format(
                    notebook_filename=notebook.split("/")[-1],
                    job_name=job_name,
                    cores=cores,
                    queue=self.shared_queue
                    if cores < self.cores_per_node
                    else self.queue,
                    minutes=int(hours * 60 + 1),
                    environment=create_environment_variables(environment),
                    singularity_image=singularity_image,
                    bind=self.bind,
                )
            )

        self.put([notebook, job_cmd_path] + additional_files, job_name)

        remote_job_folder = self.remote_job_folder(job_name)

        submit_call = self.ssh_command(
            ["cd", "{};".format(remote_job_folder)] + self.submit + ["job.cmd"]
        )
        job_id = submit_call.stdout.strip().split()[-1]
        print("Submitted job {} to {}".format(job_name, self.name))
        with open(local_job_folder / "LAST_JOB_ID", "w") as f:
            f.write(job_id)

    def get_job_id(self, job_name):
        job_id_file = self.local_base_path / job_name / "LAST_JOB_ID"
        with open(job_id_file, "r") as f:
            return f.read().strip()

    def check_job(self, job_name):
        job_id = self.get_job_id(job_name)
        check_call = self.ssh_command(self.monitor + [job_id])
        return check_call.stdout.strip().split("\n")[0].strip()

    def cancel_job(self, job_name):
        job_id = self.get_job_id(job_name)
        check_call = self.ssh_command(self.cancel + [job_id])
        self.check_job(job_name)

    def retrieve_results(self, job_name):
        if self.is_mounted():
            print(
                "No need to retrieve results "
                + "You can access the files locally in the {}/nbsubmit folder".format(
                    self.local_mount_point
                )
            )
        else:
            self.get("*", job_name)


class SlurmCluster(Cluster):

    job_template = """#!/bin/bash
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
    cancel = ["scancel"]


def get(cluster_name):
    if cluster_name == "comet":
        return SlurmCluster(
            name="comet",
            host="comet.sdsc.edu",
            singularity_image="/oasis/scratch/comet/zonca/temp_project/ubuntu_anaconda.img",
            bind="/oasis",
            ram_per_node_gb=128,
            cores_per_node=24,
            queue="compute",
            shared_queue="shared",
            remote_filesystem_path="/oasis/scratch/comet/{username}/temp_project",
        )
