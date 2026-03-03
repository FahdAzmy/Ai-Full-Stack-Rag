'use client';

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/lib/language-context';
import { useTheme } from '@/lib/theme-context';
import { useDispatch } from 'react-redux';
import { logout } from '@/store/auth/auth-actions';
import { AppDispatch } from '@/store/store';
import { useRouter } from 'next/navigation';
import { Conversation } from './chat-layout';
import { 
  Settings, 
  LogOut, 
  Globe, 
  Moon, 
  Sun, 
  ChevronRight, 
  Plus, 
  MessageSquare,
  Check
} from 'lucide-react';

interface ChatSidebarProps {
  conversations: Conversation[];
  isOpen: boolean;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
}

export function ChatSidebar({
  conversations,
  isOpen,
  onNewConversation,
  onSelectConversation,
}: ChatSidebarProps) {
  const { t, language, setLanguage, isRTL } = useLanguage();
  const { theme, setTheme, isDark } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const router = useRouter();
  
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  // Close settings when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setSettingsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    dispatch(logout());
    router.push('/');
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 z-20 lg:hidden" onClick={() => {}} />
      )}

      <aside
        className={`
          chat-sidebar w-72 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
          flex flex-col shrink-0 transition-all duration-300 ease-in-out z-30
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:border-0 lg:overflow-hidden'}
          fixed lg:relative inset-y-0 start-0 lg:inset-auto
          h-full
        `}
      >
        {/* New Conversation Button */}
        <div className="p-4">
          <button
            onClick={onNewConversation}
            className="w-full flex items-center justify-center gap-2 text-white font-semibold py-2.5 px-4 rounded-xl hover:opacity-90 transition-all duration-200 shadow-md hover:shadow-lg active:scale-[0.98]"
            style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)' }}
          >
            <Plus className="w-5 h-5" />
            <span>{t('chatNewConversation')}</span>
          </button>
        </div>

        {/* Conversations list */}
        <nav className="flex-1 overflow-y-auto px-3 space-y-1 chat-scrollbar">
          <div className="py-2">
            <p className="px-3 text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-2">
              {t('chatRecentChats')}
            </p>

            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-start transition-all duration-200 group mb-0.5
                  ${conv.active
                    ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 border border-teal-100 dark:border-teal-800'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent'
                  }
                `}
              >
                <MessageSquare
                  className={`w-5 h-5 shrink-0 ${conv.active ? 'text-teal-600 dark:text-teal-400' : 'text-gray-400 dark:text-gray-600'}`}
                />
                <span className="text-sm font-medium truncate">{conv.title}</span>
              </button>
            ))}
          </div>
        </nav>

        {/* Settings Button Container */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-800 relative" ref={settingsRef}>
          {/* Settings Menu Popup */}
          {settingsOpen && (
            <div 
              className={`absolute bottom-full mb-2 ${isRTL ? 'right-4' : 'left-4'} w-64 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-700 p-2 z-[60] animate-in fade-in slide-in-from-bottom-2 duration-200`}
            >
              {/* Language Section */}
              <div className="p-2">
                <p className="px-2 pb-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                  {t('language')}
                </p>
                <div className="grid grid-cols-2 gap-1 bg-gray-50 dark:bg-gray-900/50 p-1 rounded-xl">
                  <button 
                    onClick={() => setLanguage('en')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-xs font-medium transition-all ${language === 'en' ? 'bg-white dark:bg-gray-700 text-teal-600 dark:text-teal-400 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                  >
                    <Globe className="w-3.5 h-3.5" />
                    English
                  </button>
                  <button 
                    onClick={() => setLanguage('ar')}
                    className={`flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-xs font-medium transition-all ${language === 'ar' ? 'bg-white dark:bg-gray-700 text-teal-600 dark:text-teal-400 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                  >
                    العربية
                    <Globe className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Theme Section */}
              <div className="p-2 border-t border-gray-50 dark:border-gray-700/50">
                <p className="px-2 pb-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                  Theme
                </p>
                <div className="grid grid-cols-3 gap-1 bg-gray-50 dark:bg-gray-900/50 p-1 rounded-xl">
                  <button 
                    onClick={() => setTheme('light')}
                    className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'light' ? 'bg-white dark:bg-gray-700 text-teal-600 dark:text-teal-400 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
                    title="Light"
                  >
                    <Sun className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setTheme('dark')}
                    className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'dark' ? 'bg-white dark:bg-gray-700 text-teal-600 dark:text-teal-400 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
                    title="Dark"
                  >
                    <Moon className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setTheme('system')}
                    className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'system' ? 'bg-white dark:bg-gray-700 text-teal-600 dark:text-teal-400 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
                    title="System"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Logout button */}
              <div className="p-1 border-t border-gray-50 dark:border-gray-700/50 mt-1">
                <button 
                  onClick={handleLogout}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all font-medium group"
                >
                  <div className="flex items-center gap-3 text-sm">
                    <LogOut className="w-4 h-4" />
                    <span>{t('chatLogout')}</span>
                  </div>
                  <ChevronRight className={`w-4 h-4 opacity-0 group-hover:opacity-100 transition-all transform ${isRTL ? 'rotate-180' : ''}`} />
                </button>
              </div>
            </div>
          )}

          <button 
            onClick={() => setSettingsOpen(!settingsOpen)}
            className={`
              w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl transition-all duration-200 group
              ${settingsOpen ? 'bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}
            `}
          >
            <div className="flex items-center gap-3">
              <Settings className={`w-5 h-5 transition-transform duration-500 ${settingsOpen ? 'rotate-90' : ''}`} />
              <span className="text-sm font-semibold">{t('chatSettings')}</span>
            </div>
            <ChevronRight className={`w-4 h-4 transition-transform duration-300 ${settingsOpen ? (isRTL ? '-rotate-90' : 'rotate-90') : (isRTL ? 'rotate-180' : '')}`} />
          </button>
        </div>
      </aside>
    </>
  );
}
