#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 31 09:27:18 2019

@author: maddy
"""
import numpy as np
from expyfun._utils import logger
import warnings

class DotStrip:
    """Object for using LED DotStrip
    
    Parameters
    ----------
    client : instance of udpclient
        Usage as:
            
        # import argparse
        # from pythonosc import udp_client
        # parser = argparse.ArgumentParser()
        # parser.add_argument("--ip", default="169.254.150.219")
        # parser.add_argument("--port", type=int, default=5005)
        # args = parser.parse_args()
        # client = udp_client.SimpleUDPClient(args.ip, args.port)
        
    n_leds : int
        Number of LEDs in the strip
    packet_size : int
        Number of floats to send in each OSC message -- must be lower than 1634
    Returns
    -------
    dotstrip : instance of DotStrip
        The dotstrip object.
    """

    def __init__(self, client, n_leds, offset=False, packet_size=1500):
        if not isinstance(n_leds, int):
            raise ValueError('n_leds must be type int')
        if not isinstance(packet_size, int):
            raise ValueError('packet_size must be type int')
        self._n_leds = n_leds
        if packet_size > 1634:
            raise ValueError('packet_size must be less than 1634')
        self._client = client
        self._colors = np.zeros((n_leds, 4))
        self._pre_buffer = np.zeros((n_leds, 4))
        self._buffer = self._make_bytes(self._colors)
        self._packet_size = packet_size
        self._n_segments = int(np.ceil(len(self._buffer) / self._packet_size))
        self._tcp = False
        self._offset = offset


    def _make_pixel(self, colors):
        
        colors = np.array(colors, dtype=np.float64)
        if colors.shape[-1] not in [3, 4]:
            raise ValueError('Must specify RGB or RGBA value')
        if colors.shape[-1] == 3:
            colors = np.concatenate((colors, np.ones((self.n_leds, 1))), 0)
        assert(colors.shape[-1] == 4)

        colors = colors[:, :3] * colors[:, 3][:, np.newaxis]
        colors = self._gamma_correct(colors)
        c_max = 255
        g_max = 2 ** 5 - 2
        
        g = np.ceil(colors[:, :3].max(1) * g_max / c_max).astype(np.uint8)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            c = np.round(colors / g[:, np.newaxis]).astype(np.uint8)

        bright = np.uint8(g + int('11100000', 2))
        colors = np.concatenate((bright[:, np.newaxis], 
                                 np.fliplr(np.uint8(c))), 1)                            
        colors = list(colors.ravel())
        return colors


    def _make_bytes(self, colors):
        start = [np.uint8(0)] * 4
        end = [np.uint8(0)] * int(np.ceil((len(colors) / 2. + 1) / 8.))

        pixels = []
        pixels = self._make_pixel(colors)
        self._buffer = start + pixels + end
        return start + pixels + end


    def _gamma_correct(self, x):
        
        ref_vals = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                             1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3,
                             3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5,
                             6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9,
                             9, 10, 10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 
                             14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 
                             20, 20, 21, 21, 22, 22, 23, 24, 24, 25, 25, 26,
                             27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 
                             35, 36, 37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 
                             46, 47, 48, 49, 50, 50, 51, 52, 54, 55, 56, 57, 
                             58, 59, 60, 61, 62, 63, 64, 66, 67, 68, 69, 70, 
                             72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 
                             87, 89, 90, 92, 93, 95, 96, 98, 99, 101, 102, 104, 
                             105, 107, 109, 110, 112, 114, 115, 117, 119, 120, 
                             122, 124, 126, 127, 129, 131, 133, 135, 137, 138, 
                             140, 142, 144, 146, 148, 150, 152, 154, 156, 158, 
                             160, 162, 164, 167, 169, 171, 173, 175, 177, 180, 
                             182, 184, 186, 189, 191, 193, 196, 198, 200, 203,
                             205, 208, 210, 213, 215, 218, 220, 223, 225, 228,
                             231, 233, 236, 239, 241, 244, 247, 249, 252, 255])
#        coefs = np.array([ 0.7862484 ,  0.24822052, -0.03472465,  0.00123544])
#        return np.maximum(np.minimum(np.polyval(coefs, x) - .003, 1), 0)
        return ref_vals[np.array(np.ceil(x * 255), dtype=int)]


    def clear_strip(self):
        """Zero the LED buffer"""
        self._colors = np.zeros((self._n_leds, 4))
        self._buffer = self._make_bytes(self._colors)


    def send(self):
        """Execute LED OSC command"""
        self._client.sendall(bytes(self._buffer))
            
        
    def convert_units(self, pos, fro, to):
        """Convert units of LED index to degrees azimuth
        
        Parameters
        ----------
        pos : int or list or 1D array
            positions in either int or deg
        fro : str
            the units of pos -- either 'int' or 'deg'
        to : str
            the desired units -- either 'int' or 'deg'
        """

        calibration_inds = [246, 493, 740, 1008]
        calibration_deg = [58, 10, -38, -90]
        if isinstance(pos, int):
            pos = [pos]
        if fro == 'ind' and to == 'deg':        
            if self._offset:
                fit = np.polyfit(calibration_inds, np.array(calibration_deg) + 2, 1)
            else:
                fit = np.polyfit(calibration_inds, calibration_deg, 1)
        elif fro == 'deg' and to == 'ind':
            if self._offset:
                fit = np.polyfit(np.array(calibration_deg) + 2, calibration_inds, 1)
            else:
                fit = np.polyfit(calibration_deg, calibration_inds, 1)
        else:
            raise ValueError('fro and to must be "ind" and "deg", "deg"'
                             'and "ind" or "deg"')
        return [np.polyval(fit, p) for p in pos]
    
    def get_nearest_speaker(self, azimuth, units):    
        if units == 'ind':
            azimuth = self.convert_units(azimuth, 'ind', 'deg')
        if units == 'deg' and self._offset:
            azimuth -= 2
        return int(azimuth / 4 + 26)
    
    def get_speaker_location(self, speaker_ind, to_units):
        azimuth = (speaker_ind - 26) * 4
        if to_units == 'ind':
            azimuth = self.convert_units(azimuth, 'deg', 'ind')
        return azimuth

class _LightShape(object):
    """Super class for led objects"""


    def __init__(self, ec, led, color):
        self._ec = ec
        self._led = led
        if len(color) != 4:
            raise ValueError('Must specify RGBA color')
        self._fill_color = color
        self._colors = np.zeros(self._led._colors.shape)


    def draw(self, blend_mode='add'):
        """Draw LightShape object onto led buffer
        
        Parameters
        ----------
        blend_mode : str
            How to draw new object in relation to other objects
            'add' : add translucent object on top of existing objects
            'max' : show whichever object is brighter
            'occlude' : add opaque object on top of existing objects
        """

        if blend_mode == 'add':
            self._led._colors += self._colors
            if any(self._led._colors.ravel() > 1):
                logger.warning('Buffer values exceed 1. '
                               'Color distortion may occur.')
        if blend_mode == 'max':
            inds = np.where([dat > col for dat, col
                             in zip(self._colors[:, -1],
                                    self._led._colors[:, -1])])
            self._led._colors[inds] = self._colors[inds]
        if blend_mode == 'occlude':
            self._led._colors[self._colors[:, -1] > 0] = \
                self._colors[self._colors[:, -1] > 0]
        
        self._led._buffer = \
            self._led._make_bytes(np.minimum(1, self._led._colors))
        self._led._pre_buffer = np.zeros((self._led._pre_buffer.shape))


class Dot(_LightShape):
    """A single LED
    
    Parameters
    ----------
    ec : instance of ExperimentController
        Parent EC.
    led : instance of DotStrip
        Parent LED.
    color : list of 4
        Fill color of the dot
    pos : int or float
        must be int if 'ind', else can be int or float
    units : str
        'ind', 'deg'
    Returns
    -------
    dot : instance of Dot
        The dot object.
    """

    def __init__(self, ec, led, color, pos, units='ind'):
        _LightShape.__init__(self, ec, led, color)
        
        if units == 'ind':
            assert(isinstance(pos, int))
        elif units == 'deg':
            pos = int(np.round(self._led.convert_units(pos, 'deg', 'ind')[0]))
        else:
            raise ValueError('units must be either "ind" or "deg"')
        self._colors[pos] = color


class Line(_LightShape):
    """A bar of LEDs
    
    Parameters
    ----------
    ec : instance of ExperimentController
        Parent EC.
    led : instance of DotStrip
        Parent LED.
    color : list of 4
        Fill color of the bar
    pos : 2x1 array or list of 2
        elements must be int if 'ind', else can be int or float
    units : str
        'ind', 'deg'
    Returns
    -------
    line : instance of Line
        The line object.
    """

    def __init__(self, ec, led, color, pos, units='ind'):
        _LightShape.__init__(self, ec, led, color)
        if pos[0] > pos[1]:
            raise ValueError('Position must be specified as [start, stop]')
        if units == 'deg':
            pos = np.array(np.round(self._led.convert_units(pos, 'deg', 'ind')),
                           dtype=int)
            pos = np.flip(pos, 0)
        self._colors[pos[0]:pos[1]] = color


class Gaussian(_LightShape):
    """A bar of LEDs with Gaussian envelope
    
    Parameters
    ----------
    ec : instance of ExperimentController
        Parent EC.
    led : instance of DotStrip
        Parent LED.
    color : list of 4
        Fill color of the bar
    pos : int or float
        center of bar must be int if 'ind', else can be int or float
    width : int or float
        std of gaussian
    units : str
        'ind', 'deg'
    threshold : float
        envelope value to cut off illumination
    
    Returns
    -------
    gaussian : instance of Gaussian
        The gaussian object.
    """

    def __init__(self, ec, led, color, pos, width, units='ind', threshold=0.2):
        _LightShape.__init__(self, ec, led, color)
        
        if units == 'deg':
            pos = self._led.convert_units(pos, 'deg', 'ind')[0]
            width = np.abs(self._led.convert_units(width, 'deg', 'ind')[0] - 
                           self._led._n_leds // 2)
        colors = np.ones(self._led._colors.shape) * color
        x = np.arange(self._led._n_leds)
        env = np.exp(-np.power(x - pos, 2.) / (2 * np.power(width, 2.)))
        env[env < threshold] = 0
        colors[:, -1] *= env
        colors[env < threshold] = 0
        self._colors = colors


class Tukey(_LightShape):
    """A bar of LEDs with Tukey window envelope
    
    Parameters
    ----------
    ec : instance of ExperimentController
        Parent EC.
    led : instance of DotStrip
        Parent LED.
    color : list of 4
        Fill color of the bar
    pos : 2x1 array or list of 2
        elements must be int if 'ind', else can be int or float
    width : int
        width of the tukey window
    alpha : float
        tukey parameter
    units : str
        'ind', 'deg'
    Returns
    -------
    tukey : instance of Tukey
        The tukey object. 
    """

    def __init__(self, ec, led, color, pos, width, alpha, units='ind'):
        _LightShape.__init__(self, ec, led, color)
        from scipy.signal import tukey
        if units == 'deg':
            pos = self._led.convert_units([pos], 'deg', 'ind')[0]
            width = np.abs(self._led.convert_units(width, 'deg', 'ind')[0] - 
                           self._led._n_leds // 2)
        colors = np.ones((int(width), 4)) * color
        win = tukey(int(width), alpha)
        start = int(pos - width/2)
        stop = int(start + width)
        colors[:, -1] *= win
        self._colors[start:stop] = colors


class PixelArray():
    """Set arbitray pixel colors
    
    Parameters
    ----------
    ec : instance of ExperimentController
        Parent EC.
    led : instance of DotStrip
        Parent LED.
    colors : N x 4 array
        Fill colors of the dots
    extent : 2x1 array or list of 2
        elements must be int if 'ind', else can be int or float
    width : int
        width of the tukey window
    alpha : float
        tukey parameter
    units : str
        'ind', 'deg'
    Returns
    -------
    pixelarray : instance of PixelArray
        The pixelarray object. 
    """

    def __init__(self, ec, led, colors, extent, units='ind'):
        from scipy.interpolate import CubicSpline
        self._ec = ec
        self._led = led
        if colors.shape[-1] != 4:
            raise ValueError('Must specify RGBA colors')
        if units == 'deg':
            extent = self._led.convert_units(extent, 'deg', 'ind')
        if np.diff(extent) != colors.shape[0]:
            cs = CubicSpline(np.arange(len(colors)), colors)
            colors = cs(np.arange(self._led._n_leds) / len(colors))
        self._colors = np.zeros(self._led._colors.shape)
        self._colors[extent[0]:extent[1]] = colors


    def draw(self, blend_mode='add'):
        """Draw LightShape object onto led buffer
        
        Parameters
        ----------
        blend_mode : str
            How to draw new object in relation to other objects
            'add' : add translucent object on top of existing objects
            'max' : show whichever object is brighter
            'occlude' : add opaque object on top of existing objects
        """


        if blend_mode == 'add':
            self._led._colors += self._colors
            if any(self._led._colors.ravel() > 1):
                logger.warning('Buffer values exceed 1. '
                               'Color distortion may occur.')
        if blend_mode == 'max':
            inds = np.where([dat > col for dat, col
                             in zip(self._colors[:, -1],
                                    self._led._colors[:, -1])])
            self._led._colors[inds] = self._colors[inds]
        if blend_mode == 'occlude':
            self._led._colors[self._colors[:, -1] > 0] = \
                self._colors[self._colors[:, -1] > 0]
        
        self._led._buffer = \
            self._led._make_bytes(np.minimum(1, self._led._colors))
        self._led._pre_buffer = np.zeros((self._led._pre_buffer.shape))