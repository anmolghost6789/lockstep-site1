import type { Metadata } from 'next';
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import '@fontsource/spectral/300.css';
import '@fontsource/spectral/400.css';
import '@fontsource-variable/inter';
import './globals.css';

import { ThemeProvider } from '@/components/theme-provider';

export const metadata: Metadata = {
  title: 'Lockstep: the agentic development lifecycle for VS Code',
  description:
    'AI agents plan, build, test and ship inside VS Code. A person signs off at every gate, and every phase leaves a versioned artifact in your repo.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`} data-scroll-behavior="smooth" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
