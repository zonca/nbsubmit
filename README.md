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

## Examples

See the `examples/` folder for example Notebooks and more documentation.
