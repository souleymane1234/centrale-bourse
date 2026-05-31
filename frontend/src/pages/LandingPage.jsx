import LandingCta from '../components/landing/LandingCta';
import LandingFooter from '../components/landing/LandingFooter';
import LandingFaq from '../components/landing/LandingFaq';
import LandingFeaturesShowcase from '../components/landing/LandingFeaturesShowcase';
import LandingHero from '../components/landing/LandingHero';
import LandingPricing from '../components/landing/LandingPricing';

export default function LandingPage() {
  return (
    <div className="bg-[#f4f7fa]">
      <LandingHero />
      <LandingFeaturesShowcase />
      <LandingPricing />
      <LandingFaq />
      <LandingCta />

      <LandingFooter />
    </div>
  );
}
