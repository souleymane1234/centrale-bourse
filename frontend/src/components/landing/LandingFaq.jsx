import { useState } from 'react';
import { Minus, Plus } from 'lucide-react';

const FAQ_ITEMS = [
  {
    id: 'buy-shares',
    question: 'Puis-je acheter des actions directement sur la plateforme ?',
    answer:
      'Non. Centrale Bourse est un outil d’analyse et d’information boursière : cours, graphiques, comparatifs et actualités. Les ordres d’achat ou de vente passent par votre banque, SGI ou courtier habilité sur la BRVM.',
  },
  {
    id: 'beginners',
    question: 'Est-ce adapté aux débutants ?',
    answer:
      'Oui. L’interface est pensée pour être lisible sans jargon excessif : fiches sociétés, courbes, indicateurs expliqués et comparaisons par secteur. L’essai gratuit de 5 jours permet de découvrir la plateforme à votre rythme.',
  },
  {
    id: 'data-reliability',
    question: 'Les données sont-elles fiables ?',
    answer:
      'Les cours, volumes et informations de marché proviennent de sources publiques (BRVM, agrégateurs financiers reconnus). Elles sont rafraîchies régulièrement. Comme tout marché, un léger décalage peut exister ; vérifiez les chiffres critiques avant une décision d’investissement.',
  },
  {
    id: 'trial-card',
    question: 'Ai-je besoin d’une carte de crédit pour commencer l’essai gratuit ?',
    answer:
      'Non. L’essai de 5 jours ne demande ni carte bancaire ni paiement à l’inscription. Vous créez un compte et accédez à la plateforme ; le paiement n’intervient que si vous choisissez de vous abonner à la fin de l’essai.',
  },
  {
    id: 'companies',
    question: 'Quelles entreprises sont couvertes ?',
    answer:
      'Toutes les sociétés cotées à la Bourse régionale des Valeurs mobilières (BRVM) : actions, secteurs, cours du jour, historiques, analyses et actualités liées au marché régional.',
  },
  {
    id: 'renewal',
    question: 'Le réabonnement est-il automatique ?',
    answer:
      'Non. Aucun prélèvement automatique n’est effectué à l’échéance de votre abonnement. À la fin de la période (essai, mois ou année), vous décidez vous-même de renouveler depuis votre profil, via Mobile Money (Wave, Orange Money, MTN Money, Moov Money) ou carte Visa.',
  },
];

function FaqItem({ item, isOpen, onToggle }) {
  const panelId = `faq-panel-${item.id}`;
  const buttonId = `faq-button-${item.id}`;

  return (
    <div className="border-b border-slate-900/90">
      <button
        type="button"
        id={buttonId}
        aria-expanded={isOpen}
        aria-controls={panelId}
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-6 py-6 text-left transition hover:text-slate-600"
      >
        <span className="text-base font-medium text-slate-900 sm:text-lg">{item.question}</span>
        <span className="flex h-8 w-8 shrink-0 items-center justify-center text-slate-900">
          {isOpen ? (
            <Minus className="h-5 w-5" strokeWidth={1.75} aria-hidden />
          ) : (
            <Plus className="h-5 w-5" strokeWidth={1.75} aria-hidden />
          )}
        </span>
      </button>
      <div
        id={panelId}
        role="region"
        aria-labelledby={buttonId}
        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
          isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div className="overflow-hidden">
          <p className="pb-6 pr-12 text-sm leading-relaxed text-slate-600 sm:text-base">{item.answer}</p>
        </div>
      </div>
    </div>
  );
}

export default function LandingFaq() {
  const [openId, setOpenId] = useState(null);

  const toggle = (id) => {
    setOpenId((current) => (current === id ? null : id));
  };

  return (
    <section
      id="faq"
      className="relative overflow-hidden border-t border-slate-200/80 bg-white py-28 sm:py-32 lg:py-36"
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        aria-hidden
        style={{
          backgroundImage: `
            radial-gradient(circle at 1px 1px, rgb(148 163 184 / 0.35) 1px, transparent 0),
            linear-gradient(rgb(226 232 240 / 0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgb(226 232 240 / 0.2) 1px, transparent 1px)
          `,
          backgroundSize: '24px 24px, 48px 48px, 48px 48px',
        }}
      />

      <div className="relative mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-widest text-sky-600">FAQ</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Questions et réponses
          </h2>
        </div>

        <div className="mt-12 border-t border-slate-900/90">
          {FAQ_ITEMS.map((item) => (
            <FaqItem
              key={item.id}
              item={item}
              isOpen={openId === item.id}
              onToggle={() => toggle(item.id)}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
