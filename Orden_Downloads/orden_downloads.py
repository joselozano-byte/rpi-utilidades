#!/usr/bin/env python3
"""RPI - Triaje semanal de ~/Downloads (sistema aprobado el 2026-10-13).
Uso: python3 orden_downloads.py --base <dir con Downloads, CloudStorage, RPI> [--aplicar]
Sin --aplicar solo simula. Nunca elimina: los descartes van a Downloads/_Para_borrar.
Reglas:
  C1 Liquidaciones Axpo (ANTAM/ANTAR/AVPO) -> SP RPIP 11_DFIN/02_DFIN_COMPARTIDO/06_Tecnico/RAINERGY/Mercado/Axpo/AAAA/MM
  C2 'NN_Month AAAA Report_RPI PT.xls' -> SP RPIP 11_DFIN/01_DFIN_COMUN/01_PLATAFORMA_RPIP/Reporting/AAAA
  C3 'NN_Month AAAA REPORT HR.xls'     -> SP RPIP 11_DFIN/01_DFIN_COMUN/03_PLATAFORMA_RAINERGY/InformeMensual/MmmAA
  B1 Duplicado exacto (nombre+tamano) en SharePoint/OneDrive/RPI -> _Para_borrar
  B2 Instaladores (.dmg .pkg) -> _Para_borrar
  Resto con mas de 7 dias -> listado de pendientes en el informe.
"""
import os, re, sys, shutil, datetime, argparse
ap=argparse.ArgumentParser(); ap.add_argument('--base',required=True); ap.add_argument('--aplicar',action='store_true'); A=ap.parse_args()
B=A.base; D=f'{B}/Downloads'; CS=f'{B}/CloudStorage'
SP=f'{CS}/OneDrive-SharedLibraries-GRUPORPI/RPIP - Documentos'
AXPO=f'{SP}/11_DFIN/02_DFIN_COMPARTIDO/06_Técnico/RAINERGY/Mercado/Axpo'
REP=f'{SP}/11_DFIN/01_DFIN_COMÚN'
PB=f'{D}/_Para_borrar'; HOY=datetime.date.today()
MES={'ENE':1,'FEB':2,'MAR':3,'ABR':4,'MAY':5,'JUN':6,'JUL':7,'AGO':8,'SEP':9,'OCT':10,'NOV':11,'DIC':12}
EN={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
NOM={1:'01 Ene',2:'02 Feb',3:'03 Marzo',4:'04 Abril',5:'05 May',6:'06 Jun',7:'07 Jul',8:'08 Ago',9:'09 Sep',10:'10 Oct',11:'11 Nov',12:'12 Dic'}
ABR={1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
def mesdir(y,m):
    base=f'{AXPO}/{y}'
    if os.path.isdir(base):
        for d in os.listdir(base):
            if d[:2]==f'{m:02d}': return f'{base}/{d}'
    return f'{base}/{NOM[m]}'
def regla(f):
    m=re.match(r'ANTAM-\d+_\w+?_\d{8}_([A-Z]{3})-(\d{2})',f)
    if m: return mesdir(2000+int(m[2]),MES[m[1]]),'C1 Axpo ANTAM'
    m=re.match(r'ANTAR-\d+_\w+?_(\d{4})(\d{2})\d{2}_',f)
    if m: return mesdir(int(m[1]),int(m[2]))+'/Reliquidaciones','C1 Axpo ANTAR'
    m=re.match(r'AVPO-\d{2}-\d+_.*_(\d{4})(\d{2})\d{2}\.pdf$',f)
    if m:
        y,mm=int(m[1]),int(m[2])-1
        if mm==0: y,mm=y-1,12
        return mesdir(y,mm)+'/Representación','C1 Axpo AVPO'
    m=re.match(r'\d{2}_(\w+) (\d{4}) Report_RPI PT\.xls$',f)
    if m: return f'{REP}/01_PLATAFORMA_RPIP/Reporting/{m[2]}','C2 Report RPI PT'
    m=re.match(r'\d{2}_(\w+) (\d{4}) REPORT HR\.xls$',f)
    if m and m[1] in EN: return f'{REP}/03_PLATAFORMA_RAINERGY/InformeMensual/{ABR[EN[m[1]]]}{m[2][2:]}','C3 Report HR'
    return None,None
def indice():
    idx={}
    for r in (f'{CS}/OneDrive-GRUPORPI',f'{CS}/OneDrive-SharedLibraries-GRUPORPI',f'{B}/RPI'):
        for root,ds,fs in os.walk(r):
            ds[:]=[d for d in ds if d not in ('.venv','.git','venv','node_modules','__pycache__')]
            for x in fs: idx.setdefault(x,[]).append(root)
    return idx
def mover(src,dst_dir,acc):
    if not A.aplicar: return
    os.makedirs(dst_dir,exist_ok=True); t=os.path.join(dst_dir,os.path.basename(src))
    if os.path.exists(t):
        if os.path.getsize(t)==os.path.getsize(src): t=os.path.join(PB,os.path.basename(src)); os.makedirs(PB,exist_ok=True)
        else: b,e=os.path.splitext(t); t=f'{b}_desde_Downloads{e}'
    shutil.copy2(src,t)
    if os.path.getsize(t)==os.path.getsize(src): os.remove(src)
idx=indice(); filas=[]
for f in sorted(os.listdir(D)):
    p=f'{D}/{f}'
    if f.startswith(('.','~$','_')) or not os.path.isfile(p): continue
    s=os.path.getsize(p); edad=(HOY-datetime.date.fromtimestamp(os.path.getmtime(p))).days
    dst,r=regla(f)
    if dst: filas.append((f,r,dst.replace(B+'/',''))); mover(p,dst,r); continue
    if f.lower().endswith(('.dmg','.pkg')) and edad>=2: filas.append((f,'B2 Instalador','_Para_borrar')); mover(p,PB,'B2'); continue
    dup=[d for d in idx.get(f,[]) if os.path.exists(f'{d}/{f}') and os.path.getsize(f'{d}/{f}')==s]
    if dup: filas.append((f,'B1 Duplicado exacto','_Para_borrar (copia en '+dup[0].replace(B+'/','')+')')); mover(p,PB,'B1'); continue
    filas.append((f,'PENDIENTE' if edad>7 else f'Reciente ({edad} d)','Decidir destino'))
pb=[]
if os.path.isdir(PB):
    for f in os.listdir(PB):
        q=f'{PB}/{f}'
        if os.path.isfile(q): pb.append((f,(HOY-datetime.date.fromtimestamp(os.path.getmtime(q))).days))
out=f'{B}/RPI/Utilidades/Orden_Downloads/informes/{HOY.isoformat()}_Triaje_Downloads.md'
with open(out,'w') as o:
    o.write(f'# Triaje Downloads {HOY.isoformat()} ({"aplicado" if A.aplicar else "simulacion"})\n\n| Fichero | Regla | Destino |\n|---|---|---|\n')
    for x in filas: o.write(f'| {x[0]} | {x[1]} | {x[2]} |\n')
    o.write(f'\n## _Para_borrar: {len(pb)} ficheros; con mas de 30 dias: {sum(1 for x in pb if x[1]>30)}\n')
    for f,e in sorted(pb,key=lambda x:-x[1]): o.write(f'- {f} ({e} dias)\n')
print(open(out).read()); print('Informe:',out)
