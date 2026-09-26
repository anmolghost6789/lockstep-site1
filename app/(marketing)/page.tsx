import { HeroSection } from '../home';
import { FAQSection } from '@/components/site/faq-section';
import { LifecycleSection } from '@/components/site/sections';
import { PilotSection, ShiftSection, TrustSection } from '@/components/site/home-sections';

/**
 * Five things, in order: what it is (hero), why now (the shift), how it works (the lifecycle),
 * why teams trust it, and the one thing to do next (book a pilot). Everything else lives on
 * /pricing, /packs, the registry, or in the decks.
 */
export default function Homepage() {
  return (
    <div className="@container">
      <div className="container-frame">
        <HeroSection />
      </div>
      <div className="container-frame">
        <ShiftSection />
      </div>
      <div className="bg-neutral-50/60 dark:bg-white/[0.02]">
        <div className="container-frame">
          <LifecycleSection />
        </div>
      </div>
      <div className="container-frame">
        <TrustSection />
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
