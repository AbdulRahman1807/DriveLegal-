import type { Metadata, Viewport } from 'next';
import './globals.css';
import { AuthProvider } from '@/services/AuthContext';

export const viewport: Viewport = {
  themeColor: '#ffffff',
};

export const metadata: Metadata = {
  title: 'DriveLegal | Indian Traffic Law AI',
  description:
    'AI-powered traffic law advisor for the Indian Motor Vehicles Act.',
  manifest: '/manifest.json',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
