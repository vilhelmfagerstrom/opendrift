#!/bin/bash -f
#$ -S /bin/bash
#$ -l h_rt=10:00:00
#$ -q research-el7.q
#$ -l h_vmem=30G
#$ -pe shmem-1 1
#$ -M johannesro@met.no
#$ -t 6-644
#$ -tc 5
#$ -N loph
##$ -o $HOME/Lophelia_Skagerak/logs/OUT_$JOB_ID.$TASK_ID
##$ -e $HOME/Lophelia_Skagerak/logs/ERR_$JOB_ID.$TASK_ID
#$ -R y
#$ -m a

year=2010  # Year/s of particle seeding
#644


module list

conda activate opendrift

cd /home/johannesro/Lophelia_Skagerak/simulation_scripts
python lophelia_SVIM_forward_run_array.py $year $SGE_TASK_ID
