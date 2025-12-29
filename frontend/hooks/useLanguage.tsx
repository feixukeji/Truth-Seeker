/**
 * Language Context and Hook
 * Provides global language state management and persistence.
 */

'use client';

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { type Language, type Translations, getTranslations, DEFAULT_LANGUAGE } from '@/lib/i18n';

const LANGUAGE_STORAGE_KEY = 'truth-seeker-language';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
  initialLanguage?: Language;
}

export function LanguageProvider({ children, initialLanguage = DEFAULT_LANGUAGE }: LanguageProviderProps) {
  const [language, setLanguageState] = useState<Language>(initialLanguage);
  const [isHydrated, setIsHydrated] = useState(false);

  // Get translations for current language
  const t = getTranslations(language);

  // Set language and save to localStorage
  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  }, []);

  // Initialization: Read language setting from localStorage
  useEffect(() => {
    const savedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY) as Language | null;
    if (savedLanguage && (savedLanguage === 'zh' || savedLanguage === 'en')) {
      setLanguageState(savedLanguage);
    } else {
      // Try to detect browser language
      const browserLang = navigator.language.toLowerCase();
      if (browserLang.startsWith('zh')) {
        setLanguageState('zh');
      } else {
        setLanguageState('en');
      }
    }
    setIsHydrated(true);
  }, []);

  // Update html lang attribute and page title when language changes
  useEffect(() => {
    if (isHydrated) {
      document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
      
      // Update page title
      const suffix = language === 'zh' 
        ? ' - AI 论断真伪判断助手' 
        : ' - AI Claim Verifier';
      document.title = t.appName + suffix;
    }
  }, [language, isHydrated, t.appName]);

  // Avoid hydration mismatch
  if (!isHydrated) {
    return (
      <LanguageContext.Provider value={{ language: DEFAULT_LANGUAGE, setLanguage, t: getTranslations(DEFAULT_LANGUAGE) }}>
        {children}
      </LanguageContext.Provider>
    );
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * Hook to use language context
 */
export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
