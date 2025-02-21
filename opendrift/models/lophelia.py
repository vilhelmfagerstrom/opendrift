# This file is part of OpenDrift.
#
# OpenDrift is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2
#
# OpenDrift is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenDrift.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright 2015, Knut-Frode Dagestad, MET Norway

import numpy as np
import logging; logger = logging.getLogger(__name__)

from opendrift.models.oceandrift import OceanDrift, Lagrangian3DArray
#from opendrift.elements import LagrangianArray

#--------- Set parameters for simulation ---------

# Temperature dependence of develpoment rate ON(1) or OFF(0)
global tempdepdev
tempdepdev = 1

# Temperature dependence of vertical swimming ON(1) or OFF(0
global tempdepws
tempdepws = 1

# Set temperature for temperature INDEPENDENT simulation
global settemp
settemp = 8

#-------------------------------------------------

# Defining element properties
class LopheliaLarvae(Lagrangian3DArray):
    """Extending Lagrangian3DArray with specific properties for Lophelia larvae
    """

    variables = Lagrangian3DArray.add_variables([
        ('diameter', {'dtype': np.float32,
                      'units': 'm',
                      'default': 0.0002}),  # For Lophelia
        ('density', {'dtype': np.float32,
                     'units': 'kg/m^3',
                     'default': 1028.}),
        ('devlev', {'dtype': np.float32,
                         'units': '',
                         'default': 0.}),
        ('devstage', {'dtype': np.float32,
                         'units': '',
                         'default': 0.}),
        ('settle', {'dtype': np.int32,
                         'units': '',
                         'default': 0.}),
        ('hatched', {'dtype': np.float32,
                     'units': '',
                     'default': 0.})])


