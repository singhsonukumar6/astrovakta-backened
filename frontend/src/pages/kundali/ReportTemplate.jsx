import React from 'react';
import './report.css';

const PLANET_SYMBOLS = {
  Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿',
  Jupiter: '♃', Venus: '♀', Saturn: '♄', Rahu: '☊', Ketu: '☋',
};

const SIGN_SYMBOLS = {
  Aries: '♈', Taurus: '♉', Gemini: '♊', Cancer: '♋',
  Leo: '♌', Virgo: '♍', Libra: '♎', Scorpio: '♏',
  Sagittarius: '♐', Capricorn: '♑', Aquarius: '♒', Pisces: '♓',
};

const DIVISION_INFO = {
  D3: { name: 'D3 – Drekkana', focus: 'Siblings, Courage & Initiative' },
  D7: { name: 'D7 – Saptamsa', focus: 'Children & Progeny' },
  D10: { name: 'D10 – Dashamsa', focus: 'Career & Profession' },
  D12: { name: 'D12 – Dwadashamsa', focus: 'Parents & Ancestry' },
  D16: { name: 'D16 – Shodashamsa', focus: 'Happiness & Vehicles' },
  D20: { name: 'D20 – Vimshamsa', focus: 'Spiritual Progress' },
  D24: { name: 'D24 – Chaturvimshamsa', focus: 'Education & Learning' },
  D27: { name: 'D27 – Saptavimshamsa', focus: 'Strength & Vigor' },
  D30: { name: 'D30 – Trimsamsa', focus: 'Misfortunes & Evils' },
  D40: { name: 'D40 – Khavedamsa', focus: 'Maternal Happiness' },
  D45: { name: 'D45 – Akshavedamsa', focus: 'Paternal Happiness' },
  D60: { name: 'D60 – Shashtiamsha', focus: 'Past Life / Karmic' },
};

const HOUSE_NAMES = [
  'Ascendant / Self', 'Wealth & Family', 'Siblings & Courage',
  'Home & Comfort', 'Children & Intellect', 'Enemies & Disease',
  'Marriage & Partnership', 'Longevity & Transformation',
  'Fortune & Dharma', 'Career & Status', 'Gains & Aspirations',
  'Loss & Liberation',
];

function safe(v, fallback = '') {
  if (v === null || v === undefined) return fallback;
  if (typeof v === 'object') {
    if (Array.isArray(v)) return v.join(', ');
    if (v.sign) return v.sign;
    if (v.name) return v.name;
    if (v.value !== undefined) return String(v.value);
    if (v.prediction) return v.prediction;
    return JSON.stringify(v);
  }
  return v;
}

function safeArr(obj) {
  if (Array.isArray(obj)) return obj;
  return [];
}

