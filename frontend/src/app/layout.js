import './globals.css';
import { AuthProvider } from '@/context/AuthContext';

export const metadata = {
  title: 'Personal AI Action Agent',
  description: 'AI-powered personal automation platform for managing GitHub, LinkedIn, and more through natural language.',
  keywords: ['AI', 'automation', 'GitHub', 'LinkedIn', 'personal agent'],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