class LopheliaLarvaeDrift(OceanDrift):
    """Buoyant particle trajectory model based on the OpenDrift framework.
        Developed at MET Norway
        Generic module for particles that are subject to vertical turbulent
        mixing with the possibility for positive or negative buoyancy
        Lophelia larvae assumed to ber neutrally buoyant throughout
        Particles could be e.g. oil droplets, plankton, or sediments
        Under construction.
    """

    ElementType = LopheliaLarvae

    required_variables = {
        'x_sea_water_velocity': {'fallback': 0},
        'y_sea_water_velocity': {'fallback': 0},
        'sea_surface_wave_stokes_drift_x_velocity': {'fallback': 0},
        'sea_surface_wave_stokes_drift_y_velocity': {'fallback': 0},
        'sea_surface_wave_significant_height': {'fallback': 0},
        'sea_ice_area_fraction': {'fallback': 0},
        'x_wind': {'fallback': 0},
        'y_wind': {'fallback': 0},
        'land_binary_mask': {'fallback': None},
        'sea_floor_depth_below_sea_level': {'fallback': 100},
        'ocean_vertical_diffusivity': {'fallback': 0.02, 'profiles': True},
        'ocean_mixed_layer_thickness': {'fallback': 50},
        'sea_water_temperature': {'fallback': 10, 'profiles': True},
        'sea_water_salinity': {'fallback': 34, 'profiles': True},
        'surface_downward_x_stress': {'fallback': 0},
        'surface_downward_y_stress': {'fallback': 0},
        'turbulent_kinetic_energy': {'fallback': 0},
        'turbulent_generic_length_scale': {'fallback': 0},
        'upward_sea_water_velocity': {'fallback': 0},
      }

    # Vertical profiles of the following parameters will be available in
    # dictionary self.environment.vertical_profiles
    # E.g. self.environment_profiles['x_sea_water_velocity']
    # will be an array of size [vertical_levels, num_elements]
    # The vertical levels are available as
    # self.environment_profiles['z'] or
    # self.environment_profiles['sigma'] (not yet implemented)
    required_profiles = ['sea_water_temperature',
                         'sea_water_salinity',
                         'ocean_vertical_diffusivity']
    # The depth range (in m) which profiles shall cover
    required_profiles_z_range = [-3000, 0]


    # Default colors for plotting
    status_colors = {'initial': 'green', 'active': 'blue',
                     'spawned': 'red', 'settled': 'yellow', 'died': 'magenta'}


    def __init__(self, *args, **kwargs):

        # Calling general constructor of parent class
        super(LopheliaLarvaeDrift, self).__init__(*args, **kwargs)

        # By default, elements do not strand towards coastline
        self.set_config('general:coastline_action', 'previous')

        # Elements are lifted to seafloor if grounded and pre-comptetent
        self.set_config('general:seafloor_action', 'lift_to_seafloor')

        # Vertical mixing is enabled by default
        self.set_config('drift:vertical_mixing', True)

    # Define seafloor interaction (override function in basemodel):
    def interact_with_seafloor(self):
        """Seafloor interaction according to configuration setting"""
        if self.num_elements_active() == 0:
            return
        if 'sea_floor_depth_below_sea_level' not in self.priority_list:
            return
        sea_floor_depth = self.sea_floor_depth()
        below = np.where(self.elements.z < -sea_floor_depth)[0]

        # Update indicies for settlable larvae
        global ID_setpot
        ID_setpot = self.elements.ID[((self.elements.z < -sea_floor_depth) & (self.elements.devlev >= 2)) | (self.elements.settle == 1)]

        if len(below) == 0:
            logger.debug('No elements hit seafloor.')
            return

        i = self.get_config('general:seafloor_action')
        if i == 'lift_to_seafloor':
            logger.debug('Lifting %s elements to seafloor.' % len(below))
            self.elements.z[below] = -sea_floor_depth[below]
        elif i == 'deactivate':
            self.deactivate_elements(self.elements.z < -sea_floor_depth,
                                     reason='seafloor')
            self.elements.z[below] = -sea_floor_depth[below]
        elif i == 'previous':  # Go back to previous position (in water)
            logger.warning('%s elements hit seafloor, '
                           'moving back ' % len(below))
            below_ID = self.elements.ID[below]
            self.elements.lon[below] = \
                np.copy(self.previous_lon[below_ID - 1])
            self.elements.lat[below] = \
                np.copy(self.previous_lat[below_ID - 1])

    # Define procedure for update of terminal velocity:
    def update_terminal_velocity(self, Tprofiles=None, Sprofiles=None, z_index=None):
        """Calculate terminal velocity for larvae
        """

	    # Set parameters for vertical velocities depending on stage (age) in larval phase:
        sday = 24*60*60 # Seconds in one day
        reftemp = 8 # Reference temperature
        t_wsmax = 14*24 # Age in hours at which maximum vertical velocity is reached at reftemp
        t1 = 1056.8*np.exp(0.0907*np.log(reftemp)**2)/reftemp**1.536 # Age in hours at which first cilia appear at reftemp
        t2 = 83283*np.exp(0.5182*np.log(reftemp)**2)/reftemp**3.565 # Age in hours at which first cnidocysts appear at reftemp
        tmax = 90*24 # Maximum age in hours at reftemp

        global devlev_tmax
        #devlev_tmax = 1+tmax/(t2-t1) # Develpoment level at tmax
        devlev_tmax = 1+(tmax-t1)/(t2-t1) # Develpoment level at tmax

        # Development stage at which maximum vertical velocity is reached
        #devlev_wsmax = 1+t_wsmax/(t2-t1)
        devlev_wsmax = 1+(t_wsmax-t1)/(t2-t1)

        # Coefficients for equations:
        aT = 0.1547
        bT = 0.08893

        # Indicies for development levels/stages for swimming behavior
        ind_Devst0 = self.elements.devlev < 1
        ind_Devst1_1 = (self.elements.devlev >= 1) & (self.elements.devlev < devlev_wsmax)
        ind_Devst1_2 = (self.elements.devlev >= devlev_wsmax) & (self.elements.devlev < 2)
        ind_Devst2 = self.elements.devlev >= 2

        if tempdepws == 1:
            # Temperature DEPENDENT terminal velocity
            self.elements.terminal_velocity[ind_Devst0] = 0
            self.elements.terminal_velocity[ind_Devst1_1] = 1e-3*(aT*np.exp(bT*self.environment.sea_water_temperature[ind_Devst1_1]))*((self.elements.devlev[ind_Devst1_1]-1)/(devlev_wsmax-1))*np.sign(self.time_step.total_seconds())
            self.elements.terminal_velocity[ind_Devst1_2] = 1e-3*(aT*np.exp(bT*self.environment.sea_water_temperature[ind_Devst1_2]))*np.sign(self.time_step.total_seconds())
            self.elements.terminal_velocity[ind_Devst2] = -1e-3*(aT*np.exp(bT*self.environment.sea_water_temperature[ind_Devst2]))*np.sign(self.time_step.total_seconds())

        elif tempdepws == 0:
            # Temperature INDEPENDENT terminal velocity
            self.elements.terminal_velocity[ind_Devst0] = 0
            self.elements.terminal_velocity[ind_Devst1_1] = 1e-3*(aT*np.exp(bT*settemp))*((self.elements.devlev[ind_Devst1_1]-1)/(devlev_wsmax-1))*np.sign(self.time_step.total_seconds())
            self.elements.terminal_velocity[ind_Devst1_2] = 1e-3*(aT*np.exp(bT*settemp))*np.sign(self.time_step.total_seconds())
            self.elements.terminal_velocity[ind_Devst2] = -1e-3*(aT*np.exp(bT*settemp))*np.sign(self.time_step.total_seconds())

    def update(self):
        """Update positions and properties of particles."""

        # Coefficients and exponents for equations:
        aDevst0 = 1056.8*3600
        bDevst0 = 0.0907
        cDevst0 = 1.536

        aDevst1 = 83283*3600
        bDevst1 = 0.5182
        cDevst1 = 3.565

        if tempdepdev == 1:
            # Update temperature DEPENDENT development level
            self.elements.devlev[(self.elements.devstage == 0) & (self.environment.sea_water_temperature > 0)] += self.time_step.total_seconds()*(1/(aDevst0*np.exp(bDevst0*np.log(self.environment.sea_water_temperature[(self.elements.devstage == 0) & (self.environment.sea_water_temperature > 0)])**2)/(self.environment.sea_water_temperature[(self.elements.devstage == 0) & (self.environment.sea_water_temperature > 0)])**cDevst0))
            self.elements.devlev[(self.elements.devstage >= 1) & (self.environment.sea_water_temperature > 0)] += self.time_step.total_seconds()*(1/((aDevst1*np.exp(bDevst1*np.log(self.environment.sea_water_temperature[(self.elements.devstage >= 1) & (self.environment.sea_water_temperature > 0)])**2)/(self.environment.sea_water_temperature[(self.elements.devstage >= 1) & (self.environment.sea_water_temperature > 0)])**cDevst1)-(aDevst0*np.exp(bDevst0*np.log(self.environment.sea_water_temperature[(self.elements.devstage >= 1) & (self.environment.sea_water_temperature > 0)])**2)/(self.environment.sea_water_temperature[(self.elements.devstage >= 1) & (self.environment.sea_water_temperature > 0)])**cDevst0)))
            self.elements.devlev[(self.environment.sea_water_temperature <= 0)] += 0
        elif tempdepdev == 0:
            # Update temperature INDEPENDENT development level
            self.elements.devlev[(self.elements.devstage == 0) & (self.environment.sea_water_temperature > 0)] += self.time_step.total_seconds()*(1/(aDevst0*np.exp(bDevst0*np.log(settemp)**2)/(settemp)**cDevst0))
            self.elements.devlev[(self.elements.devstage >= 1) & (self.environment.sea_water_temperature > 0)] += self.time_step.total_seconds()*(1/((aDevst1*np.exp(bDevst1*np.log(settemp)**2)/(settemp)**cDevst1)-(aDevst0*np.exp(bDevst0*np.log(settemp)**2)/(settemp)**cDevst0)))
            self.elements.devlev[(self.environment.sea_water_temperature <= 0)] += 0

        # Update potential to settle stage
        bol_ID_setpot = np.isin(self.elements.ID,ID_setpot)
        self.elements.settle[:] = bol_ID_setpot.astype(int)

        # Update development stage
        self.elements.devstage[(self.elements.devlev >= 1)] = 1
        self.elements.devstage[(self.elements.devlev >= 2)] = 2

        # Turbulent Mixing
        self.update_terminal_velocity()
        self.vertical_mixing()

        # Horizontal advection
        self.advect_ocean_current()

        # Vertical advection
        if self.get_config('drift:vertical_advection') is True:
            self.vertical_advection()
