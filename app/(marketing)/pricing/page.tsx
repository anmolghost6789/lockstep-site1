import { redirect } from 'next/navigation';

// The site is a single page; old links to /pricing land on the pricing section.
export default function PricingPage() {
  redirect('/#pricing');
}
