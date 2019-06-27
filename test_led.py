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
n_led = 1400


parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="169.254.150.219")
parser.add_argument("--port", type=int, default=5005)
args = parser.parse_args()

client = udp_client.SimpleUDPClient(args.ip, args.port)

dots = DotStrip(client, n_led)
with ExperimentController('test_led', output_dir=None, version='dev', 
                          participant='foo', session='foo', 
                          full_screen=False) as ec:
    dots.init_osc()
    dots.clear_strip()
    dots.send()
    
    tom = Line(ec, dots, [.3, .3, .3, .6], [0, 399])
    #tom = Dot(ec, dots, [.7, .4, 0, .6], 140 * 3)
    tom.draw()
    dots.send()
    ec.screen_prompt('There are three blending modes')
    
    blend1 = Gaussian(ec, dots, [.4, .8, 0, .3], 100, 10)
    blend1.draw()
    dots.send()
    ec.screen_prompt('Background Shape')
    
    blend2 = Line(ec, dots, [.6, .6, .6, .4], [90, 95])
    blend3 = Line(ec, dots, [.6, .6, .6, .4], [97, 102])
    blend4 = Line(ec, dots, [.6, .6, .6, .4], [105, 110])
    blend3.draw('max') 
    blend2.draw('occlude')
    blend4.draw('add')
    dots.send()
    ec.screen_prompt('White line on top with occlude, max, and add modes')
    
    dots.clear_strip()
    dots.send()
    ec.screen_prompt('Now some simple shapes') 

    test1 = Dot(ec, dots, [.3, .3, .1, .8], 90)
    test1.draw()
    dots.send()
    ec.screen_prompt('Dot')

    test2 = Line(ec, dots, [.7, .2, .3, .3], [95, 100]) 
    test2.draw()
    dots.send()
    ec.screen_prompt('Line')

    test3 = Gaussian(ec, dots, [.3, .4, .7, .5], 110, 3)
    test3.draw()
    dots.send()
    ec.screen_prompt('Gaussian')  
    
    test4 = Tukey(ec, dots, [.9, .6, .1, .5], 120, 10, .9)
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
    images = [PixelArray(ec, dots, colors, [a, b]) for a, b in 
                  zip(np.arange(120, n_led - 50, 2), np.arange(160, n_led - 10, 2))]

    while not pressed:
        ec.listen_presses()
        for i in images:
            i.draw()
            dots.send()
            dots.clear_strip()
            ec.wait_secs(0)
            pressed = ec.get_presses()
    
    
    dots.clear_strip()
    dots.send()
    ec.screen_prompt('Clear')