/** @type {import('next').NextConfig} */
const nextConfig = {
  // The registry seeds itself from the skill pack on first run, so ship those files with the server bundle.
  outputFileTracingIncludes: { '/**': ['./adlc-agent/**/*', './packs/**/*'] },
  // Pack uploads can be a few MB; Vercel's own request limit is about 4.5 MB.
  experimental: { serverActions: { bodySizeLimit: '4.5mb' } },
  serverExternalPackages: ['postgres'],
};
export default nextConfig;
