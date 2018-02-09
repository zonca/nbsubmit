# Executing a Notebook in batch mode on a Supercomputer

First create a Notebook and test it locally, for example see `job.ipynb` in this folder.

It is useful to store data, especially large files, in a folder defined in the `SCRATCH` 
environment variable that points to different folders locally and remotely.
So that the same exact notebook can run locally or remotely.

## Execution environment

The Notebook is executed in a Singularity container, so all packages should be available
on both environments

## Launch a job

Once the Notebook is ready to be executed remotely, the user can open another
Notebook to launch the job and monitor it.

Here an example session.

    from nbsubmit import cluster
    comet = cluster.get("comet")

Comet is a resource already configured, we assume that the user has already an allocation
on Comet and SSH certificates set to login without a password or use `ControlMaster` (see the `ssh_configuration` folder)
Also, for now usernames need to be the same on Comet and locally.

    comet.launch_job("job_run_1", "job.ipynb")
    Submitted job job_run_1 to Comet

This will create a SLURM job submission script, copy that and the Notebook to Comet in:

    ~/nbsubmit/job_run_1/

and launch the job from that folder using the shared queue and 1 core (~5GB RAM).

`job_run_1` is the job name, it is used to identify a job submission, the job id assigned
by SLURM is saved in a text file in the `./nbsubmit/job_run_1/` folder.

## Monitor a job

The user can monitor a job:

    comet.check_job("job_run_1")
    PENDING

or:

    comet.check_job("job_run_1")
    COMPLETED

## Retrieve results

The user can copy back the executed notebook (with embedded plots) and all the files created in the same folder:

    comet.retrieve_results("job_run_1")

The executed notebook will be available locally as `./nbsubmit/job_run_1/executed_XXXXXX_job.ipynb`, see example in this folder.
