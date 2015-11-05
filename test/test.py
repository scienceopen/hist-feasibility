#!/usr/bin/env python3
"""
Registration case for HiST program
Michael Hirsch

To generate registration.h5 (only when making a new type of sim or real) type
python
"""
from __future__ import division,absolute_import
from pathlib2 import Path
from numpy.testing import assert_allclose
from sys import argv
import h5py
from tempfile import gettempdir
#from os import devnull
#
from histfeas.main_hist import doSim



def hist_registration(regh5,regXLS):
    Phi0,Phifit =doSim(ParamFN=regXLS,
                  makeplot=['fwd','optim'],
                  timeInds=None,
                  overrides = None, #{'minev': minev,'filter':filt, 'fwdguess':fwdguess, 'fitm':fitm,'cam':cam,'camx':acx,'ell':ell,'Jfwd':influx},
                  progms = gettempdir(),
                  x1d=[None],
                  vlim = {'p':[None]*6,'j':[None]*2,'b':[None]*2},
                  animtime=None,
                  cmd = ' '.join(argv),
                  verbose=0
                  )

    return Phi0,Phifit

def readCheck(Phi0,Phifit):
    with h5py.File(str(regh5),'r',libver='latest') as f:
        assert_allclose(f['/phifwd/phi'],Phi0[...,0])
        # noise makes inversion result differ uniquely each run
        xerrpct=(f['/phifwd/x0'] - Phifit[0]['gx0']) / f['/phifwd/x0'] * 100
        xmsg = 'x0 estimation error [km] {:.1f} %'.format(xerrpct[0])
        assert_allclose(f['/phifwd/x0'],Phifit[0]['gx0'],rtol=0.35,err_msg=xmsg)

        Eerrpct = (f['/phifwd/E0'] - Phifit[0]['gE0']) / f['/phifwd/E0'] * 100
        Emsg = 'E0 estimation error [eV] {:.1f} %'.format(Eerrpct[0])
        assert_allclose(f['/phifwd/E0'],Phifit[0]['gE0'],rtol=0.35,err_msg=Emsg)

        #the str() are needed instead of format() !
        print(xmsg)
        print(Emsg)



def writeout(regh5):
    with h5py.File(regh5,'a',libver='latest') as f:
        f['/phifwd/E0'] = 7500.
        f['/phifwd/x0'] = 1.

if __name__ == '__main__':
#%% simulation only
    tdir  = Path(__file__).parent
    regh5 = tdir / 'registration.h5'
    regXLS= tdir / 'registration.xlsx'

    Phi0,Phifit=hist_registration(regh5,regXLS)
    readCheck(Phi0,Phifit)
    print('OK:  simultation registration case')
#%% real data