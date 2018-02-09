# Mount the Supercomputer filesystem locally

It is possible to mount the scratch filesystem of a Supercomputer locally,
this avoids the transfer of the results back.

It requires the user to call for example `comet.mount()`, then the scratch
filesystem is mounted via `sshfs` to `~/comet` locally.

`nbsubmit` works normally to submit and monitor jobs. Once the job is completed,
the user can access the results on `~/comet/nbsubmit/job_name`.

