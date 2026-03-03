import React from 'react';
import { AuthGuard } from '@/components/auth/auth-guard';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthGuard>{children}</AuthGuard>;
}
