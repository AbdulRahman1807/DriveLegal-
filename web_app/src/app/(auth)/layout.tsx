import type { Viewport } from 'next';

export const viewport: Viewport = {
  themeColor: '#FAFBFC',
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <div className="auth-root">{children}</div>;
}
