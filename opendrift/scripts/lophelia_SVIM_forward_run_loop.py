#!/usr/bin/env python

# Simulates the dispersal of Lophelia pertusa larvae using current velocity data from SVIM archive on thredds server.

#----------- Import modules and readers ----------

import numpy as np
import os
import sys
import shutil
from datetime import datetime, timedelta, date
from opendrift.readers import reader_ROMS_native
from opendrift.readers import reader_ROMS_SVIMforcing
from opendrift.models.lophelia import LopheliaLarvaeDrift # Lophelia dispersal model (based on the PelagicEgg model)

#--------- Set parameters for simulation ---------

# Set start date and time of spawning/seeding:
ys = 2012   # Start year
ye = 2013   # End year
ms = 1      # Start month
me = 2      # End month
ds = 1      # Start day
de = 2      # End day
hs = 12     # Hour
mms = 0     # Minute

# Radius of seeding area [m] (uniform seeding within circular area):
radis = 4000

# Depth for seeding:
zs = 'seafloor'

# Number of seeding particles at each depth:
ns = 1000

# Length of simulation [days]:
tsim = 3

# Length [s] of simulation timestep:
tstep = 3600

# Length [s] of output timestep:
tstep_out = 24*3600

#-------------- Seeding locations ----------------

lcs = {1: (1.683611111,60.80927778),
        2: (1.74345,60.81011667),
        3: (1.735242,60.810117),
        4: (1.462389,60.960639),
        5: (1.804167,61.519444)}

#----------------- File paths --------------------

# SVIM ocean model data:
pth_in_SVIM = 'https://thredds.met.no/thredds/dodsC/nansen-legacy-ocean/svim_daily_agg'

# SVIM MLD data:
pth_in_SVIM_MLD = 'https://thredds.met.no/thredds/dodsC/nansen-legacy-ocean/svim_daily_mld_agg'

# Atmospheric forcing data - external path:
pth_atm_forc_ext = '/media/vilhelm/LaCie/Data/SVIM_forcing/yearly_files/'

# Atmospheric forcing data - internal path:
pth_atm_forc_int = '/home/vilhelm/Data/SVIM/forcing/yearly_files/'

# Output files:
pth_output = '/home/vilhelm/Data/OpenDrift/Output/'

# Log files:
pth_log = '/home/vilhelm/Data/OpenDrift/Logs/'

#--------------- Loop over years -----------------

for yi in range(ys, ye+1):

    print('Year: '+str(yi))

    #------ Copy wind forcing file to internal -------

    print('Copying wind forcing file to internal disk')

    ext_wffpth = pth_atm_forc_ext+'ocean_force_'+str(yi)+'.nc'
    int_wffpth = pth_atm_forc_int+'ocean_force_'+str(yi)+'.nc'
    shutil.copy2(ext_wffpth , int_wffpth)

    print('Wind forcing file copied to internal disk!')

    #--------------------- Readers ---------------------

    # Reader for SVIM model data (thredds server):
    reader_SVIM_daily_agg = reader_ROMS_native.Reader(pth_in_SVIM)
    # Reader for SVIM MLD data (thredds server):
    reader_SVIM_MLD = reader_ROMS_native.Reader(pth_in_SVIM_MLD)
    # Reader for atmospheric forcing file (local):
    reader_atm_forc  = reader_ROMS_SVIMforcing.Reader(int_wffpth)

    #--------------- Loop over locations ----------------

    for key, value in lcs.items():
        ind_loc = int(key)
        pos_arr = np.array(value)

        lon = pos_arr[0]
        lat = pos_arr[1]

        #--------------- Loop over months ----------------
        for mi in range(ms, me+1):

            #--------------- Loop over days ----------------
            for di in range(ds, de+1):

                datestr_sdate = str(date(yi, mi, di))

                #--------------- Run simulation ----------------

                print('Running simulation for location '+str(ind_loc)+', seeding date '+datestr_sdate)

                log_fname = pth_log+'lophelia_SVIM_loc'+str(ind_loc)+'_r'+str(radis)+'_n'+str(ns)+'_t'+str(tsim)+'_'+datestr_sdate+'.log'
                o = LopheliaLarvaeDrift(loglevel=0, logfile=log_fname)

                # Add readers:
                o.add_reader([reader_SVIM_daily_agg, reader_SVIM_MLD, reader_atm_forc])

                # Seed lophelia larvae at defined time:
                ts = datetime(yi, mi, di, hs, mms)
                o.seed_elements(lon, lat, z=zs, radius=radis, radius_type='uniform', number=ns, time=ts, diameter=0.0002)

                #----------- Adjusting configurations ------------

                # Adjusting configuration for turbulent mixing:
                o.set_config('drift:vertical_mixing', True)
                o.set_config('vertical_mixing:diffusivitymodel', 'windspeed_Large1994') # windspeed parameterization for eddy diffusivity
                o.set_config('drift:vertical_advection', False)

                # Use ocean model landmask instead of GSHHS:
                o.set_config('general:use_auto_landmask', False)

                # Vertical resolution and time step should be adjusted so to avoid getting
                # output warnings like 'DEBUG: WARNING! some elements have p+q>1.'
                o.set_config('vertical_mixing:timestep', 60.)

                # Output file name:
                outname = pth_output+'lophelia_SVIM_loc'+str(ind_loc)+'_tempdepdev1_tempdepws1_r'+str(radis)+'_n'+str(ns)+'_t'+str(tsim)+'_'+datestr_sdate+'.nc'

                # Run:
                o.run(duration=timedelta(days=tsim), time_step=tstep, time_step_output=tstep_out, outfile=outname)

                print('Simulation for location '+str(ind_loc)+', seeding date '+datestr_sdate+' done!')
    #----- Removing wind forcing file from internal ------

    print('Removing wind forcing file from internal disk')

    os.remove(int_wffpth)

    print('Wind forcing file removed from internal disk!')
