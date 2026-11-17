// Live version of the pipeline's transforms, computed in the browser from the same public sources.
// Formulas mirror src/mobility_etl/transform.py and the gates mirror quality.py.
const CITIES = [['Antwerp', 51.2194, 4.4025], ['Brussels', 50.8503, 4.3517], ['Ghent', 51.0543, 3.7174], ['Leuven', 50.8798, 4.7005], ['Liège', 50.6326, 5.5797]];
const MIN_EXPECTED_STATIONS = 100;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let weather = null;

// transform_station_status
function transformStations(payload) {
  return payload.network.stations.map(s => {
    const x = s.extra || {};
    const capacity = Number.isFinite(+x.slots) ? +x.slots : 0;
    const bikes = +s.free_bikes || 0, docks = +s.empty_slots || 0;
    let state = 'healthy';
    if (bikes === 0) state = 'empty';
    if (docks === 0) state = 'full';
    if (!(x.renting && x.returning)) state = 'unavailable';
    return { id: s.id, name: s.name, lat: s.latitude, lon: s.longitude, capacity, bikes, ebikes: +x.ebikes || 0, docks,
      occupancy: capacity ? Math.round(bikes / capacity * 1000) / 10 : 0, state, lastUpdated: x.last_updated, timestamp: s.timestamp };
  });
}
// estimated_mobility_demand in transform_weather
const demand = (hour, rain) => Math.max(20, Math.round(100 + ([7, 8, 9, 16, 17, 18].includes(hour) ? 20 : 0) - Math.min(rain * 12, 55)));

function tile(v, l, c = '') { return `<div class="kpi-tile ${c}"><div class="v">${v}</div><div class="l">${l}</div></div>`; }

function renderStations(st) {
  const count = k => st.filter(s => s.state === k).length;
  const avg = st.reduce((a, s) => a + s.occupancy, 0) / st.length;
  $('bm-tiles').innerHTML = tile(st.length, 'stations in the Villo! feed', 'big') + tile(count('empty'), 'empty: no bikes', count('empty') ? 'warn' : '') +
    tile(count('full'), 'full: no free docks', count('full') ? 'warn' : '') + tile(count('unavailable'), 'not renting or returning', count('unavailable') ? 'bad' : '') +
    tile(avg.toFixed(1) + '%', 'average occupancy') + tile(st.reduce((a, s) => a + s.bikes, 0), 'bikes available') + tile(st.reduce((a, s) => a + s.ebikes, 0), 'of which e-bikes');
  const ids = new Set(), dup = st.some(s => ids.size === ids.add(s.id).size);
  const tzless = st.filter(s => s.lastUpdated && !/[zZ]|[+-]\d\d:?\d\d$/.test(s.lastUpdated)).length;
  const gate = (ok, label, cls) => `<span class="pill ${ok ? 'ok' : cls || 'bad'}">${ok ? '✓' : '!'} ${label}</span>`;
  $('bm-gates').innerHTML = '<span class="small dim">Quality gates from quality.py:</span> ' +
    gate(st.length >= MIN_EXPECTED_STATIONS, `≥ ${MIN_EXPECTED_STATIONS} stations (${st.length})`) +
    gate(!st.some(s => s.bikes < 0 || s.docks < 0 || s.ebikes < 0), 'no negative counts') +
    gate(!dup, 'no duplicate station IDs') +
    gate(tzless === 0, `${tzless} station timestamps without timezone`, 'warn');
  // dot map (equirectangular, corrected for latitude)
  const lats = st.map(s => s.lat), lons = st.map(s => s.lon);
  const [la0, la1, lo0, lo1] = [Math.min(...lats), Math.max(...lats), Math.min(...lons), Math.max(...lons)];
  const k = Math.cos((la0 + la1) / 2 * Math.PI / 180), W = 520, H = Math.round(W * (la1 - la0) / ((lo1 - lo0) * k)) || 400, P = 10;
  const x = lo => P + (lo - lo0) / (lo1 - lo0) * (W - 2 * P), y = la => P + (la1 - la) / (la1 - la0) * (H - 2 * P);
  const map = $('bm-map'); map.setAttribute('viewBox', `0 0 ${W} ${H}`);
  map.innerHTML = st.map((s, i) => `<circle cx="${x(s.lon).toFixed(1)}" cy="${y(s.lat).toFixed(1)}" r="${3 + Math.sqrt(s.capacity || 1) / 2}" class="${s.state}" data-i="${i}"><title>${esc(s.name)}: ${s.bikes} bikes, ${s.docks} docks</title></circle>`).join('');
  map.onmouseover = map.onclick = e => { const s = st[e.target.dataset?.i]; if (s) $('bm-hover').innerHTML = `<b>${esc(s.name)}</b> · ${s.bikes} bikes (${s.ebikes} e) · ${s.docks} free docks · ${s.occupancy}% · <span class="pill ${s.state === 'healthy' ? 'ok' : s.state === 'unavailable' ? 'bad' : 'warn'}">${s.state}</span>`; };
  const low = st.filter(s => s.state !== 'unavailable' && s.capacity).sort((a, b) => a.occupancy - b.occupancy || b.capacity - a.capacity).slice(0, 8);
  $('bm-low').innerHTML = '<tr><th>Station</th><th class="num">Bikes</th><th class="num">Docks</th><th class="num">Occ.</th></tr>' +
    low.map(s => `<tr><td>${esc(s.name)}</td><td class="num">${s.bikes}</td><td class="num">${s.docks}</td><td class="num">${s.occupancy}%</td></tr>`).join('');
}

