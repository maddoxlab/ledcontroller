# -*- coding: utf-8 -*-
"""
Created on Fri May 31 10:37:22 2019

@author: mcappelloni
"""
from _led import (DotStrip, _LightShape, Dot, Line, Gaussian, Tukey, PixelArray)
import argparse
import numpy as np 
from pythonosc import udp_client, osc_bundle_builder
import matplotlib.pyplot as plt
from expyfun import ExperimentController
do_full = False
do_single = True
n_led = 1110

import socket
HOST = '169.254.150.219'  # The server's hostname or IP address
PORT = 5005        # The port used by the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

dots = DotStrip(client, n_led)

with ExperimentController('test_led', output_dir=None, version='dev', 
                          participant='foo', session='foo', 
                          full_screen=False) as ec:
    dots.init_osc()
    dots.clear_strip()
    dots.send()
    
    ec.screen_prompt('There are three blending modes')
    
    blend1 = Gaussian(ec, dots, [.4, .8, 0, .3], 600, 10)
    blend1.draw()
    dots.send()
    ec.screen_prompt('Background Shape')
    
    blend2 = Line(ec, dots, [.6, .6, .6, .4], [590, 595])
    blend3 = Line(ec, dots, [.6, .6, .6, .4], [597, 602])
    blend4 = Line(ec, dots, [.6, .6, .6, .4], [605, 610])
    blend3.draw('max') 
    blend2.draw('occlude')
    blend4.draw('add')
    dots.send()
    ec.screen_prompt('White line on top with occlude, max, and add modes')
    
    dots.clear_strip()
    dots.send()
    ec.screen_prompt('Now some simple shapes') 

    test1 = Dot(ec, dots, [.3, .3, .1, .8], 590)
    test1.draw()
    dots.send()
    ec.screen_prompt('Dot')

    test2 = Line(ec, dots, [.7, .2, .3, .3], [595, 600]) 
    test2.draw()
    dots.send()
    ec.screen_prompt('Line')

    test3 = Gaussian(ec, dots, [.3, .4, .7, .5], 610, 3)
    test3.draw()
    dots.send()
    ec.screen_prompt('Gaussian')  
    
    test4 = Tukey(ec, dots, [.9, .6, .1, .5], 620, 10, .9)
    test4.draw()
    dots.send()
    ec.screen_prompt('Tukey with alpha=.9')
    
    dots.clear_strip()
    dots.send()
    ec.screen_prompt('Now use any arbitrary array') 
    
    pressed = None
    ec.screen_text('Press any key to exit')
    ec.flip()
    cm = plt.get_cmap('hsv')
    colors = cm(np.linspace(0, 1, 40, dtype=float))
    colors[:, -1] = .3 
    images = [PixelArray(ec, dots, colors, [a+300, b+300]) for a, b in 
                  zip(np.arange(120, 400, 10), np.arange(160, 440, 10))]

    while not pressed:
        ec.listen_presses()
        for i in images:
            i.draw()
            dots.send()
            dots.clear_strip()
            ec.wait_secs(0)
            pressed = ec.get_presses()

    client.sendall(bytes(1))
    client.close()
