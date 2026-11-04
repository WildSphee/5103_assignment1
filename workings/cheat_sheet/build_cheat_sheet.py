from pathlib import Path
import os, re, sys
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from ifthen_content import INTRO, CORE_RULES, MORE_RULES, NOTES

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
SIZE=float(sys.argv[1]) if len(sys.argv)>1 else 6.5
LEADING=SIZE*1.09
FONT='Liberation Sans'
NAVY='17354A'
SUMMARY_ONLY=os.environ.get('SUMMARY_ONLY')=='1'
PAGES=2 if SUMMARY_ONLY else 4
SUM_SIZE=float(sys.argv[2]) if len(sys.argv)>2 else 8.9
IF_SIZE=float(sys.argv[3]) if len(sys.argv)>3 else 9.4

def split_columns(name):
 return [s.strip() for s in re.split(r'<!-- COLUMN \d+ -->', (WORK/name).read_text()) if s.strip()]

columns=split_columns('content.md')
summary_columns=split_columns('content_summaries.md')
if SUMMARY_ONLY:summary_columns=[c.replace('(Side 4)','(Side 2)') for c in summary_columns]
doc=Document()
sec=doc.sections[0]
sec.page_width=Mm(210); sec.page_height=Mm(297)
sec.top_margin=Mm(7); sec.bottom_margin=Mm(7)
sec.left_margin=Mm(7); sec.right_margin=Mm(7)
sec.header_distance=Mm(2); sec.footer_distance=Mm(2.7)
normal=doc.styles['Normal']
normal.font.name=FONT; normal.font.size=Pt(SIZE)
normal.paragraph_format.space_after=Pt(1.5)
normal.paragraph_format.line_spacing=Pt(LEADING)
normal.paragraph_format.widow_control=False
normal.paragraph_format.keep_with_next=False
normal.paragraph_format.keep_together=False
lang=OxmlElement('w:lang'); lang.set(qn('w:val'),'en-GB')
normal.element.get_or_add_rPr().append(lang)

def style_run(r,size,bold=None,color='111111'):
 if bold is not None:r.bold=bold
 r.font.name=FONT; r.font.size=Pt(size)
 r.font.color.rgb=RGBColor.from_string(color)
 fonts=r._element.get_or_add_rPr().rFonts
 if fonts is not None:
  fonts.set(qn('w:eastAsia'),FONT); fonts.set(qn('w:cs'),FONT)

def add_runs(p,text,size=SIZE,color='111111'):
 for i,part in enumerate(re.split(r'\*\*(.*?)\*\*',text)):
  if not part: continue
  style_run(p.add_run(part),size,i%2==1,color)

def heading(p,text,size,first):
 p.paragraph_format.space_before=Pt(0 if first else 3.0)
 p.paragraph_format.space_after=Pt(2)
 p.paragraph_format.line_spacing=Pt(size+2.1)
 p.paragraph_format.keep_with_next=True
 p.paragraph_format.keep_together=True
 style_run(p.add_run(text),size+1,True,NAVY)
 pp=p._p.get_or_add_pPr()
 border=OxmlElement('w:pBdr'); bottom=OxmlElement('w:bottom')
 for k,v in [('val','single'),('sz','4'),('space','1'),('color','A7B4BE')]: bottom.set(qn('w:'+k),v)
 border.append(bottom); pp.append(border)

def cell_margins(cell,top=0,bottom=0,left=0,right=0):
 tcPr=cell._tc.get_or_add_tcPr()
 margins=OxmlElement('w:tcMar')
 for tag,val in [('top',top),('bottom',bottom),('left',left),('right',right)]:
  el=OxmlElement('w:'+tag); el.set(qn('w:w'),str(val)); el.set(qn('w:type'),'dxa'); margins.append(el)
 tcPr.append(margins)

def shade(cell,fill):
 sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:color'),'auto'); sh.set(qn('w:fill'),fill)
 cell._tc.get_or_add_tcPr().append(sh)

def make_cell(cell,content,colnum,body_size,ncols=3):
 cell_margins(cell,left=65 if colnum else 0,right=65 if colnum<ncols-1 else 0)
 for j,line in enumerate(content.splitlines()):
  p=cell.paragraphs[0] if j==0 else cell.add_paragraph()
  p.paragraph_format.line_spacing=Pt(body_size*1.09)
  if line.startswith('## '):heading(p,line[3:],body_size,j==0)
  else: add_runs(p,line,body_size)

def table_borders(table,inside_v=True,grid=False,color='CAD1D6'):
 pr=table._tbl.tblPr
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  on=grid or (side=='insideV' and inside_v)
  el=OxmlElement('w:'+side);el.set(qn('w:val'),'single' if on else 'nil')
  el.set(qn('w:sz'),'3');el.set(qn('w:color'),color);borders.append(el)
 pr.append(borders)

def page_break():
 p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=Pt(1)
 p.add_run().add_break(WD_BREAK.PAGE)

MAIN_TITLE='DBA5103  •  LECTURE SUMMARY CHEAT SHEET' if SUMMARY_ONLY else 'DBA5103  •  OPERATIONS RESEARCH & ANALYTICS'
def page_title(subtitle):
 title=doc.add_paragraph()
 title.paragraph_format.space_after=Pt(2)
 title.paragraph_format.line_spacing=Pt(12)
 style_run(title.add_run(MAIN_TITLE),10,True,NAVY)
 p=doc.add_paragraph()
 p.paragraph_format.space_after=Pt(4);p.paragraph_format.line_spacing=Pt(8)
 style_run(p.add_run(subtitle),6.5,True)

