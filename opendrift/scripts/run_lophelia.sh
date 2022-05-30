#!/bin/bash -f
#$ -S /bin/bash
#$ -l h_rt=4:00:00
#$ -q research-el7.q
#$ -l h_vmem=10G
#$ -pe shmem-1 1
#$ -t 1-644
#$ -tc 5
#$ -N loph10-13
##$ -o $HOME/Lophelia_Skagerak/logs/OUT_$JOB_ID.$TASK_ID
##$ -e $HOME/Lophelia_Skagerak/logs/ERR_$JOB_ID.$TASK_ID
#$ -R y
##$ -m a

#year=2018  # Year/s of particle seeding
#644


module list

conda activate opendrift

cd /home/johannesro/Lophelia_Skagerak/simulation_scripts
python lophelia_SVIM_forward_run_array.py 2010 $SGE_TASK_ID
python lophelia_SVIM_forward_run_array.py 2011 $SGE_TASK_ID
python lophelia_SVIM_forward_run_array.py 2012 $SGE_TASK_ID
python lophelia_SVIM_forward_run_array.py 2013 $SGE_TASK_ID

#python lophelia_SVIM_forward_run_array.py $year $SGE_TASK_ID


