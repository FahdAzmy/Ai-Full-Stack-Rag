'use client';

import { useState } from 'react';
import type { SourceChunk } from '@/lib/api/chats';
import { CitationBlock } from './citation-block';
import { useLanguage } from '@/lib/language-context';

interface SourcesPanelProps {
  sources: SourceChunk[];
}

export function SourcesPanel({ sources }: SourcesPanelProps) {
  const { t } = useLanguage();
  const [expandedSource, setExpandedSource] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30 overflow-hidden animate-in slide-in-from-top-2 fade-in duration-200">
      {/* Header */}
      <div className="px-4 py-2.5 bg-slate-100/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700">
        <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {t('sourcesPanelTitle') || 'Sources'} ({sources.length})
        </p>
      </div>

      {/* Source list */}
      <div className="divide-y divide-slate-200 dark:divide-slate-700/50">
        {sources.map((source) => {
          const isExpanded = expandedSource === source.source_number;

          return (
            <div key={source.source_number} className="group">
              {/* Source header (clickable) */}
              <button
                onClick={() =>
                  setExpandedSource(isExpanded ? null : source.source_number)
                }
                className="w-full px-4 py-3 flex items-start gap-3 text-start hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors"
              >
                {/* Source number badge */}
                <span className="shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold flex items-center justify-center mt-0.5">
                  {source.source_number}
                </span>

                {/* Source info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                    {source.title || source.file_name || 'Untitled Source'}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                    {source.author && (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {source.author}
                      </span>
                    )}
                    {source.year && (
                      <span className="text-xs text-slate-400 dark:text-slate-500">
                        ({source.year})
                      </span>
                    )}
                    {source.page_number != null && (
                      <span className="text-xs text-slate-400 dark:text-slate-500">
                        p. {source.page_number}
                      </span>
                    )}
                  </div>
                </div>

                {/* Relevance score */}
                {source.similarity != null && (
                  <div className="shrink-0 flex items-center gap-1.5">
                    <div className="w-12 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${Math.round(source.similarity * 100)}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 w-8">
                      {Math.round(source.similarity * 100)}%
                    </span>
                  </div>
                )}

                {/* Expand icon */}
                <span
                  className={`material-symbols-outlined text-lg text-slate-400 shrink-0 transition-transform ${
                    isExpanded ? 'rotate-180' : ''
                  }`}
                >
                  expand_more
                </span>
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-4 pb-4 pl-[52px] animate-in slide-in-from-top-1 fade-in duration-150">
                  {/* Excerpt */}
                  {source.excerpt && (
                    <div className="mb-3">
                      <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                        {t('sourcesExcerpt') || 'Excerpt'}
                      </p>
                      <blockquote className="text-sm text-slate-600 dark:text-slate-300 italic border-l-2 border-primary/30 pl-3 py-1">
                        &ldquo;{source.excerpt}&rdquo;
                      </blockquote>
                    </div>
                  )}

                  {/* Citation block */}
                  <div>
                    <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                      {t('sourcesCitation') || 'Citation'}
                    </p>
                    <CitationBlock source={source} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
