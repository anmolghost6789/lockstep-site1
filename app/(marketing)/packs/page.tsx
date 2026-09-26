import type { Metadata } from 'next';

import { PacksSection } from '@/components/site/packs-section';
import { PilotSection } from '@/components/site/home-sections';

export const metadata: Metadata = { title: 'Packs · Lockstep' };

export default function PacksPage() {
  return (
    <div className="container-frame pt-6">
      <PacksSection />
      <PilotSection />
    </div>
  );
}
