'use client';

import { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '@/store/store';
import { updateDocumentMetadata } from '@/store/documents/document-actions';
import { DocumentListItem } from '@/lib/api/documents';
import { useLanguage } from '@/lib/language-context';

interface DocumentMetadataEditProps {
  document: DocumentListItem;
  onClose: () => void;
}

export function DocumentMetadataEdit({ document: doc, onClose }: DocumentMetadataEditProps) {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState(doc.title || '');
  const [author, setAuthor] = useState(doc.author || '');
  const [year, setYear] = useState(doc.year || '');
  const [journal, setJournal] = useState('');
  const [doi, setDoi] = useState('');

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    const data: Record<string, string> = {};
    if (title.trim()) data.title = title.trim();
    if (author.trim()) data.author = author.trim();
    if (year.trim()) data.year = year.trim();
    if (journal.trim()) data.journal = journal.trim();
    if (doi.trim()) data.doi = doi.trim();

    try {
      await dispatch(updateDocumentMetadata({ id: doc.id, data })).unwrap();
      onClose();
    } catch (err: any) {
      setError(typeof err === 'string' ? err : 'Failed to update metadata');
    } finally {
      setSaving(false);
    }
  };

  const inputClass =
    'w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:border-primary/40 outline-none transition-all';

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-in fade-in duration-150"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-md animate-in fade-in zoom-in-95 duration-200"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {t('docEditMetadata') || 'Edit Metadata'}
            </h3>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors rounded-lg"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          {/* Body */}
          <div className="px-6 py-4 space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                {t('docMetaTitle') || 'Title'}
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Document title..."
                className={inputClass}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                {t('docMetaAuthor') || 'Author(s)'}
              </label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="Author names..."
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                  {t('docMetaYear') || 'Year'}
                </label>
                <input
                  type="text"
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  placeholder="2024"
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                  {t('docMetaJournal') || 'Journal'}
                </label>
                <input
                  type="text"
                  value={journal}
                  onChange={(e) => setJournal(e.target.value)}
                  placeholder="Journal name..."
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                DOI
              </label>
              <input
                type="text"
                value={doi}
                onChange={(e) => setDoi(e.target.value)}
                placeholder="10.xxxx/xxxxx"
                className={inputClass}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-500 text-sm font-medium">
                <span className="material-symbols-outlined text-lg">error</span>
                {error}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-800">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              {t('cancel') || 'Cancel'}
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {saving && (
                <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
              )}
              {t('save') || 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
