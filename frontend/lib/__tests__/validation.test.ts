import { describe, it, expect } from 'vitest';
import {
  validateEmail,
  validatePassword,
  validateLoginPassword,
  validateFullName,
  validatePasswordMatch,
  validateVerificationCode,
  getPasswordStrength,
} from '@/lib/validation';

// ── validateEmail ───────────────────────────────────────────────────────────

describe('validateEmail', () => {
  it('returns error for empty string', () => {
    expect(validateEmail('')).toBe('emailRequired');
  });

  it('returns error for whitespace-only', () => {
    expect(validateEmail('   ')).toBe('emailRequired');
  });

  it('returns error for invalid email format', () => {
    expect(validateEmail('notanemail')).toBe('invalidEmail');
    expect(validateEmail('missing@')).toBe('invalidEmail');
    expect(validateEmail('@domain.com')).toBe('invalidEmail');
    expect(validateEmail('user@.com')).toBe('invalidEmail');
  });

  it('returns error for email exceeding 254 characters', () => {
    const longEmail = 'a'.repeat(246) + '@test.com'; // 256 chars, exceeds 254
    expect(validateEmail(longEmail)).toBe('emailTooLong');
  });

  it('returns null for valid emails', () => {
    expect(validateEmail('user@example.com')).toBeNull();
    expect(validateEmail('first.last@company.co.uk')).toBeNull();
    expect(validateEmail('user+tag@gmail.com')).toBeNull();
  });
});

// ── validatePassword ────────────────────────────────────────────────────────

describe('validatePassword', () => {
  it('returns error for empty password', () => {
    expect(validatePassword('')).toBe('passwordRequired');
  });

  it('returns error for password shorter than 8 characters', () => {
    expect(validatePassword('Abc1!')).toBe('passwordTooShort');
  });

  it('returns error for password longer than 128 characters', () => {
    expect(validatePassword('Aa1!' + 'x'.repeat(126))).toBe('passwordTooLong');
  });

  it('returns error for weak password (fewer than 2 character classes)', () => {
    expect(validatePassword('abcdefgh')).toBe('passwordWeak'); // only lowercase
    expect(validatePassword('ABCDEFGH')).toBe('passwordWeak'); // only uppercase
    expect(validatePassword('12345678')).toBe('passwordWeak'); // only numbers
  });

  it('returns null for strong passwords', () => {
    expect(validatePassword('Abcdef1!')).toBeNull(); // has upper, lower, number, special
    expect(validatePassword('Password1')).toBeNull(); // has upper, lower, number
    expect(validatePassword('abc123!@')).toBeNull(); // has lower, number, special
  });
});

// ── validateLoginPassword ───────────────────────────────────────────────────

describe('validateLoginPassword', () => {
  it('returns error for empty password', () => {
    expect(validateLoginPassword('')).toBe('passwordRequired');
  });

  it('returns null for any non-empty password', () => {
    expect(validateLoginPassword('a')).toBeNull();
    expect(validateLoginPassword('anything goes here')).toBeNull();
  });
});

// ── validateFullName ────────────────────────────────────────────────────────

describe('validateFullName', () => {
  it('returns error for empty name', () => {
    expect(validateFullName('')).toBe('nameRequired');
  });

  it('returns error for whitespace-only name', () => {
    expect(validateFullName('   ')).toBe('nameRequired');
  });

  it('returns error for name shorter than 2 characters', () => {
    expect(validateFullName('A')).toBe('nameTooShort');
  });

  it('returns error for name longer than 100 characters', () => {
    expect(validateFullName('A'.repeat(101))).toBe('nameTooLong');
  });

  it('returns error for names with numbers or special chars', () => {
    expect(validateFullName('John123')).toBe('nameInvalid');
    expect(validateFullName('User@Name')).toBe('nameInvalid');
  });

  it('returns null for valid ASCII names', () => {
    expect(validateFullName('John Doe')).toBeNull();
    expect(validateFullName("O'Brien")).toBeNull();
    expect(validateFullName('Mary-Jane')).toBeNull();
  });

  it('returns null for Unicode names (Arabic, Chinese, etc.)', () => {
    expect(validateFullName('محمد أحمد')).toBeNull();
    expect(validateFullName('张三')).toBeNull();
    expect(validateFullName('Ólafur Arnalds')).toBeNull();
    expect(validateFullName('Дмитрий')).toBeNull();
  });
});

// ── validatePasswordMatch ───────────────────────────────────────────────────

describe('validatePasswordMatch', () => {
  it('returns error when passwords do not match', () => {
    expect(validatePasswordMatch('abc', 'def')).toBe('passwordMismatch');
  });

  it('returns null when passwords match', () => {
    expect(validatePasswordMatch('password', 'password')).toBeNull();
  });
});

// ── validateVerificationCode ────────────────────────────────────────────────

describe('validateVerificationCode', () => {
  it('returns error for empty code', () => {
    expect(validateVerificationCode('')).toBe('codeRequired');
  });

  it('returns error for non-6-digit code', () => {
    expect(validateVerificationCode('123')).toBe('codeInvalid');
    expect(validateVerificationCode('1234567')).toBe('codeInvalid');
    expect(validateVerificationCode('abcdef')).toBe('codeInvalid');
  });

  it('returns null for valid 6-digit code', () => {
    expect(validateVerificationCode('123456')).toBeNull();
    expect(validateVerificationCode('000000')).toBeNull();
  });
});

// ── getPasswordStrength ─────────────────────────────────────────────────────

describe('getPasswordStrength', () => {
  it('returns "weak" for empty password', () => {
    expect(getPasswordStrength('')).toBe('weak');
  });

  it('returns "weak" for simple passwords', () => {
    expect(getPasswordStrength('abcdefgh')).toBe('weak');
    expect(getPasswordStrength('12345678')).toBe('weak');
  });

  it('returns "fair" for medium passwords', () => {
    expect(getPasswordStrength('Abcdefg1')).toBe('fair'); // upper + lower + number = score 3
  });

  it('returns "good" for good passwords', () => {
    expect(getPasswordStrength('Abcdef1!')).toBe('good'); // upper + lower + number + special, but short
  });

  it('returns "strong" for strong passwords', () => {
    expect(getPasswordStrength('Abcdefgh1!@#')).toBe('strong'); // all criteria + long
  });
});
