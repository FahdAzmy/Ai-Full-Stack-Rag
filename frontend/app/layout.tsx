import React from "react"
import type { Metadata } from 'next'
import { Inter, Outfit } from 'next/font/google'
import './globals.css'
import { LanguageProvider } from '@/lib/language-context'
import { ThemeProvider } from '@/lib/theme-context'
import { Providers } from '@/components/providers'
import { MainLayout } from '@/components/main-layout'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'ScholarGPT - Modern AI Research Assistant',
  description: 'Modern AI Research Assistant',
  colorScheme: 'light dark',
  icons: {
    icon: [
      { url: '/icon-light-32x32.png', media: '(prefers-color-scheme: light)' },
      { url: '/icon-dark-32x32.png', media: '(prefers-color-scheme: dark)' },
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/apple-icon.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className={`${inter.variable} ${outfit.variable} font-sans antialiased`} suppressHydrationWarning>
        <Providers>
          <ThemeProvider>
            <LanguageProvider>
              <MainLayout>
                {children}
              </MainLayout>
            </LanguageProvider>
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  )
}
