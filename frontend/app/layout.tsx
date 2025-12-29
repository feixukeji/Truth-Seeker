import type { Metadata, Viewport } from 'next';
import { headers } from 'next/headers';
import { LanguageProvider } from '@/hooks/useLanguage';
import { translations, type Language } from '@/lib/i18n';
import './globals.css';

async function getLanguage(): Promise<Language> {
  const headersList = await headers();
  const acceptLanguage = headersList.get('accept-language');
  
  // Simple language detection logic
  if (acceptLanguage) {
    const preferred = acceptLanguage.split(',')[0].toLowerCase();
    if (preferred.startsWith('en')) {
      return 'en';
    }
  }
  
  return 'zh';
}

export async function generateMetadata(): Promise<Metadata> {
  const lang = await getLanguage();
  
  // SEO friendly description with both languages
  const description = '使用 AI 帮助您判断生活中常见论断的真伪，破除迷思。Verify claims with AI-powered fact-checking.';

  // Title prioritized by user language
  const title = lang === 'zh' 
    ? '去伪存真 - AI 论断真伪判断助手 | Truth Seeker' 
    : 'Truth Seeker - AI Claim Verifier | 去伪存真';

  return {
    title,
    description,
    keywords: '事实核查, AI, 论断验证, 科学证据, fact-check, truth seeker',
  };
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const lang = await getLanguage();
  
  return (
    <html lang={lang === 'zh' ? 'zh-CN' : 'en'} suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 antialiased">
        <LanguageProvider initialLanguage={lang}>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
