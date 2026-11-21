// The eight everyday places of "how far does 20 minutes get you in Miami?", each as the nearest of its kind (a list of
// points), and how each was chosen. Points are [lat, lng]: beaches and shopping centres from OpenStreetMap
// (raw/osm/places.geojsonseq, Geofabrik's Florida extract of 20 Nov 2026, ODbL), the rest placed by hand at the middle
// of their OpenStreetMap outline or their main entrance. Only places in Miami-Dade County count.
import fs from 'node:fs';
import path from 'node:path';

const RAD = Math.PI / 180;
function readPlaces(B) {
    const out = [];
    for (let l of fs.readFileSync(path.join(B, 'raw/osm/places.geojsonseq'), 'utf8').split('\n')) {
        l = l.replace(/^\x1e/, ''); if (!l.trim()) continue;
        const f = JSON.parse(l); if (!/Polygon/.test(f.geometry.type)) continue;
        const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
        let area = 0, cx = 0, cy = 0; const rings = [];
        for (const pl of polys) {
            const r = pl[0], lat0 = r[0][1], mx = 111320 * Math.cos(lat0 * RAD), my = 111132; rings.push(r);
            let a = 0, x = 0, y = 0;
            for (let i = 0; i + 1 < r.length; i++) { const x0 = (r[i][0] - r[0][0]) * mx, y0 = (r[i][1] - lat0) * my, x1 = (r[i + 1][0] - r[0][0]) * mx, y1 = (r[i + 1][1] - lat0) * my, k = x0 * y1 - x1 * y0; a += k; x += (x0 + x1) * k; y += (y0 + y1) * k; }
            if (Math.abs(a) > 1) { const A = Math.abs(a) / 2; area += A; cx += (r[0][0] + x / (3 * a) / mx) * A; cy += (lat0 + y / (3 * a) / my) * A; }
        }
        if (!area) continue;
        out.push({ props: f.properties, area_ha: area / 1e4, ll: [cy / area, cx / area], rings });
    }
    return out;
}
// points every `step` metres round a ring ([lng, lat]), for a long beach
function along(ring, step) {
    const pts = []; let acc = step;
    for (let i = 0; i + 1 < ring.length; i++) {
        const [x0, y0] = ring[i], [x1, y1] = ring[i + 1], mx = 111320 * Math.cos(y0 * RAD), L = Math.hypot((x1 - x0) * mx, (y1 - y0) * 111132);
        while (acc <= L) { const t = acc / L; pts.push([y0 + (y1 - y0) * t, x0 + (x1 - x0) * t]); acc += step; }
        acc -= L;
    }
    return pts;
}

