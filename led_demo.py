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
modes = ['Full Rainbow', 'Gradient', 'Model Train', 'Cylon', 'Noise']

with ExperimentController('test_led', output_dir=None, version='dev', 
                          participant='foo', session='foo', 
                          full_screen=False) as ec:
    dots.init_osc()

    dots.clear_strip()
    dots.send()
    instructions = ('Press (1) ' + modes[0] + ' (2) ' + modes[1] + ' (3) '
                    + modes[2] + ' (4) ' + modes[3] + ' (5) ' + modes[4] + ' (6) EXIT')
    pressed = ec.screen_prompt(instructions)
    
    x_half = np.concatenate((np.arange(300, 792), 792 * np.ones((5, )), np.flipud(np.arange(300, 792)), 300 * np.ones((5, ))), 0)
    x_range = np.concatenate((x_half, np.flipud(x_half)), 0)
    cylon = [Dot(ec, dots, [1, 0, 0, .7], int(x)) for x in x_range]
    cm = plt.get_cmap('hsv')
    colors = cm(np.linspace(0, 1, 150, dtype=float))
    colors[:, -1] = .4 
    full_rainbow = [Line(ec, dots, c, [0, n_led - 1]) for c in colors]
    cm = plt.get_cmap('winter')
    colors = cm(np.linspace(0, 1, n_led // 2, dtype=float))
    colors = np.concatenate((colors, np.flipud(colors)), 0)
    colors[:, -1] *= .4
    gradient = [PixelArray(ec, dots, np.roll(colors, shift, 0), [0, n_led - 1]) for shift in np.arange(0, 1109, 5)]
    cm = plt.get_cmap('gray')
    colors = cm(np.linspace(0, 1, 20, dtype=float))
    colors[:, -1] *= .5
    model_train = [[Dot(ec, dots, c, (x + shift) % 1109) for shift, c in enumerate(colors)] for x in range(1109)]
    colors = np.random.rand(100, 1109, 4)
    colors[:, :, -1] = .4
    noise = [PixelArray(ec, dots, c, [0, n_led - 1]) for c in colors]
    all_stim = [full_rainbow, gradient, model_train, cylon, noise]
    ec.listen_presses()
    ec.screen_text(instructions)
    ec.flip()
    start = ec.current_time
    while int(pressed) != 6:
        i = int(pressed) - 1
        stim = all_stim[i]
        for s in stim:
            if type(s) == list:
                [ss.draw() for ss in s]
            else:
                s.draw('occlude')
            ec.wait_until(start + .005)
            dots.send()
            start = ec.current_time
            dots.clear_strip()
            change = ec.get_presses(timestamp=False)
            if change:
                pressed = change[0][0]
            ec.listen_presses()
            
    dots.clear_strip()
    dots.send()
    ec.wait_secs(1)
    client.sendall(bytes(1))
    client.close()