def column_page(cols,sizes):
 table=doc.add_table(rows=1,cols=len(cols))
 table.autofit=False
 for c in table.columns:c.width=Mm(196/len(cols))
 table_borders(table)
 for c,(content,size) in enumerate(zip(cols,sizes)):make_cell(table.cell(0,c),content,c,size,len(cols))

def rule_table(header,rows,widths,size):
 table=doc.add_table(rows=1+len(rows),cols=len(header))
 table.autofit=False
 table_borders(table,grid=True,color='B9C3CB')
 for i,w in enumerate(widths):
  for cell in table.columns[i].cells:cell.width=Mm(w)
 for gc,w in zip(table._tbl.tblGrid.findall(qn('w:gridCol')),widths):gc.set(qn('w:w'),str(int(w*56.7)))
 for r,row in enumerate([header]+rows):
  for c,text in enumerate(row):
   cell=table.cell(r,c)
   cell_margins(cell,top=15,bottom=15,left=55,right=55)
   p=cell.paragraphs[0]
   p.paragraph_format.space_after=Pt(0)
   p.paragraph_format.line_spacing=Pt(size*1.18)
   if r==0:
    shade(cell,NAVY);add_runs(p,text,size,'FFFFFF')
    for run in p.runs:run.bold=True
   else:
    if r%2==0:shade(cell,'EEF2F5')
    add_runs(p,text,size+(0.6 if c==1 else 0))
 return table

def section_heading(text,size,before=4):
 p=doc.add_paragraph()
 p.paragraph_format.line_spacing=Pt(size*1.09)
 heading(p,text,size,False)
 p.paragraph_format.space_before=Pt(before)

def body(text,size,after=2):
 p=doc.add_paragraph()
 p.paragraph_format.space_after=Pt(after)
 p.paragraph_format.line_spacing=Pt(size*1.15)
 add_runs(p,text,size)

subtitles=['SIDE 1 / 4  ·  LP, SIMPLEX, DUALITY & UNCERTAINTY',
 'SIDE 2 / 4  ·  NETWORKS, INTEGER MODELS & DYNAMIC PROGRAMMING',
 'SIDE 3 / 4  ·  COURSE SUMMARY: WHAT EACH LECTURE COVERED (L1–L8)',
 'SIDE 4 / 4  ·  TURNING “IF… THEN…” RULES INTO MATH (BINARY LOGIC)']
sizes=[7.0,6.75,6.7,6.65,6.75,6.5]
if SUMMARY_ONLY:
 subtitles=['','','SIDE 1 / 2  ·  WHAT EACH LECTURE COVERED (L1–L8)','SIDE 2 / 2  ·  TURNING “IF… THEN…” RULES INTO MATH (BINARY LOGIC)']
else:
 for page in range(2):
  if page:page_break()
  page_title(subtitles[page])
  column_page(columns[page*3:page*3+3],sizes[page*3:page*3+3])
 page_break()
page_title(subtitles[2])
column_page(summary_columns,[SUM_SIZE,SUM_SIZE])

page_break()
page_title(subtitles[3])
TS=IF_SIZE
N0=1 if SUMMARY_ONLY else 14
body(INTRO,TS+0.3,3)
section_heading(f'{N0} · THE CORE RULES (projects x₁…x₆, each a 0/1 switch)',TS,1)
rule_table(['Rule in words','Math','Why it works','0/1 test: the only combos it blocks'],CORE_RULES,[42,40,52,62],TS)
section_heading(f'{N0+1} · MORE RULES IN THE SAME STYLE',TS)
rule_table(['Rule in words','Math','Why it works / what it blocks'],MORE_RULES,[52,58,86],TS)
section_heading(f'{N0+2} · METHOD, CHECKS & TRAPS',TS)
table=doc.add_table(rows=1,cols=2)
table.autofit=False
for c in table.columns:c.width=Mm(98)
table_borders(table)
for c,content in enumerate(NOTES):make_cell(table.cell(0,c),content,c,TS,2)

foot=sec.footer.paragraphs[0]
foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
foot.paragraph_format.space_after=Pt(0)
foot.paragraph_format.line_spacing=Pt(6)
style_run(foot.add_run('Sources: DBA5103 lecture notes 1–8; selected assignment examples  •  A4 portrait · print 100% · duplex, flip long edge (' + ('1 sheet' if SUMMARY_ONLY else '2 sheets') + ')'),5.8,None,'444444')
doc.core_properties.title='DBA5103 Lecture Summary Cheat Sheet — Lectures 1–8' if SUMMARY_ONLY else 'DBA5103 Quiz Cheat Sheet — Lectures 1–8'
doc.core_properties.subject='Two-sided A4: lecture-by-lecture summary and if-then logic' if SUMMARY_ONLY else 'Four-sided A4 reference: formulas, worked examples, lecture summaries, if-then logic'
doc.core_properties.author=''
doc.core_properties.keywords='LP, simplex, duality, sensitivity, network flow, IP, binary logic, dynamic programming'
out=ROOT/('DBA5103_Lecture_Summary_Cheat_Sheet.docx' if SUMMARY_ONLY else 'DBA5103_Quiz_Cheat_Sheet.docx')
doc.save(out)
print(out)
for i,c in enumerate(columns+summary_columns):print('column',i+1,'words',len(c.split()))
