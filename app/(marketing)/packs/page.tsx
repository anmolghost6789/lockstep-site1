import { redirect } from 'next/navigation';

// The site is a single page; old links to /packs land on the packs section.
export default function PacksPage() {
  redirect('/#packs');
}
