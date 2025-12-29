/**
 * Language Switch Component
 * Supports switching between Chinese and English.
 */

'use client';

import { Globe } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { LANGUAGES, type Language } from '@/lib/i18n';

interface LanguageSwitchProps {
  className?: string;
}

export function LanguageSwitch({ className = '' }: LanguageSwitchProps) {
  const { language, setLanguage } = useLanguage();

  const handleToggle = () => {
    const newLang: Language = language === 'zh' ? 'en' : 'zh';
    setLanguage(newLang);
  };

  const currentLangInfo = LANGUAGES.find(l => l.code === language);

  return (
    <button
      onClick={handleToggle}
      className={`flex items-center gap-1.5 px-2 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors ${className}`}
      title={language === 'zh' ? 'Switch to English' : '切换到中文'}
    >
      <Globe className="w-4 h-4" />
      <span className="hidden sm:inline">{language === 'zh' ? 'English' : '中文'}</span>
    </button>
  );
}

/**
 * Language Dropdown (Optional more complete version)
 */
export function LanguageDropdown({ className = '' }: LanguageSwitchProps) {
  const { language, setLanguage } = useLanguage();

  return (
    <div className={`relative group ${className}`}>
      <button
        className="flex items-center gap-1.5 px-2 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
      >
        <Globe className="w-4 h-4" />
        <span>{LANGUAGES.find(l => l.code === language)?.nativeName}</span>
      </button>
      <div className="absolute right-0 mt-1 py-1 bg-white border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 min-w-[100px]">
        {LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`w-full px-3 py-1.5 text-left text-sm hover:bg-gray-100 transition-colors ${
              language === lang.code ? 'text-gray-900 font-medium bg-gray-50' : 'text-gray-600'
            }`}
          >
            {lang.nativeName}
          </button>
        ))}
      </div>
    </div>
  );
}
