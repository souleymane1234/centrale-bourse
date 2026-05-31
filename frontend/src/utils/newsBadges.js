const BADGE_STYLES = {
  marche: 'bg-emerald-100 text-emerald-800',
  brvm: 'bg-brand-50 text-brand-800',
  societe: 'bg-indigo-100 text-indigo-800',
  dividende: 'bg-amber-100 text-amber-900',
  communique: 'bg-slate-100 text-slate-800',
  obligation: 'bg-violet-100 text-violet-800',
};

export function newsBadgeClass(badgeKey) {
  return BADGE_STYLES[badgeKey] || BADGE_STYLES.brvm;
}
