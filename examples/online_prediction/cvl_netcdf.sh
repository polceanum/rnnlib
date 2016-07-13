#!/bin/bash
. env.sh
./cvl_offline_delta.py /Users/zimi/Documents/git/ma/data/cvl-database-1-1/trainset/words cvl_validate.nc 100
./cvl_offline_delta.py /Users/zimi/Documents/git/ma/data/cvl-database-1-1/testset/words cvl.nc 100
#./online_delta.py training_set.txt online.nc
#./online_delta.py validation_set.txt online_validation.nc
#normalise_inputs.sh -c 2 online.nc online_validation.nc
#normalise_targets.sh -c 2 online.nc online_validation.nc
