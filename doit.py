# Robert J. Brunner
#
# Date: January 5, 2014
#
# Note I modifed the lenses.csv file compiled by Sean after downloading it.
# sed 's/",//g' lenses.csv | sed 's/"//g' > a ; mv a lenses.csv
# This strips out the " characters and extra commas.
# I also added a '#' character at the start of line 1 to indicate it is a 
# header line.
#
# This code is run like
# python doit.py lenses.csv data
# where lenses.csv is a CSV file containing the objid, rz, dec of known lenses.
# data is a directory containing fits file images that might contain the known lens.
#

import numpy
from astropy import wcs
from astropy.io import fits
import sys
import os

if __name__ == '__main__':
    
    delta = 25 # THe half width/height of our cutout images (50x50)
    
    # First we read csv file of known lens candidates
    # Coords is a list of ra/dec lists.
    
    coords = []
    with open(sys.argv[1]) as listfile:
        for lens in listfile:
            if '#' in lens:
                continue
            
            # We pull out the three columns, and convert to float value.
            id, ra, dec = map(float, lens.split(','))
            coords.append([ra, dec])

    # We will want a numpy array for simplicity.

    lensArray = numpy.array(coords, numpy.float_)
    
    # Second we build list of fits files to search
    
    fFileList = []
    
    # We walk the directory to find all fits files to search.
    # We save the full file pathname.
    
    for root, dirs, files in os.walk(sys.argv[2]):
        for file in files:
            if file.endswith('.fits'):
                fFileList.append(os.path.join(root, file))

    # print fFileList
    
    # Now loop through fits files.
    
    for file in fFileList:

        with fits.open(file) as hdulist:
            
            # Grab WCS and data
            
            w = wcs.WCS(hdulist[0].header)
            d = hdulist[0].data
            
            # Note fits files have fastest index second (so x is columns)
            (yMax,xMax) = map(int, d.shape)
            
            # We convert lens list from Ra/Dec to pixels in this image. 
            # Note most lenses will lie outside image boundaries, 
            # so if we check to see if lens is inside image, we know
            # if we have a lens in the image.

            lensPixels = w.wcs_world2pix(lensArray, 0)
            
            # This variable is ismply used to name the output fits file. 
            # Since we will crash if we try to overwrite an existing file, 
            # this is a simple error check for duplicate lenses.
            index = 1
            
            # Now loop over known lenses to look for them in current image
            for lens in lensPixels:
                if lens[0] >= 0.0 and lens[0] < xMax:
                    if lens[1] >= 0.0 and lens[1] < yMax:
                        
                        # We have a lens, so make the cutout
                        xl = int(lens[0] - delta) ; xh = xl + 2 * delta
                        yl = int(lens[1] - delta) ; yh = yl + 2 * delta
                        
                        print lens, xl, xh, yl, yh
                        
                        # Now save the new image.
                        # Right now we do not export WVS, this should be fixed.
                        # We could also export more SDSS header info
                        # Finally, the lens fits filename is rather simple.
                        # Probebaly need to fix this to handl g, r, or i band data
                        
                        subHDU = fits.PrimaryHDU(d[yl:yh, xl:xh])
                        subHDU.writeto("lens-" + str(index) + '.fits')

                index += 1
