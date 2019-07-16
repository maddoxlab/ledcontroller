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

    def __init__(self, client, n_leds, packet_size=1500):
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
        
        g = np.ceil(colors[:, :3].max(1) * g_max).astype(np.uint8)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            c = np.round(c_max * colors / g[:, np.newaxis] \
                    * g_max).astype(np.uint8)

        bright = np.uint8(g + int('11100000', 2))
        colors = np.concatenate((bright[:, np.newaxis], 
                                 np.fliplr(np.uint8(c))), 1)                            
        colors = list(colors.ravel())
        return colors


    def _make_bytes(self, colors):
        start = [np.uint8(0)] * 4
        end = [np.uint8(0)] * int(np.ceil((len(colors) / 2. + 1) / 8.))
        # end = [np.uint8(0)] * 4 * 4

        pixels = []
        pixels = self._make_pixel(colors)
        self._buffer = start + pixels + end
        return start + pixels + end


    def _gamma_correct(self, x):
        coefs = np.array([ 0.7862484 ,  0.24822052, -0.03472465,  0.00123544])
        return np.maximum(np.minimum(np.polyval(coefs, x) - .003, 1), 0)
    
    def init_osc(self):
        #        """Send dot params to server"""
        #        self._client.send_message("/led_init", [self._n_leds,
        #                                                self._packet_size,
        #                                                self._n_segments,
        #                                                len(self._buffer)])
        self._tcp = True

    def clear_strip(self):
        """Zero the LED buffer"""
        self._colors = np.zeros((self._n_leds, 4))
        self._buffer = self._make_bytes(self._colors)


    def send(self):
        """Execute LED OSC command"""
        import time
        start = time.time()
        self._client.sendall(bytes(self._buffer))
        #received = self._client.recv(65536)
        #print('Received ', len(received), ' bytes')
        #print((time.time() - start) * 1e3)
        if not self._tcp:
            raise ValueError('Must run init_osc method first.')


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
            self._colors[pos] = color
            
        else:
            print('nice try')


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
        
        if units == 'ind':
            self._colors[pos[0]:pos[1]] = color
            
        else:
            print('nice try')


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
        
        if units == 'ind':
            colors = np.ones(self._led._colors.shape) * color
            x = np.arange(self._led._n_leds)
            env = np.exp(-np.power(x - pos, 2.) / (2 * np.power(width, 2.)))
            env[env < threshold] = 0
            colors[:, -1] *= env
            colors[env < threshold] = 0
            self._colors = colors
            
        else:
            print('nice try')
            

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
        if units == 'ind':
            colors = np.ones((width, 4)) * color
            win = tukey(width, alpha)
            start = int(pos - width/2)
            stop = start + width
            colors[:, -1] *= win
            self._colors[start:stop] = colors

        else:
            print('nice try')
            

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
    

    def __init__(self, ec, led, colors, extent):
        from scipy.signal import resample
        self._ec = ec
        self._led = led
        if colors.shape[-1] != 4:
            raise ValueError('Must specify RGBA colors')
        if np.diff(extent) != colors.shape[0]:
            colors = resample(colors, int(np.diff(extent)))
            
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