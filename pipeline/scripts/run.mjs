// "How far does 20 minutes get you in Miami?" The pipeline's engine run, with Plotlay's own code (the plotlay repo's
// src/core/drivetime.js with core/roadrules.js, and core/gtfs.js, transitrun.js for public transport).
//
// Who: every resident of Miami-Dade County, placed at the internal point of their 2020 Census block
// (raw/census/people-miami.json: 2,701,767 residents in 25,813 blocks with people).
// What: eight everyday places (scripts/destinations.mjs), each the nearest of its kind in the county.
// By car: OpenStreetMap roads of 20 Nov 2026 (raw/osm/roads.opl) with the road rules for the United States (traffic
// keeps right; one-way streets, turn bans, waits at lights and junctions), each road at its speed limit, from each
// resident TO the place:
//   free     little traffic (free-flow)
//   am       the morning rush hour slowdown of the TomTom Traffic Index 2025 for Miami's metro area (preset
//            miami-tomtom-2025-am: highways 75.5%, other roads 73.6% slower)
//   pm       the evening rush hour (miami-tomtom-2025-pm: 98.9% and 86.5%)
//   typical  Plotlay's older model: typical running speeds by kind of road, both ways, no waits (sensitivity)
// By public transport: Miami-Dade Transit's GTFS (Metrorail, Metromover, Metrobus; published 19 Nov 2026) for Tuesday
// 24 November 2026, arriving between 08:00 and 09:00 (the median trip), walking at 5.1 km/h on OpenStreetMap's
// walkable ways, up to 1,200 m to the first stop and from the last, up to 3 changes, 150 m cells.
// Out: out/times.json (minutes per block, per place and run), out/flow-*.json and out/roads-*.json (the roads with
// their minutes to downtown, for the maps), out/meta.json.
//   node --max-old-space-size=12288 scripts/run.mjs <plotlay repo> [car] [pt]
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { open } from 'node:fs/promises';
import { readOpl } from './opl.mjs';
import { destinations } from './destinations.mjs';

const [REPO, ...want0] = process.argv.slice(2), want = want0.length ? want0 : ['car', 'pt'];
const T = await import(path.join(REPO, 'src/core/drivetime.js'));
const B = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..'), OUT = path.join(B, 'out');
fs.mkdirSync(OUT, { recursive: true });
const r1 = (x) => (x == null || !Number.isFinite(x) ? null : Math.round(x * 10) / 10);

