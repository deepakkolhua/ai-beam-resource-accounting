#!/usr/bin/env python3
"""Export one merged LaTeX document with the approved figure assets and guide."""
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
M = ROOT / 'manuscript'
OUT = ROOT.parent / 'deliverables'
STAGE = ROOT / 'final_latex'
STAGE.mkdir(exist_ok=True)
(STAGE / 'figures').mkdir(exist_ok=True)
source = (M / 'beam_magazine.tex').read_text()
source = re.sub(r'\\input\{([^}]+)\}', lambda m: (M / m.group(1)).read_text().rstrip(), source)
assert '\\input{' not in source and '\\bibliography{' not in source
(STAGE / 'main.tex').write_text(source)
for name in ['quality_qualified', 'equal_budget', 'packing_comparison']:
    shutil.copy2(M / 'figures' / (name + '.pdf'), STAGE / 'figures' / (name + '.pdf'))

for ext in ['pdf', 'tex']:
    shutil.copy2(M / 'figures' / ('accounting_architecture_vector.' + ext), STAGE / 'figures' / ('accounting_architecture_vector.' + ext))
shutil.copy2(ROOT / 'FINAL_LATEX_README.md', STAGE / 'README.md')
shutil.copy2(ROOT / 'AUTHOR_REPRODUCTION.md', STAGE / 'AUTHOR_REPRODUCTION.md')
(STAGE / 'build.sh').write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\npdflatex -interaction=nonstopmode -halt-on-error main.tex\npdflatex -interaction=nonstopmode -halt-on-error main.tex\n')
shutil.copy2(STAGE / 'main.tex', OUT / 'main.tex')
files = ['main.tex', 'README.md', 'AUTHOR_REPRODUCTION.md', 'build.sh']
files += ['figures/' + name + '.pdf' for name in ['quality_qualified', 'equal_budget', 'packing_comparison']]
files += ['figures/accounting_architecture_vector.pdf', 'figures/accounting_architecture_vector.tex']
shutil.copy2(ROOT / 'DELIVERY_VALIDATION.json', STAGE / 'VALIDATION.json')
files += ['VALIDATION.json']
shutil.copy2(STAGE / 'main.tex', OUT / 'Beam_Prediction_Final.tex')
with zipfile.ZipFile(OUT / 'Beam_Prediction_Final_LaTeX.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for name in files:
        z.write(STAGE / name, name)
with zipfile.ZipFile(OUT / 'Beam_Prediction_Final_LaTeX.zip') as z:
    assert z.testzip() is None
print('Exported merged LaTeX, four vector figures, editable TikZ architecture, and build/reproduction instructions.')
