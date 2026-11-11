"""Publication figures and high-resolution formula images from saved model outputs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
from prepare_data import OUT, INPUTS, DATA

FIG=OUT/'figures'
NAVY='#19384B'; BLUE='#347594'; LIGHT='#9FBFCC'; ORANGE='#C87537'; GREY='#647580'


def save(fig,name):
    fig.savefig(FIG/f'{name}.png',dpi=260,bbox_inches='tight',facecolor='white')
    fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight',facecolor='white')
    plt.close(fig)


def formula(name,lines):
    height=.52*len(lines)
    fig=plt.figure(figsize=(7,max(height,.55)))
    for k,line in enumerate(lines):
        fig.text(.5,1-(k+.5)/len(lines),line,ha='center',va='center',fontsize=17,color=NAVY)
    save(fig,name)


def main(core_only=False):
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.labelcolor':NAVY,'text.color':NAVY,
                         'axes.titleweight':'bold','axes.titlesize':11,'grid.alpha':.2})
    s=pd.read_csv(OUT/'runs/base/site_decisions.csv')
    supply=pd.read_csv(INPUTS/'existing_supply.csv')
    boundary=json.loads((DATA/'05_geospatial_boundaries/URA_MP2019_planning_area_boundary.geojson').read_text())['features']
    tr=Transformer.from_crs(4326,3414,always_xy=True)
    fig,axs=plt.subplots(1,2,figsize=(9,4.1),layout='constrained')
    for ax in axs:
        for f in boundary:
            g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
            for poly in polys:
                xy=np.array(poly[0]);x,y=tr.transform(xy[:,0],xy[:,1]);ax.fill(np.array(x)/1000,np.array(y)/1000,facecolor='#F1F3F4',edgecolor='#CFD7DB',lw=.3)
        ax.set_xlim(s.x_coord.min()/1000-1,s.x_coord.max()/1000+1)
        ax.set_ylim(s.y_coord.min()/1000-1,s.y_coord.max()/1000+1)
        ax.set_aspect('equal');ax.set_xlabel('SVY21 easting (km)');ax.grid(False)
    hit=supply.strict_points.gt(0)
    axs[0].scatter(s.x_coord[hit]/1000,s.y_coord[hit]/1000,s=5+1.5*supply.strict_points[hit],c=BLUE,alpha=.6,lw=0)
    axs[0].set_title('Existing address-supported points')
    hit=s.ac_additions.gt(0)
    axs[1].scatter(s.x_coord/1000,s.y_coord/1000,s=2,c='#CAD3D8',lw=0)
    axs[1].scatter(s.x_coord[hit]/1000,s.y_coord[hit]/1000,s=6+2*s.ac_additions[hit],c=ORANGE,alpha=.8,lw=0)
    axs[1].set_title('Additional AC points at base budget')
    axs[0].set_ylabel('SVY21 northing (km)')
    save(fig,'placement_map')
    f=pd.read_csv(OUT/'budget_frontier.csv')
    c=pd.read_csv(OUT/'baseline_comparison.csv')
    fig,ax=plt.subplots(figsize=(7.7,3.8),layout='constrained')
    ax.plot(f.capital/1e6,100*f.service_fraction,'o-',color=NAVY,label='MILP, actual spend')
    for name,color,marker in [('equal',GREY,'s'),('proportional',BLUE,'^'),('greedy',ORANGE,'D')]:
        r=c[c.name.eq(name)].iloc[0]
        ax.scatter(r.capital/1e6,100*r.service_fraction,c=color,marker=marker,s=55,label=name.capitalize(),zorder=5)
    ax.axhline(90,color='#AAB8BF',ls='--',lw=1)
    ax.set(xlabel='Infrastructure capital expenditure (S$ million)',ylabel='Modelled demand served (%)')
    ax.legend(frameon=False,fontsize=9,loc='lower right');ax.grid(axis='y')
    save(fig,'budget_frontier')
    names=['no_build','equal','proportional','greedy','base']
    d=c.set_index('name').loc[names]
    fig,ax=plt.subplots(figsize=(7.7,3.2),layout='constrained')
    bars=ax.barh(['Existing only','Equal allocation','Proportional','Greedy','MILP'],100*d.service_fraction,color=[LIGHT, GREY,BLUE,ORANGE,NAVY])
    for bar,val in zip(bars,d.service_fraction):
        ax.text(val*100+1,bar.get_y()+bar.get_height()/2,f'{val*100:.1f}%',va='center')
    ax.set_xlim(0,105);ax.invert_yaxis();ax.set_xlabel('Modelled demand served (%)');ax.grid(axis='x')
    save(fig,'comparators')
    if core_only:
        print('Core figures saved to',FIG)
        return
    v=pd.read_csv(OUT/'sensitivity.csv').set_index('name')
    choices=['joint_high','self_site_only','hours_4','hdb_share_55','capex_10000','headroom_148','base','broad_supply','hours_8','radius_800']
    labels=['Joint high-demand/cost','Only own carpark','4 effective hours','55% HDB EV share','S$10,000 per AC point','14.8 kW spare power','Base assumptions','Broader supply matches','8 effective hours','800 m catchment']
    base=json.loads((OUT/'runs/base/metrics.json').read_text())
    rows=[{'service_fraction':base['service_fraction'],'fixed_fraction':base['service_fraction']} if x=='base' else v.loc[x] for x in choices]
    fig,ax=plt.subplots(figsize=(8,4.7),layout='constrained')
    yy=np.arange(len(rows))
    ax.barh(yy-.17,[100*r['fixed_fraction'] for r in rows],height=.30,color=LIGHT,label='Base investment held fixed*')
    ax.barh(yy+.17,[100*r['service_fraction'] for r in rows],height=.30,color=NAVY,label='Reoptimised at same budget')
    ax.set_yticks(yy,labels);ax.invert_yaxis();ax.set_xlim(0,105);ax.set_xlabel('Scenario demand served (%)')
    ax.legend(frameon=False,fontsize=9,loc='lower center',bbox_to_anchor=(.5,1.01),ncol=2);ax.grid(axis='x')
    save(fig,'sensitivity')
    names=['stock_current_2026','stock_2027_low','stock_2027_high','outlook_2030_low','outlook_2030_base','outlook_2030_high']
    d=v.loc[names]
    fig,ax=plt.subplots(figsize=(8,3.5),layout='constrained');x=np.arange(len(d))
    ax.bar(x-.18,100*d.fixed_fraction,width=.35,color=LIGHT,label='Fixed base plan')
    ax.bar(x+.18,100*d.service_fraction,width=.35,color=NAVY,label='Reoptimised, same budget')
    ax.set_xticks(x,['2026\nobserved stock','2027\nlow stock','2027\nhigh stock','2030\n25% fleet','2030\n35% fleet','2030\n45% fleet'])
    ax.set_ylabel('Demand served (%)');ax.set_ylim(0,110);ax.legend(frameon=False,fontsize=9);ax.grid(axis='y')
    save(fig,'outlook')
    formula('formula_demand',[r'$E^{HDB}_t=h_t E_t,\quad EV_{it}=w_{it}E^{HDB}_t,\quad \sum_iw_{it}=1$',
                              r'$D_{it}=EV_{it}\,\beta\,\frac{m}{365}\,\frac{e}{\eta}$'])
    formula('formula_capacity',[r'$q=pHa\rho=7.4\times6\times0.97\times0.85=36.6078$',
                                r'$Q_j^0=Ha\rho\sum_{r\in j}\max_{k\in r}\{p_k\}$'])
    formula('formula_model',[r'$\sum_{j:(i,j)\in A}f_{ij}+s_i=D_i,\qquad f_{ij},s_i\geq0$',
                             r'$\sum_{i:(i,j)\in A}f_{ij}\leq Q_j^0+qx_j$',
                             r'$x_j\leq M_jz_j,\quad z_j\leq x_j,\quad y_j\leq z_j$',
                             r'$7.4x_j\leq G_j+U_jy_j,\quad x_j+b_j^0\leq\bar L_j$',
                             r'$\sum_j(c_jx_j+F_jz_j+K_jy_j)\leq B$',
                             r'$x_j\in\mathbb{Z}_{+},\quad y_j,z_j\in\{0,1\}$'])
    formula('formula_objectives',[r'$S^*=\max\sum_{(i,j)\in A}f_{ij}$',
                                  r'$\min C_{ann}\quad\mathrm{s.t.}\quad\sum_{(i,j)\in A}f_{ij}\geq S^*-\epsilon$'])
    formula('formula_cost',[r'$C_{cap}=\sum_j(c_jx_j+F_jz_j+K_jy_j)$',
                            r'$C_{ann}=\frac{r}{1-(1+r)^{-n}}C_{cap}+\sum_j(m_j+v_j)x_j$',
                            r'$\mathrm{Cost/extra\ annual\ kWh}=\frac{C_{ann}}{365(S-S_0)}$'])
    formula('formula_stock',[r'$E_{2027}=74{,}887+15\,(2{,}872.78)(1-0.02)=117{,}116.83$',
                             r'$E_{2030}\in\{0.25,0.35,0.45\}\times651{,}003$'])
    print('Figures saved to',FIG)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--core-only',action='store_true')
    main(parser.parse_args().core_only)
