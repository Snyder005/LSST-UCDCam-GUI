#!/usr/bin/python

# Plots stability of a set of bias frames vs time

import matplotlib
matplotlib.use("Agg")
import pyfits as pf
from pylab import *
import sys, glob

patterns = ['testdata_26Jun/114-04_dark_bias_3*', 'testdata/114-04_dark_bias_9*']
dates=['26Jun', '29Jun']
xaxis = [1,2]
xmin = 100
xmax = 400
ymin = 100
ymax = 1900
numsegments = 16
numdirs = len(patterns)


means = zeros([numdirs, numsegments])
stds = zeros([numdirs, numsegments])
segnames = {}
truncated_data = zeros([ymax-ymin, xmax-xmin])

for counter,pattern in enumerate(patterns):
    files = sort(glob.glob(pattern))
    for segment in range(numsegments):
        numfiles = 0
        for filename in files:
            numfiles += 1
            hdulist = pf.open(filename, mode='readonly', do_not_scale_image_data=True)
            imhdr=hdulist[segment+1].header
            extname = imhdr['EXTNAME']
            segnames[str(segment)] = extname

            data = array(hdulist[segment+1].data + 32768, dtype = int32)
            overscan = data[2005:2021,:].sum(axis=0) / 16.0
            data = clip(data-overscan, 0, 65536)
            truncated_data += data[ymin:ymax, xmin:xmax]

        truncated_data /= numfiles
        mean = truncated_data.mean()
        std = truncated_data.std()
        means[counter,segment] = mean
        stds[counter,segment] = std
        print "for date %s, segment = %s, mean = %.2f, std = %.2f"%(dates[counter],segnames[str(segment)], mean,std)

figure()
suptitle("Bias frame stability", fontsize=18)
subplots_adjust(hspace = 0.4)
for segment in range(numsegments):

    subplot(4,4,segment+1)
    title(segnames[str(segment)], fontsize=9)
    (_, caps, _) = errorbar(xaxis, means[:,segment], yerr=stds[:,segment], label = segnames[str(segment)],fmt='--o', capsize=5, lw = 2, mew = 2)

    for cap in caps:
        cap.set_markeredgewidth=2

    xticks(xaxis,dates, fontsize = 9)
    ylim(0.0, 25.0)
    xlim(0,3)

savefig("bias_stability.png")

