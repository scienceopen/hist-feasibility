#!/usr/bin/env python3
"""
Figure flaming generated by HiST program
Michael Hirsch
"""
from __future__ import division,absolute_import
from sys import argv
from matplotlib.pyplot import show
#
import seaborn as sns
sns.color_palette("cubehelix")
sns.set(context='paper', style='whitegrid',font_scale=2,
        rc={'image.cmap': 'cubehelix_r'})
#
from histfeas.main_hist import doSim
from histfeas.loadAnalyze import readresults,findxlsh5

def hist_figure():
    Phi0,Phifit =doSim(ParamFN=regXLS,
                  makeplot=['fwd','optim','png','h5'],
                  timeInds=timeInds,
                  overrides = overrides, #{'minev': minev,'filter':filt, 'fwdguess':fwdguess,
				                    #'fitm':fitm,'cam':cam,'camx':acx,'ell':ell,'Jfwd':influx},
                  progms = outdir,
                  x1d=x1d,
                  vlim = vlim,
                  animtime=None,
                  cmd = ' '.join(argv),
                  verbose=0
                  )

    return Phi0,Phifit


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser(description='flaming figure plotter')
    p.add_argument('--load',help='load without recomputing',action='store_true')
    p.add_argument('-m','--makeplot',help='plots to make',default=[],nargs='+')
    p.add_argument('-v','--verbose',help='verbosity',action='count',default=0)
    p.add_argument('--ell',help='compute projection matrix',action='store_true')
    p.add_argument('-f','--frames',help='time steps to use',type=int,default=(1,3))
    p = p.parse_args()

    regXLS='in/2cam_flame.xlsx'
    timeInds=p.frames
    outdir='out/rev2_flame2'
    x1d = [1,1,1]
    vlim = {'p':[-1.5,4.5,90,300,5e7,8e8,5e7,2e9], 'j':[1e3,1.1e5, 1e3,8e5],
            'b':[0,1.5e3]}
    overrides = {'ell':p.ell}

    if not p.load:
        print('running Hist program -- will write png and h5 to ' + outdir)
        Phi0,Phifit=hist_figure()


    h5list,xlsfn = findxlsh5(outdir)
    readresults(h5list,xlsfn,vlim,x1d,overrides,p.makeplot,p.verbose)

    if 'show' in p.makeplot:
        show()