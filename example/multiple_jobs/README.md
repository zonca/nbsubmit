# Submit multiple jobs

## Parametrize Notebooks

Notebooks don't take input arguments, but can access environment variables via `os.environ`.

## Launch multiple jobs

Once a Notebook is ready and accepts one or multiple inputs as environment variables, it is
possible to submit multiple jobs with `nbsubmit` and modify each time the environment
variables with the `environment` dictionary argument to `launch_job`.

## Example

See how `submit_multiple_jobs.ipynb` Notebook submits 10 times `job.ipynb` on different
input data files.
Check also all the outputs in the `nbsubmit` subfolder.
