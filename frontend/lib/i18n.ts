import en from '../locales/en.json';
import ar from '../locales/ar.json';

export type Language = 'en' | 'ar';

export const translations: Record<Language, Record<string, string>> = {
  en,
  ar,
};

export function getTranslation(language: Language, key: string): string {
  return translations[language][key] || key;
}
