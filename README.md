Submit Jupyter Notebooks for remote execution
=============================================

This Python package provides a simplified interface for running a Jupyter Notebook
non-interactively on a remote machine.
It currently supports Supercomputers running SLURM, in the future I'd like to add
also HTCondor support, possibly interfacing with OpenScienceGrid.

## Use case

The idea is that you develop and test on a small dataset your custom analysis Jupyter Notebook locally.
Once the Jupyter Notebook is finalized, you would like to run it on a large dataset or on a
large amount of medium-sized dataset.
You need access to a large amount of memory and disk, therefore you would like to
use a Supercomputer you already have access to. For example Comet at the San Diego Supercomputer Center.

## Installation

Install from pypi:

    pip install nbsubmit

## How it works

This package takes care of copying the Notebook to the Supercomputer, prepare a SLURM
job and submit it to the scheduler.
Once the job starts, the Jupyter Notebook is executed non-interactively with `jupyter nbconvert` inside
a Singularity Container.
You can monitor its execution without ever leaving the Notebook on your local machine.
Once the job completes, `nbsubmit` allows you to copy back the executed Notebook (with plots included)
and any output that was produced in the same folder.

## Large data files

If you are processing files larger than ~100GB, it is better to transfer them first to the Supercomputer
with Globus Online to your SCRATCH space (e.g. on Comet it is `/oasis/scratch/comet/$USER/temp_project/`),
and then point the Notebook to that folder.

Same for the output files, you can save and automatically retrieve small files located in the same folder
as the Notebook. Save instead large files on your SCRATCH space and copy them with Globus Online.

## Mount a remote filesystem

It can be convenient to mount the filesystem locally so that we do not need to copy the results of our computation
back to the local machine.

`nbsubmit` provides some convenience functions to simplify this. However it is necessary to first setup a
multiplexed SSH connection, so that you can interactively start a SSH connection and authenticate just once,
for example this is feasible also when the Supercomputer requires 2 factor authentication.

In order to configure this, you need to copy into your `.ssh/config` the configuration available in `ssh_configuration/config`.

Then before using `nbsubmit`, open a terminal on your local machine and access the target Supercomputer via SSH
and leave that terminal open.

Then we can mount the filesystem locally with:

```
> from nbsubmit import cluster
> comet = cluster.get("comet")
> comet.mount()
Mounted comet.sdsc.edu:/oasis/scratch/comet/zonca/temp_project to /home/zonca/comet
> !df -h | tail -1
comet.sdsc.edu:/oasis/scratch/comet/zonca/temp_project  2.5P  2.3P  240T  91% /home/zonca/comet
```

See `example/mounted_filesystem` for a complete example.

## Examples

See the `examples/` folder for example Notebooks and more documentation.
