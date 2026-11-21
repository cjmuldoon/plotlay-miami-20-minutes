// OpenStreetMap OPL (osmium cat -f opl) to the elements Overpass answers with `out geom` (ways with nodes and
// geometry, signal nodes with tags, restriction relations with members), so Plotlay's networkFromElements reads the
// same thing in the pipeline as the app reads from Overpass.
import fs from 'node:fs';
const unesc = (s) => s.replace(/%([0-9a-f]+)%/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)));
const tagsOf = (t) => { const o = {}; if (!t) return o; for (const kv of t.split(',')) { const i = kv.indexOf('='); if (i > 0) o[unesc(kv.slice(0, i))] = unesc(kv.slice(i + 1)); } return o; };
export function readOpl(file) {
    const lines = fs.readFileSync(file, 'utf8').split('\n');
    const lat = new Map(), lon = new Map(), out = [];
    for (const l of lines) {
        if (!l) continue;
        const f = l.split(' '), id = +f[0].slice(1), get = (c) => { const x = f.find((s) => s[0] === c); return x ? x.slice(1) : ''; };
        if (l[0] === 'n') {
            const x = +get('x'), y = +get('y'); lat.set(id, y); lon.set(id, x);
            const t = tagsOf(get('T')); if (t.highway === 'traffic_signals') out.push({ type: 'node', id, lat: y, lon: x, tags: t });
        } else if (l[0] === 'w') {
            const nodes = get('N').split(',').filter(Boolean).map((s) => +s.slice(1));
            const geometry = nodes.map((n) => ({ lat: lat.get(n), lon: lon.get(n) }));
            if (geometry.some((g) => g.lat == null)) continue;
            out.push({ type: 'way', id, nodes, geometry, tags: tagsOf(get('T')) });
        } else if (l[0] === 'r') {
            const members = get('M').split(',').filter(Boolean).map((m) => { const at = m.indexOf('@'); return { type: { n: 'node', w: 'way', r: 'relation' }[m[0]], ref: +m.slice(1, at), role: unesc(m.slice(at + 1)) }; });
            out.push({ type: 'relation', id, members, tags: tagsOf(get('T')) });
        }
    }
    return out;
}
