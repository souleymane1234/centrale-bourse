import LegalDocumentLayout, { Section } from '../components/legal/LegalDocumentLayout';

export default function LegalPrivacyPage() {
  return (
    <LegalDocumentLayout title="Politique de confidentialité">
      <Section title="1. Responsable du traitement">
        <p>
          KS Solution, éditeur de Centrale Bourse, traite vos données personnelles dans le cadre de la
          gestion des comptes, des abonnements et de l&apos;amélioration du service.
        </p>
      </Section>

      <Section title="2. Données collectées">
        <ul className="list-disc space-y-1 pl-5">
          <li>Identité : nom, adresse email, numéro de téléphone (optionnel)</li>
          <li>Compte : mot de passe chiffré, historique d&apos;abonnement</li>
          <li>Usage : liste de suivi, alertes de cours, préférences de navigation</li>
          <li>Technique : logs de connexion, adresse IP, type de navigateur</li>
        </ul>
      </Section>

      <Section title="3. Finalités">
        <p>
          Vos données servent à créer et sécuriser votre compte, gérer l&apos;essai et
          l&apos;abonnement, afficher vos listes et alertes, assurer le support client et respecter
          nos obligations légales.
        </p>
      </Section>

      <Section title="4. Base légale">
        <p>
          Le traitement repose sur l&apos;exécution du contrat (utilisation du service), votre
          consentement lorsque requis (communications marketing) et l&apos;intérêt légitime
          (sécurité, amélioration produit).
        </p>
      </Section>

      <Section title="5. Durée de conservation">
        <p>
          Les données de compte sont conservées tant que le compte est actif, puis archivées ou
          supprimées selon la réglementation applicable. Les données de facturation peuvent être
          conservées plus longtemps pour obligations comptables.
        </p>
      </Section>

      <Section title="6. Partage des données">
        <p>
          Nous ne vendons pas vos données. Elles peuvent être partagées avec des prestataires
          strictement nécessaires (hébergement, paiement) sous contrat de confidentialité, ou sur
          demande des autorités compétentes.
        </p>
      </Section>

      <Section title="7. Sécurité">
        <p>
          Des mesures techniques et organisationnelles sont mises en place (chiffrement des mots de
          passe, accès restreint, sauvegardes). Aucun système n&apos;étant infaillible, nous vous
          invitons à protéger vos identifiants.
        </p>
      </Section>

      <Section title="8. Vos droits">
        <p>
          Vous pouvez demander l&apos;accès, la rectification, l&apos;effacement, la limitation ou
          l&apos;opposition au traitement, ainsi que la portabilité de vos données, en nous
          contactant depuis votre profil ou par email. Vous pouvez introduire une réclamation
          auprès de l&apos;autorité de protection des données compétente.
        </p>
      </Section>

      <Section title="9. Cookies et traceurs">
        <p>
          Le site peut utiliser des cookies essentiels au fonctionnement (session, préférences) et,
          le cas échéant, des outils de mesure d&apos;audience anonymisés. Vous pouvez configurer
          votre navigateur pour les refuser.
        </p>
      </Section>

      <Section title="10. Modifications">
        <p>
          Cette politique peut être mise à jour. La date en tête de page indique la dernière
          révision. Les changements substantiels vous seront signalés par email ou notification
          in-app lorsque cela est possible.
        </p>
      </Section>
    </LegalDocumentLayout>
  );
}
