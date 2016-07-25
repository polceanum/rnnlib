#!/usr/bin/env python2

import netcdf_helpers
from scipy import *
from optparse import OptionParser
import sys
import os
import re

import cv2
import numpy as np

#command line options
parser = OptionParser()

#parse command line options
(options, args) = parser.parse_args()
if (len(args)<2):
    print "usage: -options input_filename output_filename line_height max_space"
    print options
    sys.exit(2)

inputFilename = args [0]
ncFilename = args[1]
line_height = int(args[2])
print options
print "input filename", inputFilename
print "data filename", ncFilename
print "line height", line_height
seqDims = []
seqLengths = []
targetStrings = []
wordTargetStrings = []
seqTags = []
inputs = []
predictions = []
predSeqLengths = []
targetSeqDims = []
print "reading data files"

for dir in os.listdir(inputFilename):
    folder = os.path.join(inputFilename, dir.strip())
    if os.path.isdir(folder):
        for file in os.listdir(folder):
            image_file = os.path.join(folder, file)
            image = cv2.imread(image_file, cv2.IMREAD_COLOR)
            if image is not None:
                seqTags.append(folder)
                wordTargetStrings.append(' ')
                seqTxt = file.split(".")[0].split("-")[-1]
                targetStrings.append(seqTxt)
                oldlen = len(inputs)
                oldlenPred = len(predictions)
# IMAGE PROCESSING PART
                aspect = float(line_height) / float(image.shape[0])
                dim = (int(aspect * image.shape[1]), line_height)
                if aspect < 1:
                    # Shrinking should be done using INTER_AREA interpolation
                    image = cv2.resize(image, dim, image, cv2.INTER_AREA)
                else:
                    # Scaling can be done using INTER_LINEAR interpolation
                    image = cv2.resize(image, dim, image, cv2.INTER_LINEAR)

                # Convert type
                image = image.astype(np.float32)
                #print "new shape:", image.shape

                inputs.append(np.zeros((3*line_height), dtype=np.float32))
                for col in range(image.shape[1]):
                    last_col = image[:, col].flatten()
                    # Normalize to range [0,1]
                    last_col /= 255
                    inputs.append(last_col)
                predictions.extend(inputs[oldlen+1:])
                predictions.append(np.zeros((3*line_height), dtype=np.float32))
                #print len(inputs)
                #print len(predictions)
                #print("delta", len(inputs) - oldlen)
                seqLengths.append(len(inputs) - oldlen)
                predSeqLengths.append(len(predictions) - oldlenPred)
                seqDims.append([seqLengths[-1]])
                targetSeqDims.append([predSeqLengths[-1]])

# #create a new .nc file
print ("open file %s", ncFilename)
#file = netcdf_helpers.NetCDFFile(ncFilename, "wl")
file = netcdf_helpers.Dataset(ncFilename, "w")

#create the dimensions
netcdf_helpers.createNcDim(file,'numSeqs',len(seqLengths))
netcdf_helpers.createNcDim(file,'numTimesteps',len(inputs))
netcdf_helpers.createNcDim(file,'predNumTimesteps',len(predictions))
netcdf_helpers.createNcDim(file,'inputPattSize',len(inputs[0]))
netcdf_helpers.createNcDim(file,'numDims',1)

#create the variables
netcdf_helpers.createNcStrings(file,'seqTags',seqTags,('numSeqs','maxSeqTagLength'),'sequence tags')
netcdf_helpers.createNcStrings(file,'targetStrings',targetStrings,('numSeqs','maxTargStringLength'),'target strings')
netcdf_helpers.createNcStrings(file,'wordTargetStrings',wordTargetStrings,('numSeqs','maxWordTargStringLength'),'word target strings')
netcdf_helpers.createNcVar(file,'seqLengths',seqLengths,'i',('numSeqs',),'sequence lengths')
netcdf_helpers.createNcVar(file,'seqDims',seqDims,'i',('numSeqs','numDims'),'sequence dimensions')
netcdf_helpers.createNcVar(file,'inputs',inputs,'f',('numTimesteps','inputPattSize'),'input patterns')
netcdf_helpers.createNcVar(file,'predSeqLengths', predSeqLengths,'i',('numSeqs',),'pred sequence lengths')
netcdf_helpers.createNcVar(file,'targetSeqDims', targetSeqDims,'i',('numSeqs','numDims'),'pred sequence dimensions')
netcdf_helpers.createNcVar(file,'targetPatterns', predictions,'f',('predNumTimesteps','inputPattSize'),'prediction patterns')

#write the data to disk
print "closing file", ncFilename
file.close()
