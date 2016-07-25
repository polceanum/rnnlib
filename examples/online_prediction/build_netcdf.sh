#!/bin/bash
. env.sh
#./offline_delta.py offline_training_set.txt offline.nc 100 100
#./offline_delta.py offline_validation_set.txt offline_validation.nc 100 100 
./online_delta.py training_set.txt online.nc
./online_delta.py validation_set.txt online_validation.nc
normalise_inputs.sh -c 2 online.nc online_validation.nc
normalise_targets.sh -c 2 online.nc online_validation.nc
