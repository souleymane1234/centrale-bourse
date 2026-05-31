/** Indique si la valeur est un nom de dirigeant affichable (pas un titre de section). */
export function isValidExecutiveName(name) {
  if (!name) return false;
  const normalized = String(name).trim().toLowerCase();
  if (!normalized || normalized.length < 3) return false;
  if (normalized === 'dirigeants' || normalized === 'dirigeant') return false;
  if (/^dirigeants?\s*:?\s*$/i.test(normalized)) return false;
  return true;
}

/** Nettoie un nom extrait du texte dirigeants. */
function cleanPersonName(name) {
  if (!name) return null;
  let cleaned = String(name)
    .replace(/^(?:Mr|Mme|M\.|Mrs?\.?|Monsieur|Madame|Dr\.?)\s+/i, '')
    .replace(/\s*[-–]\s*DG\s*:.*$/i, '')
    .replace(/\s*\([^)]*\)\s*$/, '')
    .trim()
    .replace(/[,;.\-]+$/, '');
  if (!isValidExecutiveName(cleaned)) return null;
  cleaned = cleaned
    .replace(
      /\s+(?=(?:Directeur|Directrice|Secrétaire|Administrateur)\s+(?:Général|General|Adjoint|adjointe?|financier|Générale|Generale)\b).*/i,
      ''
    )
    .trim();
  if (!isValidExecutiveName(cleaned)) return null;
  if (/\b(?:Administrateur|Groupe|Finance)\b/i.test(cleaned)) return null;
  return cleaned;
}

/** Retire l'en-tête « Dirigeants » du texte brut Sikafinance. */
export function normalizeGovernanceRaw(raw) {
  if (!raw) return '';
  return String(raw)
    .replace(/^\s*:\s*/, '')
    .replace(/^Dirigeants?\s*:?\s*/i, '')
    .trim();
}

const CEO_PATTERNS = [
  /(?:PDG|Directeur\s+G[eéè]n[eéè]ral(?:e)?(?!\s+Adjoint)(?:\s+du\s+Groupe)?|Directrice\s+G[eéè]n[eéè]rale(?!\s+Adjoint)|Direction\s+G[eéè]n[eéè]rale|Managing\s+Director)\s*[^:]*:\s*(?:Mr|Mme|M\.|Mrs?\.?|-\s*)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)(?=\s*(?:DG\b|PCA\b|Directeur|Directrice|Président|Group|Administrateur|\(|$|;))/i,
  /\bDG\s*:\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)(?=\s*(?:DG\b|PCA\b|Directeur|Président|\(|$|;))/i,
  /Président\s+Directeur\s+G[eéè]n[eéè]ral\s*:\s*(?:Mr|Mme|M\.|Mrs?\.?)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)(?=\s|$)/i,
  /(?:Mr|Mme|Monsieur|Madame)\s+([A-Za-zÀ-ÿ][\w\s\-.]+?)\s*\(\s*Directeur\s+G[eéè]n[eéè]ral\s*\)/i,
  /([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)\s*,?\s*Directeur\s+g[eéè]n[eéè]ral\b/i,
  /([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)\s+Directeur\s+G[eéè]n[eéè]ral\b(?!\s+Adjoint)/i,
  /([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)\s+Managing\s+Director\b/i,
  /DG\s+NSIA\s+BANQUE\s*:\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)(?=\s|$)/i,
];

const CHAIRMAN_PATTERNS = [
  /Président\s+du\s+Conseil\s+d['’]Administration[^:]*:\s*(?:Mr|Mme|M\.|Mrs?\.?)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)(?=\s+Directeur|\s+DG\b|\s+PDG\b|\s+Administrateur|$)/i,
  /\bPCA\s*:\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)(?=\s+DG\b|\s+PDG\b|\s+Directeur|$)/i,
  /([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-\.\s]+?)\s+Chairman\b/i,
];

function matchFirst(patterns, raw) {
  for (const pattern of patterns) {
    const match = raw.match(pattern);
    const name = cleanPersonName(match?.[1]);
    if (name) return name;
  }
  return null;
}

/** Extrait le directeur général depuis le texte brut Sikafinance. */
export function parseChiefExecutiveFromRaw(raw) {
  if (!raw) return null;
  const text = normalizeGovernanceRaw(raw);
  if (!text) return null;
  return matchFirst(CEO_PATTERNS, text);
}

/** Extrait le président du CA depuis le texte brut Sikafinance. */
export function parseChairmanFromRaw(raw) {
  if (!raw) return null;
  return matchFirst(CHAIRMAN_PATTERNS, raw);
}

/** Calcule le cours de clôture précédent à partir du dernier cours et de la variation. */
export function computePreviousClose(quote) {
  const last = quote?.last;
  const variation = quote?.variation_pct;
  if (last != null && variation != null) {
    return Math.round(last / (1 + variation / 100));
  }
  return quote?.opening ?? null;
}

/** Affiche un site web sans protocole pour la fiche. */
export function formatWebsiteDisplay(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./, '');
  } catch {
    return url.replace(/^https?:\/\//, '').replace(/\/$/, '');
  }
}

/** Symbole boursier affiché (ex. ABJC). */
export function displaySymbol(company, quote) {
  if (company?.symbol) {
    const sym = String(company.symbol).trim();
    if (sym.length <= 6 && !sym.includes(' ')) return sym.toUpperCase();
  }
  const code = quote?.code;
  if (code) return code.split('.', 1)[0].toUpperCase();
  return company?.ticker || null;
}

/** Libellé secteur lisible pour le profil. */
export function formatIndustryLabel(sector) {
  if (!sector) return null;
  const normalized = String(sector).trim();
  if (normalized.includes('/')) {
    return normalized.split('/').pop().trim();
  }
  return normalized;
}
