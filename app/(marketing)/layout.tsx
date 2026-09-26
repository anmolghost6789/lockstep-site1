import { redirect } from 'next/navigation';

import { SiteHeader } from '@/components/site/site-header';
import { SiteFooter } from '@/components/site/site-footer';

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  // Client-hosted Enterprise installs run the registry only.
  if (process.env.REGISTRY_ONLY === 'true') redirect('/registry');
  return (
    <>
      <SiteHeader />
      {children}
      <SiteFooter />
    </>
  );
}
