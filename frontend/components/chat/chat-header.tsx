'use client';

import { useLanguage } from '@/lib/language-context';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';

interface ChatHeaderProps {
  onToggleSidebar: () => void;
}

export function ChatHeader({ onToggleSidebar }: ChatHeaderProps) {
  const { t, isRTL } = useLanguage();
  const { user } = useSelector((state: RootState) => state.auth);

  // Get user initials from name
  const getInitials = (name: string | undefined) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="chat-header h-16 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-6 bg-white dark:bg-gray-950 shrink-0 z-10">
      <div className="flex items-center gap-3">
        {/* Mobile sidebar toggle */}
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Toggle sidebar"
        >
          <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Logo */}
        <div className="size-9 rounded-lg flex items-center justify-center text-white shadow-md"
          style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)' }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" />
          </svg>
        </div>
        <h1 className="text-xl font-bold tracking-tight text-gray-800 dark:text-gray-100">
          {t('brandName')} <span className="text-teal-600 dark:text-teal-400">AI</span>
        </h1>
      </div>

      {/* User profile */}
      <div className="flex items-center gap-4">
        <div className={`hidden sm:block ${isRTL ? 'text-left' : 'text-right'}`}>
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 leading-none">{user?.name || 'User'}</p>
          <p className="text-[11px] text-gray-500 dark:text-gray-500 mt-0.5">{user?.email || ''}</p>
        </div>
        <div className="size-10 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center text-white font-bold text-sm border-2 border-teal-200 dark:border-teal-800 shadow-md">
          {getInitials(user?.name)}
        </div>
      </div>
    </header>
  );
}
