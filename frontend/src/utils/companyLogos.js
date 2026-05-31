/**
 * Logos locaux : frontend/src/assets/{symbole}.{png|jpg|...}
 * Clés en minuscules (ex. bnbc.png → "bnbc").
 */
const logoModules = import.meta.glob('../assets/*.{png,jpg,jpeg,svg,webp}', {
  eager: true,
  import: 'default',
});

const EXT_PRIORITY = ['.png', '.jpg', '.jpeg', '.svg', '.webp'];

const logoByKey = {};

for (const [path, url] of Object.entries(logoModules)) {
  const filename = path.split('/').pop() || '';
  const dot = filename.lastIndexOf('.');
  const base = (dot > 0 ? filename.slice(0, dot) : filename).toLowerCase();
  const ext = dot > 0 ? filename.slice(dot).toLowerCase() : '';

  const current = logoByKey[base];
  if (!current || EXT_PRIORITY.indexOf(ext) < EXT_PRIORITY.indexOf(current.ext)) {
    logoByKey[base] = { url, ext };
  }
}

/** Codes Sikafinance / symboles → nom de fichier dans assets */
const SYMBOL_ALIASES = {
  sdsc: 'agl',
  boab: 'boa',
  boac: 'boa',
  boam: 'boa',
  boas: 'boa',
  boan: 'boa',
  boabf: 'cbibf',
  bicb: 'biic',
  ciec: 'cie',
  cfac: 'cfao',
};

function normalizeKey(value) {
  if (!value) return '';
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');
}

function resolveLogoKey({ symbol, ticker, code }) {
  const codeBase = code ? code.split('.')[0].toLowerCase() : '';
  const candidates = [
    codeBase,
    SYMBOL_ALIASES[codeBase],
    normalizeKey(symbol),
    normalizeKey(ticker),
    normalizeKey(symbol)?.slice(0, 4),
  ].filter(Boolean);

  for (const key of candidates) {
    if (logoByKey[key]) return key;
  }

  return null;
}

export function getCompanyLogoUrl({ symbol, ticker, code } = {}) {
  const key = resolveLogoKey({ symbol, ticker, code });
  return key ? logoByKey[key].url : null;
}

export function listAvailableLogoKeys() {
  return Object.keys(logoByKey).sort();
}
