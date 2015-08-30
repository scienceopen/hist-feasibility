#!/usr/bin/env python3
"""
A collection of models and parameterizations for differential number flux,
typically taken in the collisonless region "above the top of the ionosphere"
as is commonly stated.
"""
from __future__ import division,absolute_import
from numpy import gradient, exp, logspace, asarray, atleast_1d
from matplotlib.pyplot import figure,show

def EllisonRamaty(E,E0,gamma,kappa,C0):
    E,E0,gamma,kappa,C0 = dimhandler(E,E0,gamma,kappa,C0)
#%% do work
    return C0 * E[:,None]**(-gamma) * exp(-((E[:,None]-E0)/gradient(E)[:,None])**kappa)

def dimhandler(E,E0,gamma,kappa,C0=None):
#%% lite input validation
    E = asarray(E); E0 = atleast_1d(E0); gamma = atleast_1d(gamma); kappa = atleast_1d(kappa)
    C0 = atleast_1d(C0)
    if E.ndim !=1 or E0.ndim != 1 or gamma.ndim !=1 or kappa.ndim!=1 or C0.ndim!=1:
        print('E0, gamma, kappa, C0 must be scalar or vector. E must be vector'); return None
    return E,E0,gamma,kappa,C0

def plotdnf(E,phi,E0,gamma,kappa):
    E,E0,gamma,kappa = dimhandler(E,E0,gamma,kappa)[:4]

    if gamma.size>1:
        labels = map(str,gamma)
    elif kappa.size>1:
        labels = map(str,kappa)
    else:
        labels = map(str,E0)

    ax = figure().gca()
    lines = ax.loglog(E,phi,marker='*')
    ax.set_xlabel("Particle beam energy [eV]")
    ax.set_ylabel("Flux [cm$^{-2}$s$^{-1}$eV$^{-1}$sr$^{-1}$]")
    ax.tick_params(axis='both', which='major', labelsize='large')
    ax.grid(True)
    ax.legend(lines,labels,loc='best')

if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser(description="differential number flux parameterizations")
    p.add_argument('E0',help='characteristic energy [eV]',nargs='+',type=float)
    p.add_argument('-g','--gamma',help='gamma parameter',nargs='+',type=float,default=-1)
    p.add_argument('-k','--kappa',help='kappa parameter',nargs='+',type=float,default=1)
    p.add_argument('-c','--C0',help='scaling constant',type=float,default=1)
    p = p.parse_args()

    E = logspace(1.7,4.5,num=33,base=10)

    phi =  EllisonRamaty(E,p.E0,p.gamma,p.kappa,p.C0)

    plotdnf(E,phi,p.E0,p.gamma,p.kappa)
    show()