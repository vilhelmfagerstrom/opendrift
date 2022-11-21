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
# Copyright 2022, Knut-Frode Dagestad, MET Norway

"""
OpenHNS is a 3D HNS drift module bundled within the OpenDrift framework.
"""

from io import open
import numpy as np
from datetime import datetime
import pyproj
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

from opendrift.models.oceandrift import OceanDrift, Lagrangian3DArray


# Defining the oil element properties
class HNS(Lagrangian3DArray):
    """Extending LagrangianArray with variables relevant for HNS particles."""

    variables = Lagrangian3DArray.add_variables([
        (   'mass', {
                'dtype': np.float32,
                'units': 'kg',
                'seed': False,
                'default': 1
        }),
        (
            'viscosity',
            {
                'dtype': np.float32,
                'units': 'N s/m2 (Pa s)',
                'seed': False,  # Taken from NOAA database
                'default': 0.005
            }),
        (
            'density',
            {
                'dtype': np.float32,
                'units': 'kg/m^3',
                'seed': False,  # Taken from NOAA database
                'default': 880
            }),
        (
            'wind_drift_factor',
            {
                'dtype':
                np.float32,  # TODO: inherit from
                'units':
                '%',  # OceanDrift
                'description':
                'Elements at the ocean surface are moved by '
                'this fraction of the wind vector, in addition to '
                'currents and Stokes drift',
                'default':
                0.03
            }),
        (
           'diameter',
            {
                'dtype': np.float32,  # Particle diameter
                'units': 'm',
                'seed': False,
                'default': 0.
            })
    ])


class OpenHNS(OceanDrift):
    """Open source HNS drift model based on the OpenDrift framework.

        Developed at MET Norway based on parameterisations
        found in open/published litterature.

        Under construction.
    """

    ElementType = HNS

    required_variables = {
        'x_sea_water_velocity': {
            'fallback': None
        },
        'y_sea_water_velocity': {
            'fallback': None
        },
        'x_wind': {
            'fallback': None
        },
        'y_wind': {
            'fallback': None
        },
        'upward_sea_water_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_significant_height': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_stokes_drift_x_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_stokes_drift_y_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_period_at_variance_spectral_density_maximum': {
            'fallback': 0,
            'important': False
        },
        'sea_surface_wave_mean_period_from_variance_spectral_density_second_frequency_moment':
        {
            'fallback': 0,
            'important': False
        },
        'sea_ice_area_fraction': {
            'fallback': 0,
            'important': False
        },
        'sea_ice_x_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_ice_y_velocity': {
            'fallback': 0,
            'important': False
        },
        'sea_water_temperature': {
            'fallback': 10,
            'profiles': True
        },
        'sea_water_salinity': {
            'fallback': 34,
            'profiles': True
        },
        'sea_floor_depth_below_sea_level': {
            'fallback': 10000
        },
        'ocean_vertical_diffusivity': {
            'fallback': 0.02,
            'important': False,
            'profiles': True
        },
        'land_binary_mask': {
            'fallback': None
        },
        'ocean_mixed_layer_thickness': {
            'fallback': 50,
            'important': False
        },
    }

    # The depth range (in m) which profiles shall cover
    required_profiles_z_range = [-20, 0]

    max_speed = 1.3  # m/s

    hnstypes = ['chem1', 'chem2']

    # Default colors for plotting
    status_colors = {
        'initial': 'green',
        'active': 'blue',
        'missing_data': 'gray',
        'stranded': 'red',
        'evaporated': 'yellow',
        'dispersed': 'magenta'
    }


    def __init__(self, *args, **kwargs):

        # Calling general constructor of parent class
        super(OpenHNS, self).__init__(*args, **kwargs)

        self._add_config({
            'seed:evaporation_rate': {
                'type': 'float',
                'default': .99,
                'min': 0,
                'max': 1e10,
                'units': 's-1',
                'description':
                'The evaporation rate', 
                'level': self.CONFIG_LEVEL_ESSENTIAL,
                'description': 'Evaporation rate'
            },
           'seed:entrainment_rate': {
                'type': 'float',
                'default': 1,
                'min': 0,
                'max': 1e10,
                'units': '1',
                'description':
                'The evaporation rate', 
                'level': self.CONFIG_LEVEL_ESSENTIAL,
                'description': 'Entrainment rate'
            },
           'seed:hns_type': {
                'type':
                'enum',
                'enum':
                self.hnstypes,
                'default':
                self.hnstypes[0],
                'level':
                self.CONFIG_LEVEL_ESSENTIAL,
                'description':
                'HNS type to be used for the simulation'
            },
        })

        self._set_config_default('drift:vertical_advection', False)
        self._set_config_default('drift:vertical_mixing', True)
        self._set_config_default('drift:current_uncertainty', 0.05)
        self._set_config_default('drift:wind_uncertainty', 0.5)

    def evaporation(self):
        print('Evaporating!')
        surface = np.where(self.elements.z == 0)[0]
        random_number = np.random.uniform(0, 1, len(surface))
        evaporated = np.where(random_number > self.get_config('seed:evaporation_rate'))[0]
        logger.debug('Evaporating %i of %i elements at ocean surface' % (len(evaporated), len(surface)))
        self.elements.wind_drift_factor[evaporated] = 1  # Shall follow wind 100%
        self.elements.z[evaporated] = 10  # Moving evaporated elements to 10m height


    def update(self):

        self.evaporation()
        #self.advect_ocean_current()
        self.advect_wind()
