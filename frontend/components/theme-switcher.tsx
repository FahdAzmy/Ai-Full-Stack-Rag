'use client';

import { useTheme } from '@/lib/theme-context';
import { Button } from '@/components/ui/button';
import { Moon, Sun } from 'lucide-react';

export function ThemeSwitcher() {
  const { theme, setTheme, isDark } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => {
        if (theme === 'dark') {
          setTheme('light');
        } else if (theme === 'light') {
          setTheme('system');
        } else {
          setTheme('dark');
        }
      }}
      className="relative w-10 h-10 rounded-lg transition-colors hover:bg-primary/10"
      title={`Theme: ${theme}`}
    >
      <div className="relative w-5 h-5">
        {isDark ? (
          <Moon className="w-5 h-5 absolute inset-0" />
        ) : (
          <Sun className="w-5 h-5 absolute inset-0" />
        )}
      </div>
      <span className="sr-only">Toggle theme (current: {theme})</span>
    </Button>
  );
}