function formatDate(str) {
  if (!str) return 'N/A';
  try {
    const d = new Date(str);
    if (isNaN(d.getTime())) return String(str);
    return d.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch { return String(str); }
}

function getSvgString(data) {
  if (!data) return null;
  if (typeof data === 'string') {
    const trimmed = data.trim();
    if (trimmed.startsWith('<?xml') || trimmed.startsWith('<svg')) return data;
    try {
      const parsed = JSON.parse(data);
      if (parsed && parsed.svg) return parsed.svg;
    } catch {}
    return data;
  }
  if (typeof data === 'object' && data.svg) return data.svg;
  return null;
}

function SectionHeading({ children }) {
  return <h2 className="section-heading">{children}</h2>;
}

function EmptyBlock({ message = 'Data not available for this section.' }) {
  return <p className="text-muted text-sm" style={{ fontStyle: 'italic' }}>{message}</p>;
}

function RenderSvg({ data, title, label, variant }) {
  const svgStr = getSvgString(data);
  if (!svgStr) return <EmptyBlock />;
  const cls = variant === 'major' ? 'chart-container chart-container--major'
    : variant === 'minor' ? 'chart-container chart-container--minor'
    : 'chart-container';
  return (
    <div className={cls}>
      {title && <div className="chart-title">{title}</div>}
      <div className="chart-svg-wrapper" dangerouslySetInnerHTML={{ __html: svgStr }} />
      {label && <div className="chart-label">{label}</div>}
    </div>
  );
}

/* ─────────── COVER PAGE ─────────── */
function CoverPage({ data, branding }) {
  const basic = data?.kundli?.data?.basicDetails || {};
  return (
    <div className="page cover-page">
      {branding.logoUrl ? (
        <img src={branding.logoUrl} alt={branding.brandName} className="cover-logo" />
      ) : (
        <div className="cover-logo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '42px', fontWeight: 700, color: branding.primaryColor }}>
          {branding.brandName.charAt(0)}
        </div>
      )}
      <h1 className="cover-title">{branding.coverTitle || 'Vedic Birth Chart Report'}</h1>
      <p className="cover-subtitle">{branding.coverSubtitle || 'Comprehensive Kundali Analysis'}</p>
      <hr className="cover-divider" />
      <dl className="cover-details">
        <dt>Name</dt>
        <dd>{branding.clientName || 'N/A'}</dd>
        <dt>Date of Birth</dt>
        <dd>{formatDate(basic.birthDate)}</dd>
        <dt>Time of Birth</dt>
        <dd>{basic.birthTime || 'N/A'}</dd>
        <dt>Place of Birth</dt>
        <dd>{basic.birthPlace || `${basic.latitude}, ${basic.longitude}`}</dd>
        <dt>Generated On</dt>
        <dd>{new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}</dd>
      </dl>
      <div className="cover-footer">{branding.brandName} &copy; {new Date().getFullYear()}</div>
    </div>
  );
}

/* ─────────── TABLE OF CONTENTS ─────────── */
function TableOfContents() {
  const sections = [
    'Birth Details & Panchang',
    'Planetary Positions',
    'House Positions',
    'D1 Rasi Chart (Major)',
    'D9 Navamsa Chart (Major)',
    'Moon Chart (Major)',
    'Divisional Charts D3–D60',
    'Vimshottari Dasha',
    'Current Dasha Period',
    'Chara & Yogini Dasha',
    'Bhava Chalit',
    'Yoga Analysis',
    'Dosha Analysis',
    'Transit Analysis',
    'Career Horoscope',
    'Finance Horoscope',
    'Health Horoscope',
    'Love & Marriage',
    'Education Horoscope',
    'Child Prospects',
    'Foreign Travel',
    'Lucky Elements',
    'Gemstone Recommendation',
    'Rudraksha Recommendation',
    'Annual Forecast (Varshaphal)',
  ];
  return (
    <div className="page">
      <SectionHeading>Table of Contents</SectionHeading>
      <ul className="report-list" style={{ listStyle: 'none', paddingLeft: 0 }}>
        {sections.map((s, i) => (
          <li key={i} style={{ padding: '8px 0', borderBottom: '1px dotted var(--report-border)', fontSize: '14px' }}>
            <span style={{ color: 'var(--brand-primary)', fontWeight: 600, marginRight: 12 }}>{String(i + 1).padStart(2, '0')}</span>
            {s}
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ─────────── BIRTH DETAILS ─────────── */
function BirthDetails({ data, branding }) {
  const basic = data?.kundli?.data?.basicDetails || {};
  const panchang = data?.panchang?.data || data?.kundli?.data?.panchang || {};
  const rahuKaal = data?.rahuKaal?.data || {};
  const gulikaKaal = data?.gulikaKaal?.data || {};
  const yamaganda = data?.yamaganda?.data || {};
  const choghadiya = data?.choghadiya?.data || {};
  const asc = basic.ascendant || {};

  return (
    <div className="page">
      <SectionHeading>Birth Details & Panchang</SectionHeading>

      <div className="sub-heading">Basic Information</div>
      <table className="report-table">
        <tbody>
          <tr><td className="text-bold">Name</td><td>{branding?.clientName || 'N/A'}</td></tr>
          <tr><td className="text-bold">Date of Birth</td><td>{formatDate(basic.birthDate)}</td></tr>
          <tr><td className="text-bold">Time of Birth</td><td>{basic.birthTime || 'N/A'}</td></tr>
          <tr><td className="text-bold">Place of Birth</td><td>{basic.birthPlace || `${basic.latitude}, ${basic.longitude}`}</td></tr>
          <tr><td className="text-bold">Timezone</td><td>{basic.timezone || 'N/A'}</td></tr>
          <tr><td className="text-bold">Latitude / Longitude</td><td>{basic.latitude}, {basic.longitude}</td></tr>
          <tr><td className="text-bold">Ayanamsa</td><td>{basic.ayanamsa} ({basic.ayanamsaValue?.toFixed(4)}°)</td></tr>
          <tr><td className="text-bold">Ascendant (Lagna)</td><td>{SIGN_SYMBOLS[asc.sign] || ''} {asc.sign || 'N/A'} ({asc.degree?.toFixed(1) || ''}°)</td></tr>
          <tr><td className="text-bold">Moon Sign (Rasi)</td><td>{SIGN_SYMBOLS[basic.moonSign] || ''} {basic.moonSign || 'N/A'}</td></tr>
          <tr><td className="text-bold">Sun Sign</td><td>{SIGN_SYMBOLS[basic.sunSign] || ''} {basic.sunSign || 'N/A'}</td></tr>
          <tr><td className="text-bold">Nakshatra</td><td>{asc.nakshatra || 'N/A'} (Lord: {asc.nakshatraLord || 'N/A'})</td></tr>
        </tbody>
      </table>

      <div className="sub-heading" style={{ marginTop: 24 }}>Panchang Details</div>
      <div className="panchang-grid">
        <div className="panchang-card"><div className="panchang-card__label">Tithi</div><div className="panchang-card__value">{safe(panchang.tithi)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Nakshatra</div><div className="panchang-card__value">{safe(panchang.nakshatra)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Yoga</div><div className="panchang-card__value">{safe(panchang.yoga)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Karana</div><div className="panchang-card__value">{safe(panchang.karana)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Paksha</div><div className="panchang-card__value">{safe(panchang.paksha)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Moon Phase</div><div className="panchang-card__value">{safe(panchang.moonPhase)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Sunrise</div><div className="panchang-card__value">{safe(panchang.sunrise)}</div></div>
        <div className="panchang-card"><div className="panchang-card__label">Sunset</div><div className="panchang-card__value">{safe(panchang.sunset)}</div></div>
      </div>

      <div className="sub-heading" style={{ marginTop: 24 }}>Inauspicious Timings</div>
      <table className="report-table">
        <thead><tr><th>Period</th><th>Start</th><th>End</th><th>Duration</th></tr></thead>
        <tbody>
          <tr><td className="text-bold">Rahu Kaal</td><td>{rahuKaal.rahuKaalStart || 'N/A'}</td><td>{rahuKaal.rahuKaalEnd || 'N/A'}</td><td>{safe(rahuKaal.duration, '—')}</td></tr>
          <tr><td className="text-bold">Gulika Kaal</td><td>{gulikaKaal.gulikaKaalStart || 'N/A'}</td><td>{gulikaKaal.gulikaKaalEnd || 'N/A'}</td><td>{safe(gulikaKaal.duration, '—')}</td></tr>
          <tr><td className="text-bold">Yamaganda</td><td>{yamaganda.yamagandaStart || 'N/A'}</td><td>{yamaganda.yamagandaEnd || 'N/A'}</td><td>{safe(yamaganda.duration, '—')}</td></tr>
        </tbody>
      </table>

      {(safeArr(choghadiya.dayChoghadiya).length > 0 || safeArr(choghadiya.nightChoghadiya).length > 0) && (
        <>
          <div className="sub-heading" style={{ marginTop: 24 }}>Choghadiya (Auspicious Time Slots)</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div>
              <div className="text-bold" style={{ marginBottom: 6 }}>Day</div>
              <table className="report-table">
                <thead><tr><th>Slot</th><th>Name</th><th>Start</th><th>End</th></tr></thead>
                <tbody>
                  {safeArr(choghadiya.dayChoghadiya).map((c, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td className={c.name === 'Amrit' || c.name === 'Shubh' || c.name === 'Labh' ? 'text-bold' : 'text-muted'}>{c.name}</td>
                      <td>{c.start}</td>
                      <td>{c.end}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <div className="text-bold" style={{ marginBottom: 6 }}>Night</div>
              <table className="report-table">
                <thead><tr><th>Slot</th><th>Name</th><th>Start</th><th>End</th></tr></thead>
                <tbody>
                  {safeArr(choghadiya.nightChoghadiya).map((c, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td className={c.name === 'Amrit' || c.name === 'Shubh' || c.name === 'Labh' ? 'text-bold' : 'text-muted'}>{c.name}</td>
                      <td>{c.start}</td>
                      <td>{c.end}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ─────────── PLANETARY POSITIONS ─────────── */
function PlanetaryPositions({ data }) {
  const planets = safeArr(data?.kundli?.data?.planets);
  if (!planets.length) return <div className="page"><SectionHeading>Planetary Positions</SectionHeading><EmptyBlock /></div>;
  return (
    <div className="page">
      <SectionHeading>Planetary Positions</SectionHeading>
      <table className="report-table report-table--striped">
        <thead><tr><th>Planet</th><th>Sign</th><th>Degree</th><th>House</th><th>Nakshatra</th><th>Pada</th><th>Retro</th><th>Combust</th><th>Status</th></tr></thead>
        <tbody>
          {planets.map((p, i) => (
            <tr key={i}>
              <td className="text-bold">{PLANET_SYMBOLS[p.name] || ''} {p.name}</td>
              <td>{SIGN_SYMBOLS[p.sign] || ''} {p.sign}</td>
              <td>{p.degreeDMS || (p.degree?.toFixed(2) + '°')}</td>
              <td>{p.house ? <span className="house-num">{p.house}</span> : 'N/A'}</td>
              <td>{safe(p.nakshatra, 'N/A')}</td>
              <td>{safe(p.nakshatraPada, 'N/A')}</td>
              <td style={{ color: p.isRetrograde ? '#dc2626' : undefined, fontWeight: p.isRetrograde ? 700 : 400 }}>{p.isRetrograde ? 'R' : '—'}</td>
              <td style={{ color: p.isCombust ? '#ea580c' : undefined }}>{p.isCombust ? 'Yes' : '—'}</td>
              <td className="text-sm text-muted">{safe(p.houseStatus, '—')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─────────── HOUSE POSITIONS ─────────── */
function HousePositions({ data }) {
  const houses = safeArr(data?.kundli?.data?.houses);
  return (
    <div className="page">
      <SectionHeading>House Positions (Bhava)</SectionHeading>
      {houses.length > 0 ? (
        <table className="report-table report-table--striped">
          <thead><tr><th>House</th><th>Sign</th><th>Sign Lord</th><th>Planets</th></tr></thead>
          <tbody>
            {houses.map((h, i) => (
              <tr key={i}>
                <td className="text-bold">
                  <span className="house-num">{h.number}</span>
                  <span className="text-sm text-muted" style={{ marginLeft: 8 }}>{HOUSE_NAMES[h.number - 1] || ''}</span>
                </td>
                <td>{SIGN_SYMBOLS[h.sign] || ''} {h.sign}</td>
                <td>{PLANET_SYMBOLS[h.signLord] || ''} {h.signLord}</td>
                <td>
                  {safeArr(h.planets).map((p, j) => (
                    <span key={j} className="planet-badge" style={{ margin: '2px 4px' }}>{PLANET_SYMBOLS[p] || ''} {p}</span>
                  ))}
                  {!h.planets?.length && <span className="text-muted text-sm">Empty</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : <EmptyBlock />}
    </div>
  );
}

/* ─────────── MAJOR CHART (one per page) ─────────── */
function MajorChartPage({ svgData, title, description, label }) {
  return (
    <div className="page">
      <SectionHeading>{title}</SectionHeading>
      {description && <p className="text-muted" style={{ marginBottom: 16 }}>{description}</p>}
      <RenderSvg data={svgData} variant="major" title={title} label={label} />
    </div>
  );
}

/* ─────────── DIVISIONAL CHARTS (4 per page) ─────────── */
function DivisionalCharts({ data }) {
  const chartKeys = ['D3', 'D7', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'];
  const svgKeyMap = { D3: 'd3Svg', D7: 'd7Svg', D10: 'd10Svg', D12: 'd12Svg', D16: 'd16Svg', D20: 'd20Svg', D24: 'd24Svg', D27: 'd27Svg', D30: 'd30Svg', D40: 'd40Svg', D45: 'd45Svg', D60: 'd60Svg' };
  const pages = [];
  for (let i = 0; i < chartKeys.length; i += 4) {
    pages.push(chartKeys.slice(i, i + 4));
  }
  return (
    <>
      {pages.map((batch, pageIndex) => (
        <div className="page" key={pageIndex}>
          <SectionHeading>Divisional Charts {pageIndex === 0 ? '(D3–D60)' : '(continued)'}</SectionHeading>
          <div className="chart-grid-4">
            {batch.map((key) => {
              const svgData = data?.[svgKeyMap[key]];
              const info = DIVISION_INFO[key];
              return <RenderSvg key={key} data={svgData} variant="minor" title={info?.name || key} label={info?.focus || ''} />;
            })}
          </div>
        </div>
      ))}
    </>
  );
}

/* ─────────── VIMSHOTTARI DASHA ─────────── */
function VimshottariDasha({ data }) {
  const dashaResp = data?.dasha || {};
  const dashaData = dashaResp.data || {};
  const mahadashas = safeArr(dashaData.mahadashas);
  const currentNow = dashaResp.currentNow || {};

  return (
    <div className="page">
      <SectionHeading>Vimshottari Dasha Timeline</SectionHeading>
      <p className="text-muted text-sm" style={{ marginBottom: 12 }}>System: {dashaResp.system || 'Vimshottari'}</p>

      {currentNow.mahadasha && (
        <div className="alert-box alert-box--info">
          <div className="alert-box__title">⚡ Current Dasha Period</div>
          <div className="alert-box__body">
            <strong>Main:</strong> {PLANET_SYMBOLS[currentNow.mahadasha.planet]} {currentNow.mahadasha.planet}
            {currentNow.antardasha && <> | <strong>Sub:</strong> {PLANET_SYMBOLS[currentNow.antardasha.planet]} {currentNow.antardasha.planet}</>}
            {currentNow.pratyantar && <> | <strong>Sub-Sub:</strong> {PLANET_SYMBOLS[currentNow.pratyantar.planet]} {currentNow.pratyantar.planet}</>}
          </div>
        </div>
      )}

      {mahadashas.length > 0 ? (
        <table className="report-table report-table--striped">
          <thead><tr><th>Planet</th><th>Start</th><th>End</th><th>Sub-Periods</th></tr></thead>
          <tbody>
            {mahadashas.map((d, i) => {
              const isActive = currentNow.mahadasha?.planet === d.planet;
              return (
                <tr key={i} className={isActive ? 'dasha-current' : ''}>
                  <td className="text-bold">{PLANET_SYMBOLS[d.planet] || ''} {d.planet}</td>
                  <td>{formatDate(d.startDate)}</td>
                  <td>{formatDate(d.endDate)}</td>
                  <td className="text-sm text-muted">{safeArr(d.antardasha).length} antardashas</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : <EmptyBlock message="Vimshottari Dasha data not available." />}
    </div>
  );
}

/* ─────────── CURRENT DASHA DETAILS ─────────── */
function CurrentDashaDetails({ data }) {
  const cd = data?.currentDasha || {};
  const cdData = cd.currentDasha || {};
  const overall = cd.overallPrediction || {};
  const currentD = cdData.mahadasha || {};
  const antar = cdData.antardasha || {};
  const prat = cdData.pratyantar || {};

  return (
    <div className="page">
      <SectionHeading>Current Dasha Details</SectionHeading>
      {currentD.planet ? (
        <>
          <table className="report-table">
            <tbody>
              <tr><td className="text-bold">Mahadasha</td><td>{PLANET_SYMBOLS[currentD.planet]} {currentD.planet} ({formatDate(currentD.startDate)} – {formatDate(currentD.endDate)})</td></tr>
              <tr><td className="text-bold">Antardasha</td><td>{PLANET_SYMBOLS[antar.planet]} {antar.planet} ({formatDate(antar.startDate)} – {formatDate(antar.endDate)})</td></tr>
              <tr><td className="text-bold">Pratyantardasha</td><td>{PLANET_SYMBOLS[prat.planet]} {prat.planet} ({formatDate(prat.startDate)} – {formatDate(prat.endDate)})</td></tr>
            </tbody>
          </table>

          {overall.theme && <div className="sub-heading" style={{ marginTop: 16 }}>{overall.theme}</div>}
          {overall.positive && <p style={{ marginTop: 8 }}><strong>Positive:</strong> {overall.positive}</p>}
          {overall.challenges && <p style={{ marginTop: 4 }}><strong>Challenges:</strong> {overall.challenges}</p>}
          {overall.keyAdvice && <p style={{ marginTop: 4 }}><strong>Advice:</strong> {overall.keyAdvice}</p>}

          {currentD.effects && (
            <>
              <div className="sub-heading" style={{ marginTop: 16 }}>Mahadasha Effects ({currentD.planet})</div>
              {currentD.effects.career && <p className="text-sm"><strong>Career:</strong> {currentD.effects.career}</p>}
              {currentD.effects.finance && <p className="text-sm"><strong>Finance:</strong> {currentD.effects.finance}</p>}
              {currentD.effects.health && <p className="text-sm"><strong>Health:</strong> {currentD.effects.health}</p>}
              {currentD.effects.relationships && <p className="text-sm"><strong>Relationships:</strong> {currentD.effects.relationships}</p>}
            </>
          )}
          {antar.effects && (
            <>
              <div className="sub-heading" style={{ marginTop: 16 }}>Antardasha Effects ({antar.planet})</div>
              {antar.effects.career && <p className="text-sm"><strong>Career:</strong> {antar.effects.career}</p>}
              {antar.effects.finance && <p className="text-sm"><strong>Finance:</strong> {antar.effects.finance}</p>}
              {antar.effects.health && <p className="text-sm"><strong>Health:</strong> {antar.effects.health}</p>}
              {antar.effects.relationships && <p className="text-sm"><strong>Relationships:</strong> {antar.effects.relationships}</p>}
            </>
          )}
        </>
      ) : <EmptyBlock message="Current dasha details not available." />}
    </div>
  );
}

/* ─────────── CHARA & YOGINI DASHA ─────────── */
function OtherDashas({ data }) {
  const charaResp = data?.charaDasha || {};
  const charaData = charaResp.data || {};
  const charaDashas = safeArr(charaData.mahadashas);
  const yoginiResp = data?.yoginiDasha || {};
  const yoginiData = yoginiResp.data || {};
  const yoginiDashas = safeArr(yoginiData.mahadashas);

  return (
    <>
      <div className="page">
        <SectionHeading>Chara Dasha</SectionHeading>
        {charaDashas.length > 0 ? (
          <table className="report-table report-table--striped">
            <thead><tr><th>#</th><th>Lord</th><th>Sign</th><th>Start</th><th>End</th><th>Years</th></tr></thead>
            <tbody>
              {charaDashas.map((d, i) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td className="text-bold">{PLANET_SYMBOLS[d.lord] || ''} {safe(d.lord)}</td>
                  <td>{SIGN_SYMBOLS[d.sign] || ''} {d.sign}</td>
                  <td>{formatDate(d.startDate)}</td>
                  <td>{formatDate(d.endDate)}</td>
                  <td>{d.years ? `${d.years} yrs` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <EmptyBlock message="Chara Dasha data not available." />}
      </div>

      <div className="page">
        <SectionHeading>Yogini Dasha</SectionHeading>
        {yoginiDashas.length > 0 ? (
          <>
            {yoginiData.cycleYears && <p className="text-muted text-sm">Cycle Duration: {yoginiData.cycleYears} years | Start: {yoginiData.startYogini}</p>}
            <table className="report-table report-table--striped">
              <thead><tr><th>#</th><th>Yogini</th><th>Ruling Planet</th><th>Duration</th><th>Start</th><th>End</th></tr></thead>
              <tbody>
                {yoginiDashas.map((d, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td>
                    <td className="text-bold">{safe(d.yogini)}</td>
                    <td>{PLANET_SYMBOLS[d.rulingPlanet] || ''} {safe(d.rulingPlanet)}</td>
                    <td>{d.durationYears ? `${d.durationYears} yrs` : '—'}</td>
                    <td>{formatDate(d.startDate)}</td>
                    <td>{formatDate(d.endDate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : <EmptyBlock message="Yogini Dasha data not available." />}
      </div>
    </>
  );
}

/* ─────────── BHAVA CHALIT ─────────── */
function BhavaChalit({ data }) {
  const bhava = data?.bhavaChalit?.data?.wholeSign || {};
  const cusp = data?.bhavaChalit?.data?.cuspBased || {};
  const differences = safeArr(data?.bhavaChalit?.data?.differences);
  const wsHouses = safeArr(bhava.houses);

  return (
    <div className="page">
      <SectionHeading>Bhava Chalit (House Positions)</SectionHeading>
      <p className="text-muted text-sm" style={{ marginBottom: 16 }}>
        The Bhava Chalit chart shows the actual house placement of planets as per their cuspal positions.
      </p>
      {wsHouses.length > 0 ? (
        <>
          <table className="report-table report-table--striped">
            <thead><tr><th>House</th><th>Sign</th><th>Lord</th><th>Planets</th></tr></thead>
            <tbody>
              {wsHouses.map((h, i) => (
                <tr key={i}>
                  <td className="text-bold"><span className="house-num">{h.number}</span></td>
                  <td>{SIGN_SYMBOLS[h.sign] || ''} {h.sign}</td>
                  <td>{safe(h.signLord, '—')}</td>
                  <td>{safeArr(h.planets).map((p, j) => <span key={j} className="planet-badge" style={{ margin: '2px 4px' }}>{PLANET_SYMBOLS[p] || ''} {p}</span>)}
                    {!h.planets?.length && <span className="text-muted text-sm">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {differences.length > 0 && (
            <>
              <div className="sub-heading" style={{ marginTop: 16 }}>Cusp vs Whole Sign Differences</div>
              <table className="report-table">
                <thead><tr><th>Planet</th><th>Whole Sign House</th><th>Cusp House</th><th>Difference</th></tr></thead>
                <tbody>
                  {differences.map((d, i) => (
                    <tr key={i}>
                      <td className="text-bold">{PLANET_SYMBOLS[d.planet] || ''} {d.planet}</td>
                      <td>{d.wholeSignHouse}</td>
                      <td>{d.cuspBasedHouse}</td>
                      <td className="text-sm">{safe(d.significance, '')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      ) : <EmptyBlock message="Bhava Chalit data not available." />}
    </div>
  );
}

/* ─────────── YOGA ANALYSIS ─────────── */
function YogaAnalysis({ data }) {
  const yogas = safeArr(data?.yogas?.data?.yogas);
  const total = data?.yogas?.data?.totalYogasDetected;

  return (
    <div className="page">
      <SectionHeading>Yoga Analysis</SectionHeading>
      <p className="text-muted" style={{ marginBottom: 16 }}>
        Yogas are planetary combinations that produce specific results. {total ? `Total detected: ${total}` : ''}
      </p>
      {yogas.length > 0 ? (
        yogas.map((y, i) => (
          <div key={i} className={`yoga-item ${y.isMalefic ? 'yoga-item--inauspicious' : ''}`}>
            <div className="yoga-item__name">{safe(y.name, `Yoga ${i + 1}`)}</div>
            {safeArr(y.planetsInvolved).length > 0 && (
              <div style={{ marginTop: 4 }}>
                {y.planetsInvolved.map((p, j) => (
                  <span key={j} className="planet-badge" style={{ margin: '2px' }}>
                    {PLANET_SYMBOLS[p.name] || ''} {p.name} ({p.sign}, H{p.house})
                  </span>
                ))}
              </div>
            )}
            <div className="yoga-item__desc">{safe(y.description, 'No description available.')}</div>
            {y.strength && <div className="text-sm text-muted">Strength: {safe(y.strength.level || y.strength)}</div>}
            {y.prediction && <p className="text-sm" style={{ marginTop: 4 }}>{y.prediction}</p>}
          </div>
        ))
      ) : <EmptyBlock message="No specific yogas detected for this chart." />}
    </div>
  );
}

/* ─────────── DOSHA ANALYSIS ─────────── */
function DoshaAnalysis({ data }) {
  const doshas = safeArr(data?.doshas?.data);

  return (
    <div className="page">
      <SectionHeading>Dosha Analysis</SectionHeading>
      <p className="text-muted" style={{ marginBottom: 16 }}>Doshas are planetary afflictions that can cause challenges.</p>
      {doshas.length > 0 ? (
        doshas.map((d, i) => (
          <div key={i} className={`alert-box ${d.present ? 'alert-box--danger' : 'alert-box--success'}`}>
            <div className="alert-box__title">{d.present ? '⚠' : '✓'} {safe(d.name)} {d.present && d.severity && <span style={{ marginLeft: 8, fontSize: 12 }}>({d.severity})</span>}</div>
            <div className="alert-box__body">
              <p style={{ margin: 0 }}><strong>Status:</strong> {d.present ? 'Present' : 'Not Present'}</p>
              {d.description && <p style={{ marginTop: 8 }}>{d.description}</p>}
              {d.present && safeArr(d.remedies).length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <strong>Remedies:</strong>
                  <ul className="report-list" style={{ marginTop: 4 }}>
                    {d.remedies.map((r, j) => <li key={j}>{typeof r === 'string' ? r : safe(r)}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))
      ) : <EmptyBlock message="No dosha data available." />}
    </div>
  );
}

/* ─────────── TRANSIT ANALYSIS ─────────── */
function TransitAnalysis({ data }) {
  const transitResp = data?.transit || {};
  const transits = safeArr(transitResp.transits);

  return (
    <div className="page">
      <SectionHeading>Current Transit Analysis (Gochar)</SectionHeading>
      <p className="text-muted text-sm" style={{ marginBottom: 16 }}>
        Planetary transits as of: {formatDate(transitResp.transitDate)}
      </p>
      {transits.length > 0 ? (
        <table className="report-table report-table--striped">
          <thead><tr><th>Planet</th><th>Natal Sign</th><th>Transit Sign</th><th>Transit House</th><th>Prediction</th></tr></thead>
          <tbody>
            {transits.map((t, i) => (
              <tr key={i}>
                <td className="text-bold">{PLANET_SYMBOLS[t.planet] || ''} {t.planet}</td>
                <td>{SIGN_SYMBOLS[t.natalSign] || ''} {t.natalSign}</td>
                <td>{SIGN_SYMBOLS[t.transitSign] || ''} {t.transitSign}</td>
                <td>{t.transitHouse ? <span className="house-num">{t.transitHouse}</span> : '—'}</td>
                <td className="text-sm text-muted" style={{ maxWidth: 300 }}>{t.prediction ? t.prediction.substring(0, 100) + '...' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : <EmptyBlock message="Transit data not available." />}
    </div>
  );
}

/* ─────────── PREDICTION SECTION (career, finance, health, love) ─────────── */
function PredictionSection({ data, sectionKey, title, icon, subKey }) {
  const sectionData = data?.[sectionKey]?.data || {};
  const sub = sectionData[subKey] || {};
  const overview = sectionData.overview || '';

  return (
    <div className="page">
      <SectionHeading>{title}</SectionHeading>
      {overview && (
        <div className="summary-box" style={{ margin: '12px 0' }}>
          <div className="summary-box__icon">{icon}</div>
          <div className="summary-box__content">
            <div className="summary-box__title">Overview</div>
            <div className="summary-box__text">{overview}</div>
          </div>
        </div>
      )}
      {sub.positive ? (
        <>
          <div className="sub-heading">Positive Influences</div>
          <p>{sub.positive}</p>
          {sub.challenging && (
            <>
              <div className="sub-heading" style={{ marginTop: 12 }}>Challenges</div>
              <p>{sub.challenging}</p>
            </>
          )}
          <div style={{ marginTop: 16 }}>
            <table className="report-table">
              <tbody>
                {Object.keys(sub).filter(k => !['positive', 'challenging'].includes(k) && sub[k] != null && typeof sub[k] !== 'object').map(k => (
                  <tr key={k}><td className="text-bold">{k.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase())}</td><td>{Array.isArray(sub[k]) ? sub[k].join(', ') : String(sub[k])}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : !overview ? <EmptyBlock message={`${title} data not available.`} /> : null}

      {sectionData.remedy && (
        <div className="alert-box alert-box--info" style={{ marginTop: 12 }}>
          <div className="alert-box__title">٠ Remedies</div>
          <div className="alert-box__body">{sectionData.remedy}</div>
        </div>
      )}
    </div>
  );
}

/* ─────────── EDUCATION ─────────── */
function EducationSection({ data }) {
  const edu = data?.education?.data || {};
  return (
    <div className="page">
      <SectionHeading>📚 Education & Knowledge</SectionHeading>
      {edu.overview ? (
        <>
          <div className="summary-box" style={{ margin: '12px 0' }}>
            <div className="summary-box__icon">📚</div>
            <div className="summary-box__content">
              <div className="summary-box__title">Overview</div>
              <div className="summary-box__text">{edu.overview}</div>
            </div>
          </div>
          {edu.learningStyle && <p style={{ marginTop: 8 }}><strong>Learning Style:</strong> {edu.learningStyle}</p>}
          {edu.bestFields && <p style={{ marginTop: 4 }}><strong>Best Fields:</strong> {edu.bestFields}</p>}
          {edu.examLuck && <p style={{ marginTop: 4 }}><strong>Exam Luck:</strong> {edu.examLuck}</p>}
          {edu.bestPeriodsForStudy && <p style={{ marginTop: 4 }}><strong>Best Periods for Study:</strong> {edu.bestPeriodsForStudy}</p>}
          {safeArr(edu.studyTips).length > 0 && (
            <>
              <div className="sub-heading" style={{ marginTop: 12 }}>Study Tips</div>
              <ul className="report-list">{edu.studyTips.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </>
          )}
        </>
      ) : <EmptyBlock message="Education data not available." />}
    </div>
  );
}

/* ─────────── CHILD PROSPECTS ─────────── */
function ChildSection({ data }) {
  const child = data?.child?.data || {};
  return (
    <div className="page">
      <SectionHeading>👶 Child Prospects</SectionHeading>
      {child.overallAssessment ? (
        <>
          <div className="summary-box" style={{ margin: '12px 0' }}>
            <div className="summary-box__icon">👶</div>
            <div className="summary-box__content">
              <div className="summary-box__title">Overall Assessment</div>
              <div className="summary-box__text">{child.overallAssessment}</div>
            </div>
          </div>
          {child.prospects && <p style={{ marginTop: 8 }}><strong>Prospects:</strong> {child.prospects}</p>}
          {child.childNature && <p style={{ marginTop: 4 }}><strong>Child Nature:</strong> {child.childNature}</p>}
          {child.fifthHouse && <p style={{ marginTop: 4 }}><strong>5th House:</strong> {child.fifthHouse.sign} (Lord: {child.fifthHouse.lord})</p>}
          {child.timingNote && <p style={{ marginTop: 4 }}><strong>Timing:</strong> {child.timingNote}</p>}
          {safeArr(child.remedies).length > 0 && (
            <>
              <div className="sub-heading" style={{ marginTop: 12 }}>Remedies</div>
              <ul className="report-list">{child.remedies.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </>
          )}
        </>
      ) : <EmptyBlock message="Child prospects data not available." />}
    </div>
  );
}

/* ─────────── FOREIGN TRAVEL ─────────── */
function ForeignSection({ data }) {
  const foreign = data?.foreign?.data || {};
  return (
    <div className="page">
      <SectionHeading>✈️ Foreign Travel & Settlement</SectionHeading>
      {foreign.likelihood ? (
        <>
          <div className="summary-box" style={{ margin: '12px 0' }}>
            <div className="summary-box__icon">✈️</div>
            <div className="summary-box__content">
              <div className="summary-box__title">Settlement Likelihood: {foreign.likelihood} ({foreign.foreignSettlementScore}/100)</div>
              <div className="summary-box__text">{safeArr(foreign.reasons).join(' ')}</div>
            </div>
          </div>
          {foreign.bestTiming && <p style={{ marginTop: 8 }}><strong>Best Timing:</strong> {foreign.bestTiming}</p>}
          {foreign.favorableCountries && <p style={{ marginTop: 4 }}><strong>Favorable Directions:</strong> {foreign.favorableCountries}</p>}
          {foreign.twelfthHouse && <p style={{ marginTop: 4 }}><strong>12th House:</strong> {foreign.twelfthHouse.sign} (Lord: {foreign.twelfthHouse.lord})</p>}
          {safeArr(foreign.remedies).length > 0 && (
            <>
              <div className="sub-heading" style={{ marginTop: 12 }}>Remedies</div>
              <ul className="report-list">{foreign.remedies.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </>
          )}
        </>
      ) : <EmptyBlock message="Foreign travel data not available." />}
    </div>
  );
}

/* ─────────── LUCKY ELEMENTS ─────────── */
function LuckyElements({ data }) {
  const color = data?.luckyColor?.data || {};
  const number = data?.luckyNumber?.data || {};
  const day = data?.luckyDay?.data || {};
  const metal = data?.luckyMetal?.data || {};

  return (
    <div className="page">
      <SectionHeading>Lucky Elements</SectionHeading>
      <div className="lucky-grid">
        <div className="lucky-item">
          <span className="lucky-item__icon">🎨</span>
          <div className="lucky-item__label">Lucky Colors</div>
          <div className="lucky-item__value">{safe(color.luckyColors, 'N/A')}</div>
          {color.description && <div className="text-sm text-muted" style={{ marginTop: 6 }}>{color.description}</div>}
        </div>
        <div className="lucky-item">
          <span className="lucky-item__icon">🔢</span>
          <div className="lucky-item__label">Lucky Numbers</div>
          <div className="lucky-item__value">{safe(number.luckyNumbers, 'N/A')}</div>
          {number.description && <div className="text-sm text-muted" style={{ marginTop: 6 }}>{number.description}</div>}
        </div>
        <div className="lucky-item">
          <span className="lucky-item__icon">📅</span>
          <div className="lucky-item__label">Lucky Day</div>
          <div className="lucky-item__value">{safe(day.luckyDay, 'N/A')}</div>
          {day.description && <div className="text-sm text-muted" style={{ marginTop: 6 }}>{day.description}</div>}
        </div>
        <div className="lucky-item">
          <span className="lucky-item__icon">⚙️</span>
          <div className="lucky-item__label">Lucky Metal</div>
          <div className="lucky-item__value">{safe(metal.luckyMetal, 'N/A')}</div>
          {metal.luckyGemstone && <div className="text-sm" style={{ marginTop: 4 }}>Gemstone: {metal.luckyGemstone}</div>}
        </div>
      </div>
    </div>
  );
}

/* ─────────── GEMSTONE ─────────── */
function GemstoneRecommendation({ data }) {
  const gem = data?.gemstone || {};
  const gemstone = gem.gemstone || {};
  const wearing = gem.wearing || {};

  return (
    <div className="page">
      <SectionHeading>Gemstone Recommendation</SectionHeading>
      <p className="text-muted" style={{ marginBottom: 16 }}>
        Gemstones are worn to strengthen the ruling planet and channel positive energies.
      </p>
      {gemstone.name ? (
        <div className="card card--branded card--elevated">
          <div className="card-title">{gemstone.name} {gemstone.hindiName ? `(${gemstone.hindiName})` : ''}</div>
          <table className="report-table" style={{ marginTop: 12 }}>
            <tbody>
              <tr><td className="text-bold">Ruling Planet</td><td>{PLANET_SYMBOLS[gem.planet] || ''} {safe(gem.planet)}</td></tr>
              <tr><td className="text-bold">Color</td><td>{safe(gemstone.color)}</td></tr>
              <tr><td className="text-bold">Quality</td><td>{safe(gemstone.quality)}</td></tr>
              <tr><td className="text-bold">Origin</td><td>{safe(gemstone.origin)}</td></tr>
              <tr><td className="text-bold">Weight</td><td>{safe(wearing.weightRange)}</td></tr>
              <tr><td className="text-bold">Metal</td><td>{safe(wearing.metal)}</td></tr>
              <tr><td className="text-bold">Finger</td><td>{safe(wearing.finger)}</td></tr>
              <tr><td className="text-bold">Day</td><td>{safe(wearing.day)}</td></tr>
              <tr><td className="text-bold">Mantra</td><td>{safe(wearing.mantra)}</td></tr>
            </tbody>
          </table>
          {gem.recommendationReason && <p className="text-sm text-muted" style={{ marginTop: 12 }}>{gem.recommendationReason}</p>}
          {safeArr(wearing.dos).length > 0 && (
            <>
              <div className="sub-heading" style={{ marginTop: 12 }}>Do's</div>
              <ul className="report-list">{wearing.dos.map((d, i) => <li key={i}>{d}</li>)}</ul>
            </>
          )}
          {safeArr(wearing.donts).length > 0 && (
            <>
              <div className="sub-heading" style={{ marginTop: 12 }}>Don'ts</div>
              <ul className="report-list">{wearing.donts.map((d, i) => <li key={i}>{d}</li>)}</ul>
            </>
          )}
          {gem.alternateGemstone?.name && (
            <div className="alert-box alert-box--info" style={{ marginTop: 12 }}>
              <div className="alert-box__title">Alternate: {gem.alternateGemstone.name}</div>
              <div className="alert-box__body">{safe(gem.alternateGemstone.reason)}</div>
            </div>
          )}
        </div>
      ) : <EmptyBlock message="Gemstone recommendation not available." />}
    </div>
  );
}

/* ─────────── RUDRAKSHA ─────────── */
function Rudraksha({ data }) {
  const rudraData = data?.rudraksha?.data || {};
  const primary = rudraData.primaryRecommendation || {};
  const secondary = rudraData.secondaryRecommendation || {};

  return (
    <div className="page">
      <SectionHeading>Rudraksha Recommendation</SectionHeading>
      <p className="text-muted" style={{ marginBottom: 16 }}>
        Recommended based on Moon Sign: {rudraData.moonSign || 'N/A'}
      </p>
      {primary.name ? (
        <>
          <div className="card card--branded card--elevated">
            <div className="card-title">Primary: {primary.name}</div>
            <table className="report-table" style={{ marginTop: 12 }}>
              <tbody>
                {primary.deity && <tr><td className="text-bold">Deity</td><td>{primary.deity}</td></tr>}
                {primary.planet && <tr><td className="text-bold">Planet</td><td>{PLANET_SYMBOLS[primary.planet] || ''} {primary.planet}</td></tr>}
                {primary.rulingGod && <tr><td className="text-bold">Ruling God</td><td>{primary.rulingGod}</td></tr>}
                {primary.color && <tr><td className="text-bold">Color</td><td>{primary.color}</td></tr>}
                {primary.shape && <tr><td className="text-bold">Shape</td><td>{primary.shape}</td></tr>}
                {primary.origin && <tr><td className="text-bold">Origin</td><td>{primary.origin}</td></tr>}
                {primary.rarity && <tr><td className="text-bold">Rarity</td><td>{primary.rarity}</td></tr>}
              </tbody>
            </table>
            {primary.description && <p style={{ marginTop: 12 }}>{primary.description}</p>}
            {safeArr(primary.benefits).length > 0 && (
              <>
                <div className="sub-heading" style={{ marginTop: 12 }}>Benefits</div>
                <ul className="report-list">{primary.benefits.map((b, i) => <li key={i}>{b}</li>)}</ul>
              </>
            )}
          </div>
          {secondary.name && (
            <div className="alert-box alert-box--info" style={{ marginTop: 12 }}>
              <div className="alert-box__title">Secondary: {secondary.name}</div>
              <div className="alert-box__body">{safe(secondary.description)}</div>
            </div>
          )}
        </>
      ) : <EmptyBlock message="Rudraksha recommendation not available." />}
    </div>
  );
}

/* ─────────── ANNUAL FORECAST ─────────── */
function AnnualForecast({ data }) {
  const varsha = data?.varshaphal?.data || {};
  const year = varsha.returnDate?.date ? new Date(varsha.returnDate.date).getFullYear() : new Date().getFullYear();
  const predictions = safeArr(varsha.predictions);
  const muntha = varsha.muntha || {};

  return (
    <div className="page">
      <SectionHeading>Annual Forecast (Varshaphal) – {year}</SectionHeading>
      {varsha.yearSummary && (
        <div className="summary-box">
          <div className="summary-box__icon">📅</div>
          <div className="summary-box__content">
            <div className="summary-box__title">Year {year} Overview</div>
            <div className="summary-box__text">{varsha.yearSummary}</div>
          </div>
        </div>
      )}

      {muntha.prediction && (
        <div className="alert-box alert-box--info" style={{ marginTop: 12 }}>
          <div className="alert-box__title">Muntha Position: {muntha.position?.sign} (House {muntha.position?.house})</div>
          <div className="alert-box__body">{muntha.prediction}</div>
        </div>
      )}

      {predictions.length > 0 ? (
        predictions.map((p, i) => (
          <div key={i} className="prediction-block keep-together" style={{ marginTop: 12 }}>
            <div className="prediction-block__heading">{PLANET_SYMBOLS[p.planet] || ''} {p.planet} in House {p.house} ({p.sign})</div>
            {p.dignity && <div className="text-sm text-muted">Dignity: {p.dignity}</div>}
            <div className="prediction-block__text">{safe(p.prediction, '')}</div>
          </div>
        ))
      ) : !varsha.yearSummary ? <EmptyBlock message="Annual forecast data not available." /> : null}
    </div>
  );
}

/* ─────────── BACK PAGE ─────────── */
function BackPage({ branding }) {
  return (
    <div className="page back-page">
      <div className="back-brand">{branding.brandName}</div>
      <div className="back-tagline">{branding.headerText}</div>
      <div className="back-disclaimer">
        <strong>Disclaimer:</strong><br />
        {branding.backPageMessage || (
          <>
            This report is generated based on Vedic astrological principles and ancient shastraic texts.
            The predictions and recommendations are for general guidance purposes only and should not be
            considered as a substitute for professional medical, financial, or legal advice. The accuracy of
            predictions depends on the correctness of the birth data provided.
          </>
        )}
      </div>
      <div style={{ marginTop: 32, fontSize: 13, color: 'var(--report-text-secondary)' }}>
        <p>For consultations and personalized readings:</p>
        <p style={{ color: 'var(--brand-primary)', fontWeight: 600 }}>{branding.brandName}</p>
      </div>
      <div style={{ position: 'absolute', bottom: 32, fontSize: 12, color: 'var(--report-text-secondary)' }}>
        &copy; {new Date().getFullYear()} {branding.brandName}. All rights reserved.
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   MAIN REPORT TEMPLATE COMPONENT
   ═══════════════════════════════════════════════ */
export default function ReportTemplate({ data = {}, branding = {} }) {
  const b = {
    brandName: 'AstroVakta',
    logoUrl: '',
    headerText: 'Vedic Birth Chart Report',
    footerText: 'Generated by AstroVakta',
    primaryColor: '#7c3aed',
    secondaryColor: '#6366f1',
    coverTitle: 'Vedic Birth Chart Report',
    coverSubtitle: 'Comprehensive Kundali Analysis',
    backPageMessage: '',
    clientName: '',
    ...branding,
  };

  return (
    <div className="report-container" style={{ '--brand-primary': b.primaryColor, '--brand-secondary': b.secondaryColor }}>
      <CoverPage data={data} branding={b} />
      <TableOfContents />
      <BirthDetails data={data} branding={b} />
      <PlanetaryPositions data={data} />
      <HousePositions data={data} />

      <MajorChartPage svgData={data?.rasiSvg} title="D1 Rasi Chart" description="The D1 (Rasi) chart represents the physical body, material existence, and overall life blueprint." />
      <MajorChartPage svgData={data?.navamsaSvg} title="D9 Navamsa Chart" description="The Navamsa (D9) chart represents the soul, marriage, and dharma. It reveals the true strength of planets." label="Soul / Marriage Significance" />
      <MajorChartPage svgData={data?.moonSvg} title="Moon Chart (Chandra Kundali)" description="The Moon chart is used to analyze mental state, emotions, and mother-related matters." />
      <MajorChartPage svgData={data?.horaSvg} title="Hora Chart (D2)" description="The Hora (D2) chart represents wealth, resources, and financial stability." />
      <MajorChartPage svgData={data?.sudarshanaSvg} title="Sudarshana Chakra" description="The Sudarshana Chakra provides a comprehensive view of all 12 signs from each house as ascendant." />

      <DivisionalCharts data={data} />

      <VimshottariDasha data={data} />
      <CurrentDashaDetails data={data} />
      <OtherDashas data={data} />
      <BhavaChalit data={data} />
      <YogaAnalysis data={data} />
      <DoshaAnalysis data={data} />
      <TransitAnalysis data={data} />

      <PredictionSection data={data} sectionKey="career" title="💼 Career & Profession" icon="💼" subKey="career" />
      <PredictionSection data={data} sectionKey="finance" title="💰 Finance & Wealth" icon="💰" subKey="finance" />
      <PredictionSection data={data} sectionKey="health" title="🏥 Health & Wellness" icon="🏥" subKey="health" />
      <PredictionSection data={data} sectionKey="love" title="❤️ Love & Marriage" icon="❤️" subKey="love" />
      <EducationSection data={data} />
      <ChildSection data={data} />
      <ForeignSection data={data} />

      <LuckyElements data={data} />
      <GemstoneRecommendation data={data} />
      <Rudraksha data={data} />
      <AnnualForecast data={data} />
      <BackPage branding={b} />
    </div>
  );
}