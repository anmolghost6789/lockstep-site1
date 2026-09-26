import type { Metadata } from 'next';

import { PricingSection } from '@/components/site/pricing-section';
import { PilotSection } from '@/components/site/home-sections';

export const metadata: Metadata = { title: 'Pricing · Lockstep' };

export default function PricingPage() {
  return (
    <div className="container-frame pt-6">
      <PricingSection />
      <PilotSection />
    </div>
  );
}