// in Miami-Dade: south of the Broward line (NW 215th Street, about 25.957 N), and up to Golden Beach (25.975 N) east of
// about 80.167 W, where the line steps north round Aventura
export const inCounty = ([lat, lng]) => lat < 25.9573 || (lat < 25.9745 && lng > -80.167);
const pts = (list) => list.map(([name, a, b]) => ({ name, ll: [a, b] }));
export function destinations(B) {
    const P = readPlaces(B).filter((p) => inCounty(p.ll));
    const beaches = P.filter((p) => p.props.natural === 'beach' && p.area_ha >= 1);
    const beachPts = beaches.flatMap((b) => { const a = along(b.rings[0], 500).filter(inCounty); return (a.length ? a : [b.ll]).map((ll) => ({ name: b.props.name || 'Beach', ll })); });
    const malls = P.filter((p) => p.props.shop === 'mall' && p.props.name && p.area_ha >= 2);
    return [
        { id: 'cbd', name: 'Downtown Miami (Government Center)', short: 'Downtown', how: 'Downtown Miami at Government Center, 111 NW 1st Street (the Stephen P. Clark Government Center and its Metrorail and Metromover station).', points: pts([['Government Center', 25.7761, -80.1961]]) },
        { id: 'beach', name: 'The nearest beach', short: 'A beach', how: `OpenStreetMap sand beaches (natural=beach) of 1 ha or more in Miami-Dade: ${beaches.length}, from Golden Beach and Sunny Isles down Miami Beach and South Beach to Key Biscayne and the bay beaches, each a point every 500 m along its outline (${beachPts.length} points).`, points: beachPts },
        { id: 'airport', name: 'Miami International Airport', short: 'The airport', how: 'Miami International Airport, the departures road in front of the main terminal by Concourse E.', points: pts([['Miami International Airport', 25.7954, -80.2790]]) },
        { id: 'hospital', name: 'The nearest hospital emergency department', short: 'An ER', how: 'General hospitals in Miami-Dade with emergency services in the CMS Hospital General Information file (October 2026), with Jackson Health System’s four campuses (one listing in the file) counted apart, and HCA Florida Mercy in Coconut Grove: 20. Children’s, veterans’ and freestanding emergency rooms are left out.',
            points: pts([['Jackson Memorial Hospital', 25.7948, -80.2150], ['Jackson North Medical Center', 25.9306, -80.2044], ['Jackson South Medical Center', 25.6303, -80.3479], ['Jackson West Medical Center', 25.7998, -80.3249], ['Baptist Hospital of Miami', 25.6876, -80.3417], ['West Kendall Baptist Hospital', 25.6770, -80.4573], ['South Miami Hospital', 25.7001, -80.2961], ['Doctors Hospital', 25.7245, -80.2752], ['Homestead Hospital', 25.4813, -80.4323], ['Mount Sinai Medical Center', 25.8109, -80.1459], ['North Shore Medical Center', 25.8581, -80.2166], ['HCA Florida Aventura Hospital', 25.9716, -80.1459], ['HCA Florida Kendall Hospital', 25.7314, -80.3880], ['HCA Florida Mercy Hospital', 25.7418, -80.2182], ['Hialeah Hospital', 25.8457, -80.2709], ['Palmetto General Hospital', 25.8877, -80.3277], ['Larkin Community Hospital', 25.7068, -80.2934], ['Larkin Community Hospital Palm Springs Campus', 25.8695, -80.3132], ['Coral Gables Hospital', 25.7439, -80.2559], ['Keralty Hospital', 25.7466, -80.3175]]) },
        { id: 'uni', name: 'The nearest university campus', short: 'A university', how: 'The teaching campuses of Florida International University (Modesto A. Maidique in Westchester, Biscayne Bay in North Miami), the University of Miami (Coral Gables, the Miller School medical campus), Barry University, St. Thomas University and Florida Memorial University. Miami Dade College and branch campuses of out-of-county universities are left out.',
            points: pts([['FIU Modesto A. Maidique Campus', 25.7567, -80.3842], ['FIU Biscayne Bay Campus', 25.9123, -80.1447], ['University of Miami, Coral Gables', 25.7145, -80.2857], ['University of Miami, Miller School of Medicine', 25.7907, -80.2178], ['Barry University', 25.8801, -80.2088], ['St. Thomas University', 25.9254, -80.2605], ['Florida Memorial University', 25.9208, -80.2731]]) },
        { id: 'stadium', name: 'loanDepot park', short: 'The ballpark', how: 'loanDepot park in Little Havana, home of the Miami Marlins (the middle of its OpenStreetMap outline).', points: pts([['loanDepot park', 25.7781, -80.2196]]) },
        { id: 'glades', name: 'The Everglades (Shark Valley or the Coe Visitor Center)', short: 'The Everglades', how: 'Everglades National Park’s two entrances in Miami-Dade, whichever is nearer: the Shark Valley Visitor Center on the Tamiami Trail and the Ernest F. Coe Visitor Center west of Homestead.', points: pts([['Shark Valley Visitor Center', 25.7569, -80.7655], ['Ernest F. Coe Visitor Center', 25.3952, -80.5832]]) },
        { id: 'shops', name: 'The nearest big mall', short: 'A mall', how: `Named malls in OpenStreetMap (shop=mall) in Miami-Dade with an outline of 2 ha or more: ${malls.length}. Centres mapped another way (The Falls is mapped as retail land) are missed; others nearby stand in.`, points: malls.map((m) => ({ name: m.props.name, ll: m.ll })) },
    ];
}
