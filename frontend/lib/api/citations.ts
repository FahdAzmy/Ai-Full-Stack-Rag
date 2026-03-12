import type { SourceChunk } from './chats';

/**
 * Client-side citation formatting utilities.
 *
 * The backend does not yet have citation endpoints (/citations/...).
 * These helpers format citations from the source_chunks data returned
 * by the chat query endpoint.
 */

export type CitationFormat = 'apa' | 'mla' | 'bibtex';

export interface FormattedCitation {
  format: CitationFormat;
  text: string;
}

/** Format a source chunk as an APA citation */
export function formatAPA(source: SourceChunk): string {
  const author = source.author || 'Unknown Author';
  const year = source.year || 'n.d.';
  const title = source.title || source.file_name || 'Untitled';

  return `${author} (${year}). ${title}.`;
}

/** Format a source chunk as an MLA citation */
export function formatMLA(source: SourceChunk): string {
  const author = source.author || 'Unknown Author';
  const title = source.title || source.file_name || 'Untitled';
  const year = source.year || 'n.d.';

  return `${author}. "${title}." ${year}.`;
}

/** Format a source chunk as a BibTeX entry */
export function formatBibTeX(source: SourceChunk): string {
  const key = (source.author?.split(/[,\s]+/)[0] || 'unknown').toLowerCase() + (source.year || '');
  const title = source.title || source.file_name || 'Untitled';
  const author = source.author || 'Unknown Author';
  const year = source.year || '';

  return [
    `@article{${key},`,
    `  title  = {${title}},`,
    `  author = {${author}},`,
    `  year   = {${year}}`,
    `}`,
  ].join('\n');
}

/** Get citation in all formats for a source */
export function getAllFormats(source: SourceChunk): FormattedCitation[] {
  return [
    { format: 'apa', text: formatAPA(source) },
    { format: 'mla', text: formatMLA(source) },
    { format: 'bibtex', text: formatBibTeX(source) },
  ];
}

/** Copy text to clipboard, returns true on success */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
