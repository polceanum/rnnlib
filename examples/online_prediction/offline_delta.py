#!/usr/bin/env python2

import netcdf_helpers
from scipy import *
from optparse import OptionParser
import sys
import os
import re

import cv2
import numpy as np

def Std(array,axis):
	if shape(array)[axis]>1:
		return (std(array,axis))
	return array
def GetTargetString(strokeFileName):
         asciiFileName = re.sub('lineImages', 'ascii', strokeFileName)
         asciiFileName = re.sub('-[0-9]+\.tif', '.txt', asciiFileName)
         try:
                 lineNr = int(re.search('-([0-9]+)\.tif', strokeFileName).group(1))
                 lines = [line.strip() for line in open(asciiFileName)]
                 return lines[lineNr+lines.index('CSR:') + 1]
         except (AttributeError, IndexError) as e:
                 raise SystemExit
                 return ' '

#command line options
parser = OptionParser()

#parse command line options
(options, args) = parser.parse_args()
if (len(args)<2):
	print "usage: -options input_filename output_filename line_height"
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
for l in file(inputFilename).readlines():
	inkmlfile = l.strip()
	if len(inkmlfile):
		seqTags.append(inkmlfile)
                wordTargetStrings.append(' ')
                seqTxt = GetTargetString(inkmlfile)
                targetStrings.append(seqTxt)			
		oldlen = len(inputs)
                oldlenPred = len(predictions)
                firstCol = array([])
# IMAGE PROCESSING PART
                image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                aspect = 100 / image.shape[0]
                dim = (int(aspect * image.shape[1]), line_height)
                if aspect < 1:
                    # Shrinking should be done using INTER_AREA interpolation
                    image = cv2.resize(image, dim, cv2.INTER_AREA)
                else:
                    # Scaling can be done using INTER_LINEAR interpolation
                    image = cv2.resize(image, dim, cv2.INTER_LINEAR)

                th, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                for col in range(image.shape[1]):
                    last_col = image[:, col]
                    print last_col
                    if len(firstCoord) == 0: firstCoord = last
                    last = last - firstCoord
                    inputs.append(last)
                predictions.extend(inputs[oldlen+1:])
                predictions.append(np.zeros((line_height, 1), dtype=uint8))
		seqLengths.append(len(inputs) - oldlen)
		predSeqLengths.append(len(predictions) - oldlenPred)
		seqDims.append([seqLengths[-1]])
		targetSeqDims.append([predSeqLengths[-1]])


firstIx = 0
for i in range(len(seqLengths)):
        for k in reversed(range(seqLengths[i])):
                if k > 0:
                        inputs[firstIx + k] = array(inputs[firstIx + k]) - array(inputs[firstIx + k - 1])
                        inputs[firstIx + k][-1] = abs(inputs[firstIx + k][-1])
                        predictions[firstIx + k - 1 ] = inputs[firstIx + k]
                if k == 0:
                        predictions[firstIx] = inputs[firstIx+1]
        inputs[firstIx] = array([0, 0, 0])
        firstIx += seqLengths[i]


#create a new .nc file
print ("open file %s", ncFilename)
file = netcdf_helpers.NetCDFFile(ncFilename, 'w')

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
