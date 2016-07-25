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
    print "usage: -options input_filename output_filename line_height max_space"
    print options
    sys.exit(2)

inputFilename = args [0]
ncFilename = args[1]
line_height = int(args[2])
max_space = int(args[3])
print options
print "input filename", inputFilename
print "data filename", ncFilename
print "line height", line_height
print "max space", max_space
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
cv2.namedWindow("asdf")

for l in file(inputFilename).readlines():
    inkmlfile = l.strip()
    if len(inkmlfile):
        seqTags.append(inkmlfile)
        wordTargetStrings.append(' ')
        seqTxt = GetTargetString(inkmlfile)
        targetStrings.append(seqTxt)
        oldlen = len(inputs)
        oldlenPred = len(predictions)
# IMAGE PROCESSING PART
        image = cv2.imread(inkmlfile, cv2.IMREAD_GRAYSCALE)
        th, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        left = -1
        right = -1
        top = -1
        bottom = -1

        for row in range(image.shape[0]):
            if np.any(image[row, :]) and top < 0:
                top = row
            if np.any(image[image.shape[0] - row - 1, :]) and bottom < 0:
                bottom = image.shape[0] - row - 1
            if top > -1 and bottom > -1:
                break

        for col in range(image.shape[1]):
            if np.any(image[:, col]) and left < 0:
                left = col
            if np.any(image[:, image.shape[1] - col - 1]) and right < 0:
                right = image.shape[1] - col - 1
            if left > -1 and right > -1:
                break

        # print "Left: ", left, " Right: ", right
        # print "Top: ", top, " Bottom: ", bottom

        image = image[top:bottom, left:right]

        aspect = float(line_height) / float(image.shape[0])
        dim = (int(aspect * image.shape[1]), line_height)
        if aspect < 1:
            # Shrinking should be done using INTER_AREA interpolation
            image = cv2.resize(image, dim, cv2.INTER_AREA)
        else:
            # Scaling can be done using INTER_LINEAR interpolation
            image = cv2.resize(image, dim, cv2.INTER_LINEAR)

        # cv2.imshow("asdf", image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        last_non_zero = 0
        skipped = 0
        non_skipped = 0
        inputs.append(np.zeros(line_height, np.uint8))
        for col in range(image.shape[1]):
            last_col = image[:, col]
            if np.any(last_col):
                last_non_zero = 0
                inputs.append(last_col)
                non_skipped += 1
            else:
                last_non_zero += 1
                # Hard threshold whitespaces
                if last_non_zero > max_space:
                    skipped += 1
                    continue
                else:
                    inputs.append(last_col)
                    non_skipped += 1
        # print("skipped:", skipped)
        # print("non skipped:", non_skipped)
        predictions.extend(inputs[oldlen+1:])
        predictions.append(np.zeros(line_height, dtype=np.uint8))
        # print len(inputs)
        # print len(predictions)
        # print("delta", len(inputs) - oldlen)
        seqLengths.append(len(inputs) - oldlen)
        predSeqLengths.append(len(predictions) - oldlenPred)
        seqDims.append([seqLengths[-1]])
        targetSeqDims.append([predSeqLengths[-1]])


# firstIx = 0
# for i in range(len(seqLengths)):
#         for k in reversed(range(seqLengths[i])):
#                 if k > 0:
#                         inputs[firstIx + k] = array(inputs[firstIx + k]) - array(inputs[firstIx + k - 1])
#                         inputs[firstIx + k][-1] = abs(inputs[firstIx + k][-1])
#                         predictions[firstIx + k - 1 ] = inputs[firstIx + k]
#                 if k == 0:
#                         predictions[firstIx] = inputs[firstIx+1]
#         inputs[firstIx] = np.zeros(line_height, dtype=uint8)
#         firstIx += seqLengths[i]

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
