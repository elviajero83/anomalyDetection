#!/usr/bin/env python

"""
Read a bunch of EKG data, chop out windows and cluster the windows. Then
reconstruct the signal and figure out the error.
"""

import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import struct

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def read_data(input_file):
    #    Read the data from the given file.
    
    with open(input_file, 'rb') as input_file:
        data_raw = input_file.read()
    n_bytes = len(data_raw)
    n_shorts = n_bytes/2
    # data is stored as 16-bit samples, little-endian
    # '<': little-endian
    # 'h': short
    unpack_string = '<%dh' % n_shorts
    # sklearn seems to break if data not in float format
    data_shorts = np.array(struct.unpack(unpack_string, data_raw)).astype(float)
    return data_shorts

def plot_data(data,reconstruction,error, n_plot_samples):
    # Plot the data from the given file .
    
    plt.figure()
    plt.plot(data[0:n_plot_samples], label="Original data")
    plt.plot(reconstruction[0:n_plot_samples], label="Reconstructed data")
    plt.plot(error[0:n_plot_samples], label="Reconstruction error")
    plt.legend()
    plt.show()

def sliding_chunker(data, window_len, slide_len):
    # Split a list into a series of sub-lists, each sub-list window_len long,
    # sliding along by slide_len each time. If the list doesn't have enough
    # elements for the final sub-list to be window_len long, the remaining data
    # will be dropped.

    chunks = []
    for pos in range(0, len(data), slide_len):
        chunk = np.copy(data[pos:pos+window_len])
        if len(chunk) != window_len:
            continue
        chunks.append(chunk)

    return chunks

def get_windowed_segments(data, window):
    #     Populate a list of all segments seen in the input data.  Apply a window to
    #     each segment so that they can be added together even if slightly
    #     overlapping, enabling later reconstruction.
    
    step = 2
    windowed_segments = []
    segments = sliding_chunker(
        data,
        window_len=len(window),
        slide_len=step
    )
    for segment in segments:
        segment *= window
        windowed_segments.append(segment)
    return windowed_segments


def reconstruct(data, window, clusterer):
    #    Reconstruct the given data using the cluster centers from the given clusterer.

    window_len = len(window)
    slide_len = window_len//2
    segments = sliding_chunker(data, window_len, slide_len)
    reconstructed_data = np.zeros(len(data))
    for segment_n, segment in enumerate(segments):
        # window the segment so that we can find it in our clusters which were
        # formed from windowed data
        segment *= window
        nearest_match_idx = clusterer.predict(segment)[0]
        nearest_match = np.copy(clusterer.cluster_centers_[nearest_match_idx])

        pos = segment_n * slide_len
        reconstructed_data[pos:pos+window_len] += nearest_match

    return reconstructed_data

def main():

    WINDOW_LEN = 32
    n_samples = 1000
    print("Reading data...")
    data = read_data('a02.dat')[0:n_samples]

    window_rads = np.linspace(0, np.pi, WINDOW_LEN)
    window = np.sin(window_rads)**2
    print("Windowing data...")
    windowed_segments = get_windowed_segments(data, window)

    print("Clustering...")
    clusterer = KMeans(n_clusters=150)
    clusterer.fit(windowed_segments)

    # Anomalus data is generated by zeroing a part of signal
    data_anomalous = np.copy(data)
    data_anomalous[210:215] = 0

    print("Reconstructing anomalus data...")
    reconstruction = reconstruct(data_anomalous, window, clusterer)
    error = np.absolute(reconstruction- data_anomalous)
    error_98th_percentile = np.percentile(error, 98)
    print("Maximum reconstruction error was %.1f at %d" % (error.max(), np.where(error==error.max())[0]))
    print("98th percentile of reconstruction error was %.1f" % error_98th_percentile)

    print("Plotting...")
    
    n_plot_samples=300
    plot_data(data_anomalous,reconstruction,error, n_plot_samples)


main()