function renderChart() {
  const city = $('bm-city').value, i = CITIES.findIndex(c => c[0] === city), w = Array.isArray(weather) ? weather[i] : weather;
  const now = Date.now(), h = w.hourly;
  const rows = h.time.map((t, j) => ({ t, hour: +t.slice(11, 13), rain: h.precipitation[j] ?? 0, temp: h.temperature_2m[j] }))
    .filter(r => Date.parse(r.t + ':00Z') - (w.utc_offset_seconds || 0) * 1000 >= now - 36e5).slice(0, 48);
  const W = 720, H = 200, B = 26, bw = (W - 30) / rows.length;
  const yD = v => H - B - v / 120 * (H - B - 14), maxRain = Math.max(2, ...rows.map(r => r.rain));
  let s = `<line x1="28" x2="${W}" y1="${yD(100)}" y2="${yD(100)}" class="ref"/><text x="0" y="${yD(100) + 4}" class="ax">100</text>`;
  rows.forEach((r, j) => {
    const d = demand(r.hour, r.rain), x0 = 30 + j * bw;
    s += `<rect x="${x0 + 1}" y="${yD(d)}" width="${bw - 2}" height="${H - B - yD(d)}" class="d${[7, 8, 9, 16, 17, 18].includes(r.hour) ? ' c' : ''}"><title>${r.t.replace('T', ' ')} · demand ${d} · rain ${r.rain} mm · ${r.temp}°C</title></rect>`;
    if (r.rain > 0) s += `<rect x="${x0 + bw * .3}" y="${H - B - r.rain / maxRain * 40}" width="${bw * .4}" height="${r.rain / maxRain * 40}" class="rain"/>`;
    if (r.hour % 6 === 0 && j < rows.length - 2) s += `<text x="${x0}" y="${H - 8}" class="ax">${r.hour === 0 ? r.t.slice(5, 10) : r.hour + 'h'}</text>`;
  });
  $('bm-chart').setAttribute('viewBox', `0 0 ${W} ${H}`); $('bm-chart').innerHTML = s;
}

async function load() {
  $('bm-status').textContent = 'Fetching live data from CityBikes and Open-Meteo…';
  const q = k => CITIES.map(c => c[k]).join(',');
  const [bikes, wx] = await Promise.allSettled([
    fetch('https://api.citybik.es/v2/networks/villo').then(r => { if (!r.ok) throw new Error('CityBikes HTTP ' + r.status); return r.json(); }),
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${q(1)}&longitude=${q(2)}&hourly=temperature_2m,precipitation,weather_code&forecast_days=3&timezone=Europe%2FBrussels`).then(r => { if (!r.ok) throw new Error('Open-Meteo HTTP ' + r.status); return r.json(); }),
  ]);
  const msgs = [];
  if (bikes.status === 'fulfilled') { renderStations(transformStations(bikes.value)); msgs.push(`Villo! snapshot ${new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`); }
  else msgs.push(`Bike data unavailable (${bikes.reason.message}): the pipeline would fail visibly here too.`);
  if (wx.status === 'fulfilled') { weather = wx.value; renderChart(); msgs.push('Open-Meteo forecast loaded'); }
  else msgs.push(`Weather unavailable (${wx.reason.message})`);
  $('bm-status').textContent = 'Live · ' + msgs.join(' · ');
}
$('bm-city').innerHTML = CITIES.map(c => `<option${c[0] === 'Brussels' ? ' selected' : ''}>${c[0]}</option>`).join('');
$('bm-city').addEventListener('change', () => weather && renderChart());
$('bm-refresh').addEventListener('click', load);
load();
