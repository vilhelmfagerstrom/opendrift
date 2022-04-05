#!/bin/bash

#----------------- Input ------------------
# Dates for seeding:

ys=2012             # Year/s of particle seeding
ms=2                # Month/s of particle seeding
ds=($(seq 1 1 2))  # Day/s of particle seeding
hs=12               # Hour of particle seeding
mms=0               # Minute of particle seeding

# Horizontal location for seeding:
lats=59.545686
lons=1.537903

# Radius of seeding area [m] (uniform seeding within circular area):
radis=4000

# Depth for seeding:
zs=95

# Number of seeding particles at each depth:
ns=1000

# Length of simulation [days]:
tsim=300

#--------- Loop over seeding days ---------

#for loop to run script
for a in "${ds[@]}"
do
  python lophelia_SVIM_forward_run.py $ys $ms "$a" $hs $mms $lats $lons $radis $zs $ns $tsim
  echo "Simulation for seeding on day $a done"
done
