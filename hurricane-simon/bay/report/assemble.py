"""Assemble the expanded report: new front sections + renumbered original sections + partnership section + appendices.
Usage: assemble.py SCRATCH OUT.html"""
import re, sys, os, glob
S, OUT = sys.argv[1], sys.argv[2]
old = open(S + '/report/simon_report.html', encoding='utf-8').read()
front = open(S + '/report/frag_front.html', encoding='utf-8').read()
ppp = open(S + '/report/frag_ppp.html', encoding='utf-8').read() if os.path.exists(S + '/report/frag_ppp.html') else '<section class="pb"><h2>10. Training, collaboration and a public-private partnership</h2><p>[pending]</p></section>'
head = old[:old.index('<body>') + len('<body>')]
tail = '\n</body>\n</html>\n'
def section(title_start):
    i = old.index(title_start); a = old.rfind('<section', 0, i); b = old.index('</section>', i) + len('</section>')
    return old[a:b]
s3 = section('<h2>3. The uploaded analysis'); s4 = section('<h2>4. The verification, model by model'); s5 = section('<h2>5. The intensity problem'); s6 = section('<h2>6. Uncertainty, shown rather than hidden'); s7 = section('<h2>7. Risk communication')
appB = section('<h2>Appendix B. Methods and sources')
# --- renumber headings and figure references (placeholders first to avoid collisions) ---
def ren(s, pairs):
    for a, b in pairs: s = s.replace(a, '\x00' + b + '\x00')
    return s.replace('\x00', '')
s3 = ren(s3, [('<h2>3. The uploaded analysis', '<h2>5. The uploaded analysis'), ('(Figure 4)', '(Figure 8)')])
s3 = s3.replace('<section class="pb">', '<section>', 1)
s3 = s3.replace('The table below checks each claim against the record', 'The table below checks each claim against the record (as of Sunday 3 pm, advisory 18, the last full verification before the closest pass; section 3 carries the outcome)')
s4 = ren(s4, [('<h2>4. The verification, model by model', '<h2>6. The verification, model by model'), ('<b>Figure 2.</b>', '<b>Figure 6.</b>'), ('<b>Figure 3a.</b>', '<b>Figure 7a.</b>'), ('<b>Figure 3b.</b>', '<b>Figure 7b.</b>'),
              ('<figure><img src="__REP__/f2_track_error.png"', '<figure class="chart"><img src="__REP__/f2_track_error.png"'), ('__REP__/verify_en_top.jpg', '__REP__/verify_light_top.jpg'), ('__REP__/verify_en_table.jpg', '__REP__/verify_light_table.jpg'), ('reached 15–20% late Friday and early Saturday (section 6)', 'reached 15–20% late Friday and early Saturday (section 3)')])
s4 = s4.replace('<p>Every model was scored the same way.', '<p>This section is the verification as it stood on Sunday at 3 pm (advisory 18), the last full set before the closest pass. Every model was scored the same way.')
s5 = ren(s5, [('<h2>5. The intensity problem', '<h2>7. The intensity problem'), ('<b>Figure 4.</b>', '<b>Figure 8.</b>')])
# section 6 (uncertainty): drop the odds figure (now Figure 4 in section 3), renumber
i = s6.index('<figure><img src="__REP__/f3_pv_odds.png"'); j = s6.index('</figure>', i) + len('</figure>'); s6 = s6[:i] + s6[j:]
s6 = ren(s6, [('<h2>6. Uncertainty, shown rather than hidden', '<h2>8. Uncertainty, shown rather than hidden'), ('<b>Figure 6.</b>', '<b>Figure 9.</b>'), ('(see Figure 5)', '(see Figure 4)')])
s6 = s6.replace('<p>The document\'s criticism of the cone is that it looks certain. The honest alternative is to show how the forecast itself moved, how wide the ensembles are, and what the models\' own error record implies for tonight.</p>',
                '<p>This section is kept as it was written on Sunday at 3 pm, before the closest pass, because that is when it was needed; the outcome (section 3) is the test of it. The document\'s criticism of the cone is that it looks certain. The honest alternative is to show how the forecast itself moved (Figure 4), how wide the ensembles are, and what the models\' own error record implies.</p>')
