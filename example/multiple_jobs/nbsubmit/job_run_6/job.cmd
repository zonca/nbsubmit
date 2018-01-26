#!/bin/bash
#SBATCH --job-name="nbsubmit-job_run_6"
#SBATCH --output="job_run_6.%j.out"
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --export=ALL
#SBATCH --time=00:61:00

module load singularity

NOTEBOOK_FILENAME="job.ipynb"
OUTPUT_FILENAME=executed_$SLURM_JOB_ID
OUTPUT_FILENAME+=_$NOTEBOOK_FILENAME

export INPUTFILE=input_data_6.h5

SINGULARITY_IMAGE="/oasis/scratch/comet/zonca/temp_project/ubuntu_anaconda.img"
COMMAND="/opt/conda/bin/jupyter nbconvert --execute --to notebook --output $OUTPUT_FILENAME $NOTEBOOK_FILENAME"
export SINGULARITY_BINDPATH="/oasis"

singularity exec $SINGULARITY_IMAGE $COMMAND
