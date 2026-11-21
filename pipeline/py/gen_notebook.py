# Writes python/miami_20_minutes.ipynb for the public repo: a short narrated notebook that reads only ../data and gets
# the page's numbers again (the share of residents with half the places or more within 20 minutes, each place, all
# eight, by car and public transport, the Census places where it holds), with a few charts in the page's colours.
# Execute it afterwards with nbconvert (outputs kept).
#   python -I gen_notebook.py <repo dir>
import sys, os, nbformat as nbf
REPO = sys.argv[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))
md('''
# How far does 20 minutes get you in Miami?

The trip from every Miami-Dade Census block to eight everyday places: by car at the speed limit with no traffic
(`free`), in the TomTom Traffic Index 2025 morning and evening rush-hour slowdown (`am`, `pm`), with Plotlay's older
typical speeds (`typical`, for comparison) and by public transport arriving 8 to 9 am (`pt`). Made in
[Plotlay](https://www.getplotlay.com). This notebook reads only `../data`.

**Read it carefully.** This is a model, not a traffic forecast: the rush hour is a city-wide average slowdown, and the
accuracy depends on OpenStreetMap, the timetable and the cited slowdown. Trips go to the nearest place of each kind
and leave out parking.
''')
code('''
import pandas as pd
import matplotlib.pyplot as plt
DATA = '../data'
mb = pd.read_csv(f'{DATA}/block_minutes.csv', dtype={'block_geoid': str, 'place_geoid': str})
PLACES = ['cbd', 'beach', 'airport', 'hospital', 'uni', 'stadium', 'glades', 'shops']
NAMES = {'cbd': 'Downtown', 'beach': 'A beach', 'airport': 'The airport', 'hospital': 'An ER', 'uni': 'A university',
         'stadium': 'The ballpark', 'glades': 'The Everglades', 'shops': 'A mall'}
RUNS = ['free', 'am', 'pm', 'typical', 'pt']
total = mb.residents.sum()
print(f'{len(mb):,} Census blocks, {total:,.0f} residents')
''')
md('''
## The headline: half the places or more

Read as a general saying, "everything is 20 minutes away" holds for a resident when at least 4 of the 8 places are
within 20 minutes. A block counts for a place when its minutes are 20 or fewer; an empty cell means not reached.
''')
code('''
def counts(run, limit=20):
    return sum((mb[f'{run}_{p}'] <= limit).astype(int) for p in PLACES)
def share(mask): return (mb.residents * mask).sum() / total
for run in ['free', 'am', 'pm', 'pt']:
    print(f'{run:4s} {share(counts(run) >= 4) * 100:5.1f}% of residents have 4 or more of the 8 within 20 minutes')
''')
code('''
for run in RUNS:
    c = counts(run)
    o = c.sort_values(); w = mb.residents[o.index].cumsum(); median = o[w >= total / 2].iloc[0]
    print(f"{run:8s} 3+ {share(c >= 3) * 100:5.1f}%   4+ {share(c >= 4) * 100:5.1f}%   5+ {share(c >= 5) * 100:5.1f}%   all eight {share(c == 8) * 100:4.1f}%   median {median} of 8")
''')
md('## Within 20 minutes of each place')
code('''
table = pd.DataFrame({run: {NAMES[p]: share(mb[f'{run}_{p}'] <= 20) for p in PLACES} for run in RUNS})
(table * 100).round(1).sort_values('free', ascending=False)
''')
md('''
Nobody has all eight. The Everglades are the reason: Shark Valley and the Coe Visitor Center are at the county's edge,
and only a few percent of residents live within 20 minutes of either.
''')
code('''
BG, INK, MUTED = '#160a2b', '#f4ecff', '#a99bc4'
COL = {'free': '#5ee7ef', 'am': '#ff5fa8', 'pm': '#ffb24d', 'pt': '#a99bc4'}
LABEL = {'free': 'Car, speed limit', 'am': 'Car, morning rush', 'pm': 'Car, evening rush', 'pt': 'Public transport'}
plt.rcParams.update({'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG, 'text.color': INK,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': INK, 'axes.edgecolor': MUTED,
                     'font.size': 11})
order = table.sort_values('free').index
fig, ax = plt.subplots(figsize=(9, 5.5))
h = 0.2
for k, run in enumerate(['free', 'am', 'pm', 'pt']):
    ax.barh([i + (1.5 - k) * h for i in range(len(order))], table.loc[order, run] * 100, height=h, color=COL[run], label=LABEL[run])
ax.set_yticks(range(len(order)), order)
ax.set_xlim(0, 100); ax.set_xlabel('Residents within 20 minutes (%)')
ax.set_title('Within 20 minutes of each place, Miami-Dade', loc='left', color=INK)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.legend(frameon=False, loc='lower right')
plt.tight_layout(); plt.show()
''')
md('## How many of the eight')
code('''
dist = pd.DataFrame({LABEL[run]: mb.groupby(counts(run)).residents.sum().reindex(range(9), fill_value=0) / total * 100 for run in ['free', 'am', 'pm', 'pt']})
dist.index.name = 'places within 20 minutes'
dist.round(1)
''')
code('''
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, run in zip(axes, ['free', 'am', 'pt']):
    d = dist[LABEL[run]]
    ax.bar(d.index, d.values, color=[COL[run] if i >= 4 else MUTED for i in d.index], width=0.8)
    ax.set_title(f"{LABEL[run]}: {d[d.index >= 4].sum():.1f}% have 4+", loc='left', fontsize=10, color=INK)
    ax.set_xticks(range(9)); ax.set_xlabel('places within 20 minutes')
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
axes[0].set_ylabel('residents (%)')
plt.tight_layout(); plt.show()
''')
md('''
## Downtown by the minute

The share of residents who reach Government Center within each number of minutes. The gap between the lines is what
the rush hour costs.
''')
code('''
mins = list(range(0, 91, 1))
fig, ax = plt.subplots(figsize=(9, 4.5))
for run in ['free', 'am', 'pm', 'pt']:
    m = mb[f'{run}_cbd']
    ax.step(mins, [share(m <= t) * 100 for t in mins], where='post', color=COL[run], lw=2.2, label=LABEL[run])
ax.axvline(20, color=MUTED, lw=1, ls=':')
ax.set_xlim(0, 90); ax.set_ylim(0, 100)
ax.set_xlabel('minutes'); ax.set_ylabel('residents (%)')
ax.set_title('Reaching Downtown Miami (Government Center)', loc='left', color=INK)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.legend(frameon=False, loc='lower right')
plt.tight_layout(); plt.show()
''')
md('## Where it holds: Census places of 10,000 residents or more')
code('''
pl = pd.read_csv(f'{DATA}/places_table.csv', dtype={'place_geoid': str})
big = pl[(pl.residents >= 10000) & pl.place_geoid.notna()]  # the row for blocks outside any Census place left out
print((big.share_half_free >= 0.5).sum(), 'of', len(big), 'places hold at the speed limit;',
      (big.share_half_am >= 0.5).sum(), 'in the morning rush hour;', (big.share_half_pt >= 0.5).sum(), 'by public transport')
big.sort_values(['share_half_am', 'places_within_20_free'], ascending=False)[['place_name', 'residents', 'share_half_free', 'share_half_am', 'share_half_pt', 'places_within_20_am']].head(10)
''')
md('## Where it fails')
code('''
big.sort_values(['share_half_free', 'places_within_20_free'])[['place_name', 'residents', 'share_half_free', 'places_within_20_free', 'mean_min_downtown_free']].head(10)
''')
md('''
## Sources

OpenStreetMap (c) OpenStreetMap contributors, ODbL 1.0 (roads, beaches, malls; the minutes are a derived database
under the same licence). U.S. Census Bureau 2020 Census and TIGER/Line 2020 (public domain). CMS Hospital General
Information (public domain). TomTom Traffic Index 2025, Miami (cited figures). Miami-Dade Transit GTFS (fetched by
`scripts/get_gtfs.sh`, not redistributed).
''')
nb['cells'] = C
nb['metadata'] = {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}}
nbf.write(nb, os.path.join(REPO, 'python', 'miami_20_minutes.ipynb'))
print('notebook')
