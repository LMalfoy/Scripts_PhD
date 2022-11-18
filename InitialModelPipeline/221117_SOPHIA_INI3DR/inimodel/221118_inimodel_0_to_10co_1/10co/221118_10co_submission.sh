#!/bin/bash -l
#SBATCH -D /Users/sophiawraage/PycharmProjects/Master/InitialModelPipeline/221117_SOPHIA_INI3DR/inimodel/221118_inimodel_0_to_10co_1/10co/
#SBATCH -J inimodel
#SBATCH -C scratch
#SBATCH --partition=medium
#SBATCH --error=/Users/sophiawraage/PycharmProjects/Master/InitialModelPipeline/221117_SOPHIA_INI3DR/inimodel/221118_inimodel_0_to_10co_1/10co/inimodel_10co.err
#SBATCH --output=/Users/sophiawraage/PycharmProjects/Master/InitialModelPipeline/221117_SOPHIA_INI3DR/inimodel/221118_inimodel_0_to_10co_1/10co/inimodel_10co.out
#SBATCH --ntasks=24
#SBATCH -t 02:00:00
#SBATCH --qos=short
module purge
shopt -s expand_aliases
source /usr/users/rubsak/sw/rubsak.bashrc
use_relion4
# load relion/4.0.0
echo - e "$(hostname) modules: $(module list 2>&1 | grep relion --color=never)"
relion_helix_inimodel2d \
--i file.star \
--o 10co_initial_model \
--angpix 1.9 \
--iter 10 \
--mask_diameter 200 \
--search_shift 3 \
--search_angle 1 \
--step_angle 1 \
--sym 2 \
--maxres 5 \
--j 24 
