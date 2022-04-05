#!/usr/bin/env python

# Simulates the dispersal of Lophelia pertusa larvae using current velocity data from SVIM archive on thredds server.

#----------- Import modules and readers ----------

import numpy as np
import os
import sys
from datetime import datetime, timedelta, date
from opendrift.readers import reader_ROMS_native
from opendrift.readers import reader_ROMS_SVIMforcing
from opendrift.models.lophelia import LopheliaLarvaeDrift # Lophelia dispersal model (based on the PelagicEgg model)

#--------- Set parameters for simulation ---------

# From bash:
# Set start date and time of spawning/seeding:
ys = int(sys.argv[1])    # Year
ms = int(sys.argv[2])    # Month
ds = int(sys.argv[3])    # Day
hs = int(sys.argv[4])    # Hour
mms = int(sys.argv[5])   # Minute

# Set location for seeding:
lats = float(sys.argv[6])   # Latitude [deg N]
lons = float(sys.argv[7])   # Longitude [deg E]
radis = int(sys.argv[8])  # Radius [m]
zs = int(sys.argv[9])     # Depth [m]

# Set number of seeding particles at each depth:
ns = int(sys.argv[10])

# Length of simulation [days]:
tsim = int(sys.argv[11])

# Specify within script:
# Length [s] of simulation timestep:
tstep = 3600

# Length [s] of output timestep:
tstep_out = 24*3600

#-------Read model data and run simulation -------
datestr_out = str(date(ys, ms, ds))
log_fname = '/home/vilhelm/Data/OpenDrift/Logs/lophelia_SVIM_seedingBeryl_r'+str(radis)+'_n'+str(ns)+'_t'+str(tsim)+'_'+datestr_out+'.log'
o = LopheliaLarvaeDrift(loglevel=0, logfile=log_fname)

# Reader for SVIM model data (thredds server):
reader_SVIM_daily_agg = reader_ROMS_native.Reader('https://thredds.met.no/thredds/dodsC/nansen-legacy-ocean/svim_daily_agg')

# Reader for SVIM MLD data (thredds server):
reader_SVIM_MLD = reader_ROMS_native.Reader('https://thredds.met.no/thredds/dodsC/nansen-legacy-ocean/svim_daily_mld_agg')

# Reader for atmospheric forcing file (local):
reades_atm_forc  = reader_ROMS_SVIMforcing.Reader('/home/vilhelm/Data/SVIM/forcing/yearly_files/ocean_force_'+str(ys)+'.nc')

# Add data readers:
o.add_reader([reader_SVIM_daily_agg, reader_SVIM_MLD, reades_atm_forc])

# Seed lophelia larvae at defined time:
t1 = datetime(ys, ms, ds, hs, mms)      # Time of first seeding

# Seed elements:
#o.seed_elements(1.3, 58.7, z='seafloor', radius=50, number=100, time=t1, diameter=0.0002) # Brae oil field
o.seed_elements(lons, lats, z=-zs, radius=radis, radius_type='uniform', number=ns, time=t1, diameter=0.0002) # Beryl oil field

# Adjusting configuration for turbulent mixing:
o.set_config('drift:vertical_mixing', True)
o.set_config('vertical_mixing:diffusivitymodel', 'windspeed_Large1994') # windspeed parameterization for eddy diffusivity
o.set_config('drift:vertical_advection', False)

# Use ocean model landmask instead of GSHHS:
o.set_config('general:use_auto_landmask', False)

# Vertical resolution and time step should be adjusted so to avoid getting
# output warnings like 'DEBUG: WARNING! some elements have p+q>1.'
o.set_config('vertical_mixing:timestep', 60.) # seconds

# Output file name:
outname = '/home/vilhelm/Data/OpenDrift/Output/seedingBeryl_tempdepdev1_tempdepws1_r'+str(radis)+'_n'+str(ns)+'_t'+str(tsim)+'_'+datestr_out+'.nc'

# Run model:
o.run(duration=timedelta(days=tsim), time_step=tstep, time_step_output=tstep_out, outfile=outname)

# Print and plot results:
print(o)

o.plot()
o.animation()
o.plot_vertical_distribution()
