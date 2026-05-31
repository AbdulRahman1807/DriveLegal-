import type { Metadata, Viewport } from 'next';
import './globals.css';

export const viewport: Viewport = {
  themeColor: '#0a0a0c',
};

export const metadata: Metadata = {
  title: 'DriveLegal | Indian Traffic Law AI',
  description: 'AI-powered traffic law advisor for the Indian Motor Vehicles Act. Get instant legal citations, fine calculations, and compliance checks.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'DriveLegal',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
      </head>
      <body suppressHydrationWarning>
        <div className="app-container">
          <header>
            <h1>DriveLegal</h1>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
