import { HeroSection } from '../home';
import { FAQSection } from '@/components/site/faq-section';
import { LifecycleSection } from '@/components/site/sections';
import { GovernanceSection, PilotSection } from '@/components/site/home-sections';
import { PacksSection } from '@/components/site/packs-section';
import { PricingSection } from '@/components/site/pricing-section';

/**
 * One page: what it is (hero), how it works (the lifecycle journey), the governance that runs with every phase,
 * the domain packs that give agents industry knowledge, pricing, the pilot, and a short FAQ.
 */
export default function Homepage() {
  return (
    <div className="@container">
      <div className="container-frame">
        <HeroSection />
      </div>
      <div className="bg-neutral-50/60 dark:bg-white/[0.02]">
        <div className="container-frame">
          <LifecycleSection />
        </div>
      </div>
      <div className="container-frame">
        <GovernanceSection />
      </div>
      <div className="bg-neutral-50/60 dark:bg-white/[0.02]">
        <div className="container-frame">
          <PacksSection />
        </div>
      </div>
      <div className="container-frame">
        <PricingSection />
      </div>
      <div className="container-frame">
        <PilotSection />
      </div>
      <div className="container-frame">
        <FAQSection />
      </div>
    </div>
  );
}
