"""Single Python entry point for the full analysis and checked Office deliverables."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
from prepare_data import ROOT, OUT


def execute(name,*args):
    subprocess.run([sys.executable,str(Path(__file__).with_name(name)),*args],check=True)


def main():
    for script,args in [('prepare_data.py',()),('test_models.py',()),('run_analysis.py',('--mode','all')),
                        ('review_shortlist.py',()),('audit_outputs.py',()),('build_figures.py',()),('build_workbook.py',()),('build_report.py',())]:
        execute(script,*args)
    if not shutil.which('libreoffice'):
        raise SystemExit('DOCX/XLSX created. Install LibreOffice and rerun to render and validate the PDF.')
    subprocess.run(['libreoffice','-env:UserInstallation=file:///tmp/hdb_report_render',
                    '--headless','--convert-to','pdf','--outdir',str(ROOT),str(ROOT/'HDB_EV_Charging_Report.docx')],check=True)
    execute('audit_outputs.py','--office')
    execute('build_workbook.py') # Include the completed Office-validation rows.
    execute('audit_outputs.py','--office')
    execute('finalise_release.py')
    print('All deliverables and release checks complete:',ROOT)


if __name__=='__main__':
    main()
