import pandas as pd
import numpy as np

from fluids import *
from scipy.constants import *
from fluids.control_valve import size_control_valve_l
from thermo.chemical import Chemical

list_fluids = ['nitrogen', 'octane', 'water', 'oxygen', 'argon']

for item in list_fluids :
    element = Chemical(item)
    print (element)
    print(element.phase_STP)
    print(element.phase_ref)
    print(element.rho)
    print(element.mu)
    print(element.Pc)
    print(element.Tc)


#how to manage liquid vs gas on sizing Cv

#liquid ? 

size_control_valve_l

#gas ? 

# def size_control_valve_g(T, MW, mu, gamma, Z, P1, P2, Q, D1=None, D2=None, 
#                          d=None, FL=0.9, Fd=1, xT=0.7, allow_choked=True, 
#                          allow_laminar=True, full_output=False):

T = 290 # K
MW = element.MW # [g/mol]
viscosity = element.mug # [Pa*s]
heat_cap = element.Cpg # - 
compres_factor = element.Zg # - 
P1 = 5 #Pascal 
P2 = 1 # Pascal
Q = 0.5 
#  Volumetric flow rate of the gas at *273.15 K* and 1 atm specifically [m^3/s]

print('parameters for sizing')
print(MW)
print(viscosity)
print(heat_cap)
print(compres_factor)
sizing = size_control_valve_g(T=T, MW = MW, mu=viscosity, gamma = heat_cap, Z = compres_factor, P1=P1, P2=P2, Q=Q, full_output=True)
print( 'Cv: ', Kv_to_Cv(sizing['Kv'] ))
print( 'xTP: ', sizing['xTP'])
