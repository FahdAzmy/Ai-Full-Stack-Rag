export interface ValidationErrors {
  [key: string]: string;
}

export function validateEmail(email: string): string | null {
  if (!email || email.trim() === '') return 'emailRequired';
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) return 'invalidEmail';
  
  if (email.length > 254) return 'emailTooLong';
  
  return null;
}

export function validatePassword(password: string): string | null {
  if (!password) return 'passwordRequired';
  if (password.length < 8) return 'passwordTooShort';
  if (password.length > 128) return 'passwordTooLong';
  
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
  
  const strengthScore = [hasUpperCase, hasLowerCase, hasNumber, hasSpecialChar].filter(Boolean).length;
  
  if (strengthScore < 2) return 'passwordWeak';
  
  return null;
}

export function validateLoginPassword(password: string): string | null {
  if (!password) return 'passwordRequired';
  return null;
}

export function validateFullName(name: string): string | null {
  if (!name || name.trim() === '') return 'nameRequired';
  
  const trimmedName = name.trim();
  if (trimmedName.length < 2) return 'nameTooShort';
  if (trimmedName.length > 100) return 'nameTooLong';
  
  if (!/^[a-zA-Z\s\-']+$/.test(trimmedName)) return 'nameInvalid';
  
  return null;
}

export function validatePasswordMatch(password: string, confirmPassword: string): string | null {
  if (password !== confirmPassword) return 'passwordMismatch';
  return null;
}

export function validateVerificationCode(code: string): string | null {
  if (!code || code.trim() === '') return 'codeRequired';
  if (code.length !== 6 || !/^\d+$/.test(code)) return 'codeInvalid';
  return null;
}

export function getPasswordStrength(password: string): 'weak' | 'fair' | 'good' | 'strong' {
  if (!password) return 'weak';
  
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
  const isLongEnough = password.length >= 12;
  
  const score = [hasUpperCase, hasLowerCase, hasNumber, hasSpecialChar, isLongEnough].filter(Boolean).length;
  
  if (score <= 2) return 'weak';
  if (score === 3) return 'fair';
  if (score === 4) return 'good';
  return 'strong';
}
