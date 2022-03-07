#!/usr/bin/env python

# Simulates the dispersal of Lophelia pertusa larvae using current velocity data from SVIM archive on thredds server.

#----------- Import modules and readers ----------

import numpy as np
import os
from datetime import datetime, timedelta
from opendrift.readers import reader_ROMS_native
from opendrift.readers import reader_ROMS_native_edit_MLD_01
from opendrift.readers import reader_ROMS_SVIMforcing
from opendrift.models.lophelia import LopheliaLarvaeDrift # Lophelia dispersal model (based on the PelagicEgg model)

#--------- Set parameters for simulation ---------

# Set start date and time of spawning/seeding:
ys = 2012 # Year
ms = 2    # Month
ds = 1    # Day
hs = 12   # Hour
mms = 0   # Minute

tspwn = 15  # Duration [days] of spawning

# Length [days] of simulation:
tsim = 20

# Length [s] of simulation timestep:
tstep = 3600

# Length [s] of output timestep:
tstep_out = 3*3600

#-------Read model data and run simulation -------
o = LopheliaLarvaeDrift(loglevel=0, logfile="test_lophelia_SVIM_MLD_07.log")

# Reader for SVIM model data (thredds server):
reader_SVIM_daily_agg = reader_ROMS_native.Reader('https://thredds.met.no/thredds/dodsC/nansen-legacy-ocean/svim_daily_agg')

# Reader for SVIM MLD data (local):
#reader_SVIM_MLD = reader_ROMS_native_edit_MLD_01.Reader('/media/vilhelm/LaCie/Data/SVIM_MLD/2012/MLD_avg_20120201.nc4')
reader_SVIM_MLD = reader_ROMS_native_edit_MLD_01.Reader('/media/vilhelm/LaCie/Data/SVIM_MLD/2012/filemerge/MLD_avg_20120201.nc4')

# Reader for atmospheric forcing file (local):
reades_atm_forc  = reader_ROMS_SVIMforcing.Reader('/media/vilhelm/LaCie/Data/SVIM_forcing/yearly_files/ocean_force_2012.nc')

# Add data readers:
o.add_reader([reader_SVIM_daily_agg, reader_SVIM_MLD, reades_atm_forc])

# Seed lophelia larvae at defined time:
t1 = datetime(ys, ms, ds, hs, mms)      # Time of first seeding

# Seed elements:
#o.seed_elements(1.3, 58.7, z='seafloor', radius=50, number=100, time=t1, diameter=0.0002) # Brae oil field
o.seed_elements(1.51667, 59.61667, z='seafloor', radius=50, number=100, time=t1, diameter=0.0002) # Beryl oil field

# Adjusting configuration for turbulent mixing:
o.set_config('drift:vertical_mixing', True)
o.set_config('vertical_mixing:diffusivitymodel', 'windspeed_Large1994') # windspeed parameterization for eddy diffusivity
o.set_config('drift:vertical_advection', False)

# Vertical resolution and time step should be adjusted so to avoid getting
# output warnings like 'DEBUG: WARNING! some elements have p+q>1.'
o.set_config('vertical_mixing:timestep', 60.) # seconds

# Output file name:
outname = 'seedingBeryl_tempdepdev1_tempdepws1_MLD_SVIM_20d_20120201_test07.nc'

# Run model:
o.run(duration=timedelta(days=tsim), time_step=tstep, time_step_output=tstep, outfile=outname)

# Print and plot results:
print(o)

o.plot()
o.animation()
o.plot_vertical_distribution()