// people: each 2020 Census block at its internal point
const ppl = JSON.parse(fs.readFileSync(path.join(B, 'raw/census/people-miami.json'), 'utf8'));
const homes = ppl.blocks.map((b, i) => ({ i, code: b.geoid, place: b.place, people: b.people, ll: b.ll }));
console.log('blocks', homes.length, 'residents', homes.reduce((t, h) => t + h.people, 0));
const D = destinations(B);
const times = fs.existsSync(path.join(OUT, 'times.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'times.json'), 'utf8')) : { homes: homes.map((h) => ({ code: h.code, place: h.place, people: h.people, ll: h.ll })), runs: {} };
const meta = fs.existsSync(path.join(OUT, 'meta.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'meta.json'), 'utf8')) : {};

if (want.includes('car')) {
    let t0 = performance.now();
    const els = readOpl(path.join(B, 'raw/osm/roads.opl'));
    const net = T.networkFromElements(els, { rules: true, model: 'limits' });
    const typ = T.networkFromElements(els, { model: 'typical' });
    if (net.region !== 'us' || net.rules.side !== 'right') throw new Error('expected the United States road rules');
    console.log('networks', net.nodes, net.edges, Math.round(net.length_m / 1000), 'km', ((performance.now() - t0) / 1000).toFixed(1), 's');
    meta.network = { nodes: net.nodes, edges: net.edges, km: Math.round(net.length_m / 1000), signal_nodes: net.rules.signals, sets_of_lights: net.rules.light_sets, turn_bans: net.rules.restrictions,
        turn_bans_left_out: net.rules.restrictions_left_out, one_way_stretches: net.rules.oneway_edges, region: net.region, keeps: net.rules.side, osm_extract: 'Geofabrik florida-latest.osm.pbf, 2026-11-20T21:21:21Z' };
    const RUNS = { free: { net, opts: { rules: true, direction: 'to' } }, am: { net, opts: { rules: true, direction: 'to', peak: 'miami-tomtom-2025-am' } }, pm: { net, opts: { rules: true, direction: 'to', peak: 'miami-tomtom-2025-pm' } }, typical: { net: typ, opts: {} } };
    for (const [rk, R] of Object.entries(RUNS)) {
        for (const d of D) {
            t0 = performance.now();
            // snap 400 m: a place must be by a road (a beach on an island with no road, out in the bay, is not reached by car)
            const run = T.fromSources(R.net, d.points.map((q, i) => ({ key: q.name || `${d.id}${i}`, ll: q.ll })), { snap: 400, ...R.opts });
            const mins = new Array(homes.length), near = new Array(homes.length);
            homes.forEach((h, i) => { const r = T.timeAt(run, h.ll); mins[i] = r ? r1(r.minutes) : null; near[i] = r ? r.nearest : null; });
            times.runs[`car_${rk}_${d.id}`] = mins;
            if (rk === 'free') times.runs[`nearest_${d.id}`] = near;
            if (rk === 'free' && run.not_placed.length) console.log('  not placed', d.id, run.not_placed);
            console.log(rk, d.id, ((performance.now() - t0) / 1000).toFixed(1), 's');
            // the roads with their minutes to downtown (and the nearest beach), for the maps and the example
            if ((rk === 'free' || rk === 'am') && (d.id === 'cbd' || d.id === 'beach')) {
                const nm = T.nodeMinutes(run), out = [];
                const fl = T.driveFlow(run, [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60], { maxSegs: 140000, skip: ['service', 'living_street', 'track'] });
                fs.writeFileSync(path.join(OUT, `flow-${rk}-${d.id}.json`), JSON.stringify(fl));
                console.log('   flow segments', fl.drive.segments, 'simplify', fl.drive.simplify_m);
                // edges as [lat1, lng1, lat2, lng2, min1, min2, class] for the page's road map
                for (let k = 0; k < net.edges; k++) {
                    const w = net.ways[net.way[k]], a = net.a[k], b = net.b[k];
                    if (!w || ['service', 'living_street', 'track'].includes(w.highway)) continue;
                    const ma = nm[a], mb = nm[b];
                    if (!(Math.min(ma, mb) < 90)) continue;
                    out.push([+net.lat[a].toFixed(5), +net.lng[a].toFixed(5), +net.lat[b].toFixed(5), +net.lng[b].toFixed(5), r1(ma), r1(mb), w.highway]);
                }
                fs.writeFileSync(path.join(OUT, `roads-${rk}-${d.id}.json`), JSON.stringify(out));
            }
        }
    }
}

if (want.includes('pt')) {
    const G = await import(path.join(REPO, 'src/core/gtfs.js')), R = await import(path.join(REPO, 'src/core/transitroute.js')), RUN = await import(path.join(REPO, 'src/core/transitrun.js'));
    let t0 = performance.now();
    const fh = await open(path.join(B, 'raw/gtfs/miami-dade-transit.zip')), { size } = await fh.stat();
    const src = { size, read: async (o, n) => { const b = new Uint8Array(n); await fh.read(b, 0, n, o); return b; } };
    const DAY = '2026-11-24';
    const tt = await G.readGtfs(src, { date: DAY, from: '06:00', to: '09:00', shapes: false, feedName: 'Miami-Dade Transit', licence: 'Miami-Dade County public records (Florida Statutes chapter 119)' });
    await fh.close();
    console.log('timetable', ((performance.now() - t0) / 1000).toFixed(1), 's');
    const f = R.frameAt(25.7761, -80.1961);
    t0 = performance.now();
    const graph = await walkGraph(path.join(B, 'raw/osm/walk.geojsonseq'), f);
    console.log('walk graph', graph.n, graph.edges, ((performance.now() - t0) / 1000).toFixed(1), 's');
    const SC = await import(path.join(REPO, 'src/core/transitscenario.js')), WK = (await import(path.join(REPO, 'src/core/walkerpresets.js'))).walkerOf?.('adult') || { kmh: 5.1 };
    const rev = SC.reverseTimetable(tt);
    const nIdx = (() => { const cells = new Map(), Gs = 250; for (let i = 0; i < graph.n; i++) { const k = Math.floor(graph.x[i] / Gs) * 1e6 + Math.floor(graph.y[i] / Gs); const c = cells.get(k); if (c) c.push(i); else cells.set(k, [i]); }
        return { near(x, y, r, fn) { const cx = Math.floor(x / Gs), cy = Math.floor(y / Gs); for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) { const c = cells.get((cx + i) * 1e6 + cy + j); if (c) for (const q of c) { const dd = Math.hypot(graph.x[q] - x, graph.y[q] - y); if (dd <= r) fn(q, dd); } } } }; })();
    meta.pt = { day: DAY, arrive: '08:00 to 09:00', stat: 'median', walker: 'adult 5.1 km/h', walk_max_m: 1200, transfers: 3, home_from_nodes_m: 250, feed_version: tt.feeds?.[0]?.version || null, walk_km: graph.km };
    for (const d of D) {
        t0 = performance.now();
        // up to 50 places at once (the engine's limit), spread along the list
        const pts = d.points.length <= 50 ? d.points : d.points.filter((_, i) => i % Math.ceil(d.points.length / 50) === 0);
        // each home from the street nodes near it (within 250 m, the walk on to the home added), from the router's
        // times to every street node: reading a 150 m cell instead left homes in cells no street node falls in unreached,
        // and which cells those were moved with the grid's corner from run to run
        const res = R.transitTimes(rev, { origins: pts.map((q) => q.ll), frame: f, from: SC.MIRROR - 9 * 3600, to: SC.MIRROR - 8 * 3600, step: 120, minutes: 120, transfers: 3, kmh: WK.kmh, walkMaxM: 1200, graph, targets: 'nodes' });
        const nm = res.median, mps = WK.kmh / 3.6;
        const mins = homes.map((h) => { const [x, y] = f.toXY(h.ll[0], h.ll[1]); let b = Infinity; nIdx.near(x, y, 250, (q, dd) => { if (nm[q] < 255) { const v = nm[q] + (dd * 1.3) / mps / 60; if (v < b) b = v; } }); return b <= 120 ? Math.ceil(b) : null; });
        times.runs[`pt_${d.id}`] = mins;
        if (d.id === 'cbd') {
            // the picture's grid (the hero and the app): the engine's own run, as the app makes it
            const run = RUN.runTransit(tt, { origins: pts.map((q) => q.ll), frame: f, from: '08:00', to: '09:00', step: 120, bands: [20, 40, 60, 90, 120], transfers: 3, walker: 'adult', walkMaxM: 1200, graph, targets: 'cells', cell: 150, direction: 'to', stat: 'median', align: true });
            fs.writeFileSync(path.join(OUT, 'pt-grid-cbd.json'), JSON.stringify({ ...run.grid, minutes: Buffer.from(run.grid.minutes).toString('base64') }));
        }
        console.log('pt', d.id, pts.length, 'places', ((performance.now() - t0) / 1000).toFixed(1), 's');
    }
}
fs.writeFileSync(path.join(OUT, 'times.json'), JSON.stringify(times));
fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));

// the walk graph of the transit-45-minutes showcase (its run.mjs): ways read as lines, only their ends and shared
// points become nodes
async function walkGraph(file, f) {
    const WALKABLE = new Set(['footway', 'path', 'pedestrian', 'living_street', 'residential', 'service', 'unclassified', 'tertiary', 'tertiary_link', 'secondary', 'secondary_link', 'primary', 'primary_link', 'steps', 'track', 'cycleway', 'corridor', 'road', 'bridleway']);
    const key = (x, y) => (Math.round(x * 2) + 2 ** 20) * 2 ** 21 + (Math.round(y * 2) + 2 ** 20);
    const lines = [];
    const rl = readline.createInterface({ input: fs.createReadStream(file), crlfDelay: Infinity });
    for await (let l of rl) {
        if (l.charCodeAt(0) === 0x1e) l = l.slice(1);
        if (!l) continue;
        const ft = JSON.parse(l), t = ft.properties || {};
        if (!WALKABLE.has(t.highway) || /^(no|private)$/.test(t.foot || '') || /^(no|private)$/.test(t.access || '') || t.area === 'yes') continue;
        const c = ft.geometry.coordinates, xy = new Float64Array(c.length * 2);
        for (let i = 0; i < c.length; i++) { const q = f.toXY(c[i][1], c[i][0]); xy[i * 2] = q[0]; xy[i * 2 + 1] = q[1]; }
        lines.push(xy);
    }
    const seen = new Map();
    for (const xy of lines) for (let i = 0; i < xy.length; i += 2) { const k = key(xy[i], xy[i + 1]); seen.set(k, (seen.get(k) || 0) + ((i === 0 || i === xy.length - 2) ? 2 : 1)); }
    const idx = new Map(), xs = [], ys = [], ea = [], eb = [], el = [];
    const node = (x, y, k) => { let n = idx.get(k); if (n == null) { n = xs.length; idx.set(k, n); xs.push(x); ys.push(y); } return n; };
    for (const xy of lines) {
        let a = node(xy[0], xy[1], key(xy[0], xy[1])), len = 0;
        for (let i = 2; i < xy.length; i += 2) {
            len += Math.hypot(xy[i] - xy[i - 2], xy[i + 1] - xy[i - 1]);
            const k = key(xy[i], xy[i + 1]);
            if (seen.get(k) >= 2 || i === xy.length - 2 || len > 120) { const b = node(xy[i], xy[i + 1], k); if (a !== b && len > 0) { ea.push(a); eb.push(b); el.push(len); } a = b; len = 0; }
        }
    }
    // only the connected walking network: islands of footway (inside a stadium, a mall's car park, a gated estate whose
    // gates are not mapped) would catch a stop or a place on their nearest node and strand it, so components under
    // 500 nodes are dropped and everything snaps to the network that joins up (Miami, 22 Nov 2026)
    {
        const N0 = xs.length, par = Int32Array.from({ length: N0 }, (_, i) => i);
        const find = (a) => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
        for (let i = 0; i < ea.length; i++) { const a = find(ea[i]), b = find(eb[i]); if (a !== b) par[a] = b; }
        const size = new Int32Array(N0); for (let i = 0; i < N0; i++) size[find(i)]++;
        const keep = new Int32Array(N0).fill(-1), kx = [], ky = [];
        for (let i = 0; i < N0; i++) if (size[find(i)] >= 500) { keep[i] = kx.length; kx.push(xs[i]); ky.push(ys[i]); }
        const na = [], nb = [], nl = [];
        for (let i = 0; i < ea.length; i++) if (keep[ea[i]] >= 0) { na.push(keep[ea[i]]); nb.push(keep[eb[i]]); nl.push(el[i]); }
        console.log('walk graph: kept', kx.length, 'of', N0, 'nodes in components of 500 or more');
        xs.length = 0; ys.length = 0; for (let i = 0; i < kx.length; i++) { xs.push(kx[i]); ys.push(ky[i]); } ea.length = 0; eb.length = 0; el.length = 0;
        for (let i = 0; i < na.length; i++) { ea.push(na[i]); eb.push(nb[i]); el.push(nl[i]); }
    }
    const n = xs.length, off = new Int32Array(n + 1);
    for (let i = 0; i < ea.length; i++) { off[ea[i] + 1]++; off[eb[i] + 1]++; }
    for (let i = 0; i < n; i++) off[i + 1] += off[i];
    const to = new Int32Array(off[n]), len = new Float32Array(off[n]), fill = off.slice(0, n);
    for (let i = 0; i < ea.length; i++) { to[fill[ea[i]]] = eb[i]; len[fill[ea[i]]++] = el[i]; to[fill[eb[i]]] = ea[i]; len[fill[eb[i]]++] = el[i]; }
    return { n, x: Float64Array.from(xs), y: Float64Array.from(ys), off, to, len, edges: ea.length, km: Math.round(el.reduce((t, v) => t + v, 0) / 1000) };
}
