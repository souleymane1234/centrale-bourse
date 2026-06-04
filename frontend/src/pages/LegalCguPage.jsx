import LegalDocumentLayout, { Section } from '../components/legal/LegalDocumentLayout';

export default function LegalCguPage() {
  return (
    <LegalDocumentLayout title="Conditions générales d'utilisation">
      <Section title="1. Objet">
        <p>
          Les présentes conditions régissent l&apos;accès et l&apos;utilisation de la plateforme
          Centrale Bourse, éditée par KS Solution. Centrale Bourse fournit des données, analyses et outils
          d&apos;aide à la décision sur les sociétés cotées à la Bourse régionale des Valeurs
          mobilières (BRVM).
        </p>
      </Section>

      <Section title="2. Nature du service">
        <p>
          Centrale Bourse n&apos;est pas un intermédiaire financier : aucun ordre d&apos;achat ou de
          vente ne peut être passé via la plateforme. Les informations publiées sont fournies à
          titre informatif et ne constituent pas un conseil en investissement personnalisé.
        </p>
      </Section>

      <Section title="3. Compte utilisateur">
        <p>
          L&apos;inscription nécessite des informations exactes. Vous êtes responsable de la
          confidentialité de vos identifiants. L&apos;accès à la plateforme est gratuit pour le
          moment ; une offre payante pourra être proposée ultérieurement.
        </p>
      </Section>

      <Section title="4. Évolution du service">
        <p>
          KS Solution se réserve le droit de proposer à l&apos;avenir des formules payantes ou des
          fonctionnalités additionnelles. Les utilisateurs seront informés avant toute mise en place
          de facturation.
        </p>
      </Section>

      <Section title="5. Liste de suivi et alertes">
        <p>
          Les fonctionnalités de liste de suivi et d&apos;alertes de cours permettent de suivre des
          sociétés et des seuils de prix. Les notifications push, email ou SMS pourront être
          activées ultérieurement ; l&apos;état des alertes reste consultable dans votre espace Suivi.
        </p>
      </Section>

      <Section title="6. Données et disponibilité">
        <p>
          Les cours et indicateurs proviennent de sources publiques et peuvent présenter un léger
          décalage. KS Solution s&apos;efforce d&apos;assurer la fiabilité du service sans garantir
          une disponibilité ininterrompue.
        </p>
      </Section>

      <Section title="7. Propriété intellectuelle">
        <p>
          Les contenus, marques, interfaces et logiciels de Centrale Bourse sont protégés. Toute
          reproduction ou extraction automatisée non autorisée est interdite.
        </p>
      </Section>

      <Section title="8. Limitation de responsabilité">
        <p>
          KS Solution ne saurait être tenue responsable des pertes financières liées à des
          décisions prises sur la base des informations affichées. L&apos;utilisateur investit sous
          sa seule responsabilité.
        </p>
      </Section>

      <Section title="9. Résiliation">
        <p>
          Vous pouvez cesser d&apos;utiliser le service à tout moment. KS Solution peut suspendre
          un compte en cas de violation des présentes conditions ou d&apos;usage frauduleux.
        </p>
      </Section>

      <Section title="10. Droit applicable">
        <p>
          Les présentes CGU sont soumises au droit applicable dans le pays d&apos;exploitation du
          service. Pour toute question : contact@ks-solution.com (adresse indicative à adapter).
        </p>
      </Section>
    </LegalDocumentLayout>
  );
}