s6 = s6.replace('<p>From Friday afternoon to Saturday night (advisories 10 to 15)', '<p>Figure 4 (section 3) shows the NHC\'s own odds. From Friday afternoon to Saturday night (advisories 10 to 15)')
# section 7 (risk communication): drop "what to do tonight", renumber
k = s7.index('<h2>8. What to do tonight'); s7 = s7[:k].rstrip() + '\n</section>'
s7 = ren(s7, [('<h2>7. Risk communication: my own input', '<h2>9. Risk communication: my own input'), ('as in Figure 3,', 'as in Figure 7,'), ('(Figure 3 and A1–A5 here) and the one-page building summary (Figure 1)', '(Appendix A here) and the one-page building summary (Figure 1)')])
s7 = s7.replace('Section 11 turns that into a proposal.', 'Section 10 turns that into a proposal.')
front = front.replace('Section 11 sets out', 'Section 10 sets out')
# --- Appendix A: every resident graphic, by advisory version, light theme, English ---
SETS = [('17a', 'A1 · Advisory 17, first set (Sunday 9:10 am)', 'The first set of the day. Rain scaled to the SMN regional maximum; wind from the NHC line that passed 74 km from the city.'),
        ('17b', 'A2 · Advisory 17, corrected set (Sunday 1 pm)', 'Same advisory, rain no longer scaled up after a ground report that it was not raining; dry-side wording added.'),
        ('18', 'A3 · Advisory 18 (Sunday 3 pm)', 'The last set before the closest pass: the NHC line at 101 km, Vallarta tropical-storm odds 8%. Includes the model verification graphic.'),
        ('20', 'A4 · Advisory 20 (Monday 6 am)', 'Rebuilt Monday morning with the storm stalled 120–140 km to the west-southwest; the SMN figures are from aviso 40.')]
NAMES = {'summary': 'Building summary', 'wind': 'Wind', 'rain': 'Rain', 'flood': 'Water and slopes', 'timing': 'Timing', 'models': 'Models', 'verify': 'Model verification'}
appA = ['<section>\n  <div><h2>Appendix A. The resident graphics, every version, on white</h2>\n  <p>Everything produced for residents during the storm, in the order it was issued, rendered in English on a white background for print. Each set is dated with the advisory it was built on; the numbers are those of that moment and were superseded by the next set. The Spanish originals remain on the shared page.</p>']
first = True
for key, title, note in SETS:
    appA.append(f'  <h3 style="margin-top:14pt">{title}</h3><p class="small">{note}</p>' if first else f'  <div class="apage"><h3>{title}</h3><p class="small">{note}</p>')
    for g in ['summary', 'wind', 'rain', 'flood', 'timing', 'models', 'verify']:
        p = f'{S}/bay/light/{key}/simon_{g}_en.jpg'
        if not os.path.exists(p): continue
        appA.append(f'  <figure class="page"><img src="file://{p}" alt="{NAMES[g]}, {title}"><figcaption><b>{title.split(" · ")[0]}-{g}.</b> {NAMES[g]} · {title.split(" · ")[1]}.</figcaption></figure>')
    appA.append('  </div>')
    first = False
appA = '\n'.join(appA) + '\n</section>'
# --- Appendix B additions ---
appB = appB.replace('<h3>Sources</h3>', '<h3>Forecast evolution and outcome</h3>\n  <p>Figures 2–3 use the NHC forecast/advisory products for advisories 1–20: each advisory\'s forecast points were interpolated hourly and the closest approach to 20.61N 105.23W taken as the minimum distance; the intensity is interpolated at that time. The real closest approach uses the NHC best track to Monday 6 am interpolated the same way. Figure 5 uses the building summaries\' own numbers (bay.json for each version) and the airport reports (METAR MMPR) from Sunday 3 pm to Monday 8 am. Print versions of the resident graphics (Appendix A) are the same renderer with page colours remapped for a white background; map areas keep their original colours. From the Monday build onward, satellite centre fixes more than 60 km from the NHC analysed or interpolated position are replaced by the NHC position before the fields are computed (section 4).</p>\n  <h3>Sources</h3>')
appB = appB.replace('NHC forecast/advisory, discussion, wind-speed probabilities and forecast advisory for EP202026 (advisories 1–18)', 'NHC forecast/advisory, discussion, wind-speed probabilities and forecast advisory for EP202026 (advisories 1–20A)')
appB = appB.replace('SMN-CONAGUA avisos de ciclón tropical (through aviso 34)', 'SMN-CONAGUA avisos de ciclón tropical (through aviso 40)')
if os.path.exists(S + '/report/frag_sources.html'): appB = appB.replace('<div class="foot">', open(S + '/report/frag_sources.html', encoding='utf-8').read() + '\n  <div class="foot">')
appB = ren(appB, [('<h2>Appendix B. Methods and sources', '<h2>Appendix B. Methods and sources')])
html = head + '\n' + front + '\n' + s3 + '\n' + s4 + '\n' + s5 + '\n' + s6 + '\n' + s7 + '\n' + ppp + '\n' + appA + '\n' + appB + tail
html = html.replace('__LIGHT20__', 'file://' + S + '/bay/light/20')
html = html.replace('<title>Hurricane Simon and Puerto Vallarta: models, verification and uncertainty</title>', '<title>Hurricane Simon and Puerto Vallarta: forecasts, outcome, and what coastal early warning needs next</title>')
open(OUT, 'w', encoding='utf-8').write(html); print('assembled', len(html), 'chars; figures', html.count('<figure'))
