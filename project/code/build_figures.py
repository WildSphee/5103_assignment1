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
    from build_showcase import build_tables, build_top100
    area,years=build_tables()
    top100=build_top100()
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif'],
                         'mathtext.fontset':'stix','font.size':10,'axes.spines.top':False,
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
    fig,ax=plt.subplots(figsize=(8,5.0),layout='constrained')
    for f in boundary:
        g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in polys:
            xy=np.array(poly[0]);x,y=tr.transform(xy[:,0],xy[:,1])
            ax.fill(np.array(x)/1000,np.array(y)/1000,facecolor='#F1F3F4',edgecolor='#C4D0D6',lw=.45,zorder=0)
    other=s[(s.ac_additions>0)&~s.car_park_no.isin(top100.car_park_no)]
    ax.scatter(other.x_coord/1000,other.y_coord/1000,s=7,c='#AAB8BF',alpha=.65,lw=0,label='Other 449 base-selected carparks',zorder=2)
    ax.scatter(top100.x_coord/1000,top100.y_coord/1000,s=29,c=ORANGE,edgecolors='white',linewidths=.5,label='Top 100 review candidates',zorder=4)
    for name,xy in {'Jurong West':(14.5,38.5),'Bukit Batok':(22,40),'Woodlands':(22,49),
                    'Yishun':(30,46),'Ang Mo Kio':(32,40),'Sengkang':(38,43.7),
                    'Tampines':(43,39),'Bedok':(42,33),'Central':(30,30)}.items():
        ax.text(*xy,name,fontsize=8,color=NAVY,ha='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':1},zorder=5)
    ax.plot([9,14],[26,26],color=NAVY,lw=2);ax.text(11.5,26.6,'5 km',ha='center',fontsize=8)
    ax.annotate('N',xy=(47,46),xytext=(47,43.8),ha='center',fontsize=10,arrowprops={'arrowstyle':'->','color':NAVY})
    ax.set(xlim=(7,49),ylim=(24.5,51),aspect='equal',title='End-2027 review shortlist: 100 carparks across 21 planning areas')
    ax.axis('off');ax.legend(loc='lower center',bbox_to_anchor=(.5,-.03),ncol=2,frameon=False,fontsize=9)
    save(fig,'top100_map')
    show=area.head(12)
    names=show.planning_area.str.title().tolist()+[f'Other {len(area)-12} planning areas']
    values=show.additional_ac_points.tolist()+[area.iloc[12:].additional_ac_points.sum()]
    fig,ax=plt.subplots(figsize=(8,4.2),layout='constrained')
    bars=ax.barh(names,values,color=[BLUE]*12+[LIGHT])
    for b,vv in zip(bars,values):ax.text(vv+7,b.get_y()+b.get_height()/2,f'{int(vv):,}',va='center',fontsize=9)
    ax.invert_yaxis();ax.set_xlim(0,max(values)*1.14);ax.set_xlabel('Additional AC points for the end-2027 base scenario')
    ax.grid(axis='x');save(fig,'planning_area_allocation')
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
    d=years.set_index('scenario').loc[['current_2026','2027_base','2030_low','2030_base','2030_high']]
    fig,ax=plt.subplots(figsize=(8,3.4),layout='constrained');x=np.arange(len(d))
    ax.bar(x-.18,100*d.existing_shortfall_fraction,width=.35,color=ORANGE,label='Frozen existing supply only')
    ax.bar(x+.18,100*d.fixed_2027_plan_shortfall_fraction,width=.35,color=NAVY,label='Existing + fixed 2027 additions')
    ax.set_xticks(x,['Sep 2026\nbenchmark','End 2027\nbase','2030\nlow','2030\ncentral','2030\nhigh'])
    ax.set_ylabel('Modelled energy unmet (%)');ax.set_ylim(0,85)
    ax.legend(frameon=False,fontsize=9,loc='lower center',bbox_to_anchor=(.5,1.01),ncol=2);ax.grid(axis='y')
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
    formula('formula_stock',[r'$E_{2027}=74{,}887+15\,(2{,}872.78)(1-0.02)\approx117{,}116.83$',
                             r'$E_{2030}\in\{0.25,0.35,0.45\}\times651{,}003$'])
    print('Figures saved to',FIG)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--core-only',action='store_true')
    main(parser.parse_args().core_only)
