from __future__ import print_function,division
from time import time
from numpy import arange, empty, asarray, uint16, rot90, fliplr, flipud
from dateutil import parser
from dateutil.relativedelta import relativedelta
from os.path import expanduser,join
import calendar
from scipy.interpolate import interp1d
# local
import histutils.getRawInd as gri
import histutils.rawDMCreader as rdr
from get1Dcut import get1Dcut

#this contains function for loading HST data
# michael hirsch 2014, ported from Matlab code

#INPUT FILE FORMAT: intended for use with "DMCdata" raw format, 4-byte
# "footer" containing frame index (must use typecast)

def getSimulData(sim,cam,makeplot,progms,dbglvl=0):
#%% synchronize
    cam,sim = HSTsync(sim,cam,dbglvl)
#%% load 1-D cut slices into keogram array
    cam,rawdata = HSTframeHandler(sim,cam,makeplot,progms,dbglvl)
    return cam,rawdata,sim

def HSTsync(sim,cam,dbglvl):

    reqStart = parser.parse(sim.startutc)
    reqStop = parser.parse(sim.stoputc)

#%% get more parameters per used camera (candidate for class def)
    for c in cam.keys():
        # data file name
        cam[c].fnStemCam = expanduser(join(sim.realdatapath, cam[c].fn))
        # parameters for this camera
        finf = rdr.getDMCparam(cam[c].fnStemCam,
                                 (cam[c].xpix,cam[c].ypix),
                                 (cam[c].xbin,cam[c].ybin),
                                 None,verbose=-1)

        cam[c].ingestcamparam(finf)

        fullFileStartUT = parser.parse(cam[c].fullstart)
        #get start/end raw frame indices
        #FIXME is this silly? should be assigned in getDMCparam?
        cam[c].nHeadBytes = cam[c].BytesPerFrame - cam[c].PixelsPerImage * 16 // 8
        cam[c].BytesPerImage = cam[c].BytesPerFrame - cam[c].nHeadBytes

        (cam[c].firstFrameNum,
         cam[c].lastFrameNum ) = gri.getRawInd(cam[c].fnStemCam,
                                                cam[c].BytesPerImage,
                                                cam[c].nHeadBytes,
                                                cam[c].Nmetadata)

        #number of frames in file
        cam[c].nFrame = cam[c].lastFrameNum - cam[c].firstFrameNum + 1
        #start/stop frame times of THIS camera data file
        cam[c].startUT = fullFileStartUT + relativedelta(seconds= (cam[c].firstFrameNum - 1) * cam[c].kineticSec )
        cam[c].stopUT =  fullFileStartUT + relativedelta(seconds= (cam[c].lastFrameNum -  1) * cam[c].kineticSec )

        if cam[c].timeShiftSec != 0 and dbglvl >0:
            print(('HST1 Time Shifted by ' + str(cam[c].timeShiftSec) + ' seconds'))

        #FIXME check for off-by-one error
        basestart = fullFileStartUT + relativedelta(seconds=cam[c].timeShiftSec)  #in this order
        #now we create a vector of time deltas using list comprehension
        #FIXME check for off-by-one
        deltarange = arange(cam[c].firstFrameNum, cam[c].lastFrameNum+1) * cam[c].kineticSec
        cam[c].tCam = asarray([basestart + relativedelta(seconds = vx) for vx in deltarange])

        if dbglvl >0:
            print('Camera ' + c + ' start/stop UTC: ' + str(cam[c].startUT) +
              ' / ' + str(cam[c].stopUT) + ', ' + str(cam[c].nFrame) + ' frames.')

#%% determine mutual start/stop frame
# FIXME: assumes that all cameras overlap in time at least a little.
# FiXME: learn how to do this more efficently with Python class
# we will play only over UTC times for which both sites have frames available
    mutualStart = max( [cam[str(x)].startUT for x in sim.useCamInd] ) #who started last
    mutualStop =  min( [cam[str(x)].stopUT for x in sim.useCamInd] )   # who ended first
#%% make playback time steps
# based on the "simulated" UTC times that do not correspond exactly with either camera, necessarily.
#FIXME check for off-by-one
#FIXME there is probably a list comprehension way to do this
    alltReq = [mutualStart] #makes a list so we can append
    while alltReq[-1] < mutualStop:
        alltReq.append( alltReq[-1] + relativedelta(seconds=sim.kineticSec) )

    nMutRawFrame = len(alltReq)  # NOT alltReq.size--it's a list as it should be!

    print(nMutRawFrame, 'mutual frames available from',mutualStart,'to',mutualStop)

