"""Vector figure: the three distinct accounts in cell-level beam accounting.

Run with Python + matplotlib. No experimental values are generated here.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8.0,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})
out = Path(__file__).resolve().parent
fig, ax = plt.subplots(figsize=(7.1, 2.35))
fig.subplots_adjust(0, 0, 1, 1)
ax.set_xlim(0, 7.1); ax.set_ylim(0, 2.35); ax.axis('off')
navy = '#15334A'; teal = '#147A78'; orange = '#AD602B'; gray = '#53616D'

def rounded(x, y, w, h, edge, fill, radius=.045, lw=.8):
    p = FancyBboxPatch((x,y), w,h, boxstyle=f'round,pad=0,rounding_size={radius}',
                       linewidth=lw, edgecolor=edge, facecolor=fill)
    ax.add_patch(p)
    return p

rounded(.12, 1.98, 6.86, .28, teal, '#EAF4F2')
ax.text(3.55, 2.12, 'COMMON QUALITY GATE  •  Qualify beam quality before comparing resource use',
        ha='center', va='center', fontsize=8.0, color=navy, weight='bold')

boxes = [
    (.12, navy, '#F2F5F8', 'UE measurements',
     'Observations made by each UE', 'Candidate measurements\nand monitoring work',
     'Inputs and audit coverage'),
    (2.48, teal, '#EFF7F5', 'Cell CSI-RS occurrences',
     'Unique physical transmissions', 'Retained consumers plus\nadditional audit demand',
     'All consumers and audit timing'),
    (4.84, orange, '#FCF4ED', 'Residual active slots',
     'Time positions still occupied', 'CSI-RS, fixed synchronization\nand other scheduled activity',
     'Placement and background traffic'),
]
for x, c, fill, title, sub, detail, constraint in boxes:
    rounded(x, .82, 2.14, .99, c, fill)
    ax.text(x+.12, 1.59, title, ha='left', va='center', color=c,
            fontsize=9.0, weight='bold')
    ax.text(x+.12, 1.36, sub, ha='left', va='center', color=navy,
            fontsize=7.7)
    ax.text(x+.12, 1.08, detail, ha='left', va='center', color=gray,
            fontsize=7.7, linespacing=1.35)
    ax.plot([x+1.07, x+1.07], [.82,.66], color=c, lw=.75)
    ax.text(x+1.07, .49, constraint, ha='center', va='center', color=c,
            fontsize=7.6, weight='bold')

for x in [2.26,4.62]:
    ax.add_patch(FancyArrowPatch((x+.025,1.31),(x+.195,1.31),
        arrowstyle='-|>', mutation_scale=10, color=gray, linewidth=.9))

ax.plot([.12,6.98],[.27,.27],color='#D4DCE1',lw=.6)
ax.text(3.55,.12,'Outside the numerical ledger: uplink allocation, control signaling, model computation and hardware energy.',
        ha='center',va='center',color=gray,fontsize=7.2)
fig.savefig(out/'accounting_architecture.pdf', metadata={'Title':'From UE measurements to cell resources and residual active time'})
fig.savefig(out/'accounting_architecture.png',dpi=220)
plt.close(fig)
