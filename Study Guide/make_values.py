"""Refresh worked-example values from V7, then compile study_guide.tex with latexmk."""
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from aircraft import C172, CL3500
from atmosphere import isa, sigma, speed_of_sound, G0_MPS2
from takeoff import takeoff
from landing import landing
from bfl import balanced_field
from segments import make_conditions
from units import m_to_ft, mps_to_kt, ft_to_m
from airports import KICT
from runway_analysis import analyze_runway
values={}
def add(key,value,places=2):values[key]=f'{value:,.{places}f}'
cond=make_conditions(C172,C172.mtow_kg)
to=takeoff(C172);ld=landing(C172,use_reverse=False)
for key,value in [('mass',cond.mass_kg),('weight',cond.weight_n),('rho',cond.rho_kg_m3),('sound',speed_of_sound(0)),('vs',to['vs1_mps']),('vr',to['vr_mps']),('vtwo',to['v2_mps'])]:add(key,value,6 if key=='rho' else 2)
q=.5*cond.rho_kg_m3*to['vr_mps']**2
lift=C172.lift(to['vr_mps'],cond.rho_kg_m3,C172.cl_gnd)
drag=C172.drag(to['vr_mps'],cond.rho_kg_m3,C172.cl_gnd)
thrust=C172.thrust(to['vr_mps'])
friction=C172.mu_roll*(cond.weight_n-lift)
for key,value in [('q',q),('lift',lift),('drag',drag),('thrust',thrust),('friction',friction),('accel',(thrust-drag-friction)/cond.mass_kg),('vrkt',mps_to_kt(to['vr_mps'])),('rot',to['vr_mps']*C172.ROTATION_S),('roll',to['ground_roll_m']),('rolltime',to['ground_roll_s']),('air',to['air_dist_m']),('tod',to['tod_m']),('todft',m_to_ft(to['tod_m'])),('grad',to['climb_grad_pct']),('ldair',ld['air_dist_m']),('free',ld['free_roll_m']),('brake',ld['braking_roll_m']),('ld',ld['ld_m']),('ldft',m_to_ft(ld['ld_m'])),('vref',ld['vref_mps']),('vtd',ld['vtd_mps'])]:add(key,value)
for key,value in [('tempFive',isa(ft_to_m(5000),20)[0]),('pressFive',isa(ft_to_m(5000),20)[1]),('rhoFive',isa(ft_to_m(5000),20)[2]),('sigmaFive',sigma(ft_to_m(5000),20))]:add(key,value,4 if 'rho' in key or 'sigma' in key else 2)
jet=balanced_field(CL3500,n_curve_points=2)
for key,value in [('jetvone',mps_to_kt(jet['v1_mps'])),('jetvr',mps_to_kt(jet['vr_mps'])),('jetbfl',m_to_ft(jet['bfl_m'])),('jetgo',m_to_ft(jet['todg_oei_m'])),('jetstop',m_to_ft(jet['asd_m'])),('jetaeo',m_to_ft(jet['tod_aeo_m'])),('jetfact',m_to_ft(jet['tod_aeo_factored_m'])),('jettofl',m_to_ft(jet['tofl_m']))]:add(key,value)
r=analyze_runway(CL3500,KICT,KICT.runway('01L'),oat_c=30,wind_dir_deg=20,wind_kt=10)
for key,value in [('kictisa',r['isa_dev_c']),('kictwind',r['hw_perf_kt']),('kicttofl',m_to_ft(r['tod_req_m'])),('kictasd',m_to_ft(r['asd_req_m'])),('kictldr',m_to_ft(r['landing_checks'][0][1])),('kictmargin',m_to_ft(r['landing_checks'][0][3]-r['landing_checks'][0][1]))]:add(key,value)
(ROOT/'values.tex').write_text('% Calculated from V7 by make_values.py.\n'+''.join(r'\expandafter\def\csname value'+k+r'\endcsname{'+v+'}\n' for k,v in values.items()))
print('Calculated',len(values),'worked-example values from V7.')