#%% adjust start/stop to user request
    alltReqAdj = asarray([t for t in alltReq if t>reqStart and t<reqStop ]) #keep greater than start time
    nMutSim = alltReqAdj.size
    if dbglvl > 0:
        print(('Per user specification, analyzing ' +str(nMutSim) + ' frames from ' +
          str(alltReqAdj[0]) + ' to ' + str(alltReqAdj[-1]) ))
#%% use *nearest neighbor* interpolation to find mutual frames to display.
#   sometimes one camera will have frames repeated, while the other camera
#   might skip some frames altogether
    alltReqUnix = asarray([calendar.timegm(t.utctimetuple()) + t.microsecond / 1.e6 for t in alltReqAdj ])


    for ci in sim.useCamInd.astype(str):
        #put current cam times into a temporary vector (sigh)
        tCamUnix = asarray([calendar.timegm(t.utctimetuple()) + t.microsecond / 1.e6 for t in cam[ci].tCam ])

        ft = interp1d(tCamUnix, arange(cam[ci].nFrame,dtype=int), kind='nearest')
        cam[ci].pbInd = ft(alltReqUnix).astype(int) #these are the indices for each time (the slower camera will use some frames twice in a row)


    sim.alltReq = alltReqAdj

    return cam,sim

def HSTframeHandler(sim,cam,makeplot,progms,dbglvl=0):

#%% load 1D cut coord
    cam = get1Dcut(cam,sim.useCamInd,makeplot,progms,dbglvl)

#%% use 1D cut coord
    if dbglvl>0: print('frameHandler: Loading and 1-D cutting data...',end='')
    tic = time()
    rawdata = {}
    for ci in sim.useCamInd.astype(str):
        nProcFrame = cam[ci].pbInd.size #should be the same for all cameras! FIXME add assert

        keo = empty( ( cam[ci].nCutPix, len(cam[ci].pbInd) ),dtype=uint16,order='F') #1-D cut data
        tKeo = empty( nProcFrame,dtype=object) #datetime of each frame
        #yes rawdata is order C!
        rawdata[ci] = empty( ( nProcFrame, cam[ci].SuperX, cam[ci].SuperY),
                             dtype=uint16,order='C')
        with open(cam[ci].fnStemCam, 'rb') as fid:
            finf = {'bytesperframe':cam[ci].BytesPerFrame,
                    'pixelsperimage':cam[ci].PixelsPerImage,
                    'nmetadata':cam[ci].Nmetadata,
                    'superx':cam[ci].SuperX,
                    'supery':cam[ci].SuperY
                    }

            for j,iFrm in enumerate(cam[ci].pbInd):

                #FIXME compare rawFrameInd with truly requested frame to catch off-by-one errors
                frame,rawFrameInd = rdr.getDMCframe(fid,iFrm,finf,verbose=-1)
                #print(frame.flags)
                #print(iFrm)
                if cam[ci].transpose:
                    frame = frame.T
                # rotate -- note if you use origin='lower', rotCCW -> rotCW !
                if cam[ci].rotCCW != 0:
                    frame = rot90(frame,k=cam[ci].rotCCW)
                # flip
                if cam[ci].flipLR:
                    frame = fliplr(frame)
                if cam[ci].flipUD:
                    frame = flipud(frame)
                # declare frame UTC time based on raw Index, start time, and kinetic rate
                tKeo[j] = ( cam[ci].startUT +
                           relativedelta(seconds= (rawFrameInd - cam[ci].firstFrameNum) * cam[ci].kineticSec ) +
                           relativedelta(seconds = cam[ci].timeShiftSec) )
                #%% do pixel cutting
                keo[:,j] = frame[cam[ci].cutrow,cam[ci].cutcol]
                #store raw frame for playback synchronized of raw video
                rawdata[ci][j,:,:] = frame

        #assign slice & time to class variables
        cam[ci].keo = keo
        cam[ci].tKeo = tKeo

    if dbglvl >0: print('DONE  in {:0.2f}'.format(time() - tic) + ' seconds.')
    return cam,rawdata

#def loadmatcut(matcutfn,useCamInd,cam):
#    #THIS FUNCTION NO LONGER USED
#    matData = scipy.io.loadmat(matcutfn) #one file for all cameras
#    for i,ci in zip(useCamInd,useCamInd.astype(str)):
#          #identify cut pixels for this camera
#        cam[ci].cutRow = (matData['Pix' + str(i+1)][0][0][1][:,1] - 1).astype(int) # -1 makes zero-indexed
#        cam[ci].cutCol = (matData['Pix' + str(i+1)][0][0][1][:,0] - 1).astype(int) # -1 makes zero-indexed
#        cam[ci].angle_deg =  matData['Pix' + str(i+1)][0][0][1][:,2]
#    return cam