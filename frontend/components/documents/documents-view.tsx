'use client';

import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { fetchDocuments } from '@/store/documents/document-actions';
import { deleteDocument } from '@/store/documents/document-actions';
import { DocumentUpload } from './document-upload';
import { DocumentMetadataEdit } from './document-metadata-edit';
import { setSidebarOpen } from '@/store/chat/chat-slice';
import { DocumentListItem } from '@/lib/api/documents';
import { useLanguage } from '@/lib/language-context';

export function DocumentsView() {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { documents, loading, total } = useSelector(
    (state: RootState) => state.documents
  );
  const { sidebarOpen } = useSelector((state: RootState) => state.chat);
  
  const [editingDoc, setEditingDoc] = useState<DocumentListItem | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch documents on mount and when filter changes
  useEffect(() => {
    dispatch(fetchDocuments(statusFilter));
  }, [dispatch, statusFilter]);

  // Poll every 5 seconds while any document is 'processing'
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === 'processing');

    if (hasProcessing && !pollingRef.current) {
      pollingRef.current = setInterval(() => {
        dispatch(fetchDocuments(statusFilter));
      }, 5000);
    }

    if (!hasProcessing && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [documents, dispatch, statusFilter]);

  const handleDelete = (id: string) => {
    if (confirmDeleteId === id) {
      dispatch(deleteDocument(id));
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(id);
      setTimeout(() => setConfirmDeleteId(null), 3000);
    }
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return '';
    }
  };

  const statusConfig: Record<string, { label: string; dotClass: string; badgeClass: string }> = {
    ready: {
      label: t('docStatusReady') || 'Ready',
      dotClass: 'bg-emerald-600 dark:bg-emerald-400',
      badgeClass: 'bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
    },
    processing: {
      label: t('docStatusProcessing') || 'Processing',
      dotClass: 'bg-blue-600 dark:bg-blue-400 animate-pulse',
      badgeClass: 'bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    },
    uploading: {
      label: t('docStatusUploading') || 'Uploading',
      dotClass: 'bg-slate-500',
      badgeClass: 'bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-400',
    },
    failed: {
      label: t('docStatusFailed') || 'Failed',
      dotClass: 'bg-red-600 dark:bg-red-400',
      badgeClass: 'bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    },
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-8 chat-scrollbar">
      {/* Page Title & Actions */}
      <div className="flex flex-col gap-6 mb-8">
        <div className="flex flex-col md:flex-row justify-between md:items-end gap-4">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => dispatch(setSidebarOpen(!sidebarOpen))}
              className="p-1 -ml-2 text-slate-500 hover:text-primary dark:text-slate-400 dark:hover:text-emerald-400 transition-colors rounded-md"
            >
              <span className="material-symbols-outlined text-[28px]">{sidebarOpen ? 'menu_open' : 'menu'}</span>
            </button>
            <div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                {t('docLibraryTitle') || 'Document Library'}
              </h2>
              <p className="text-sm md:text-base text-slate-500 dark:text-slate-400 mt-1">
                {t('docLibrarySubtitle') || 'Manage and organize your research papers for AI analysis.'}
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            {/* Status filter */}
            <select
              value={statusFilter || ''}
              onChange={(e) => setStatusFilter(e.target.value || undefined)}
              className="px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-semibold bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">{t('docFilterAll') || 'All Status'}</option>
              <option value="ready">{t('docStatusReady') || 'Ready'}</option>
              <option value="processing">{t('docStatusProcessing') || 'Processing'}</option>
              <option value="failed">{t('docStatusFailed') || 'Failed'}</option>
            </select>
          </div>
        </div>

        {/* Upload zone */}
        <DocumentUpload />
      </div>

      {/* Loading skeleton */}
      {loading && documents.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="animate-pulse flex items-center gap-4 px-6 py-4">
                <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
                  <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/4" />
                </div>
                <div className="h-6 w-20 bg-slate-200 dark:bg-slate-700 rounded-full" />
              </div>
            ))}
          </div>
        </div>
      ) : documents.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="material-symbols-outlined text-6xl text-slate-300 dark:text-slate-600">
            description
          </span>
          <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-4">
            {t('docEmptyTitle') || 'No documents yet'}
          </h3>
          <p className="text-slate-500 dark:text-slate-400 mt-2 max-w-sm">
            {t('docEmptySubtitle') || 'Upload your first research paper above to get started with AI-powered analysis.'}
          </p>
        </div>
      ) : (
        /* Data Table */
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-start border-collapse">
              <thead>
                <tr className="dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 bg-stone-50">
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    {t('docColTitle') || 'Title'}
                  </th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    {t('docColAuthors') || 'Authors'}
                  </th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-center">
                    {t('docColYear') || 'Year'}
                  </th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    {t('docColStatus') || 'Status'}
                  </th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-end">
                    {t('docColActions') || 'Actions'}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {documents.map((doc) => {
                  const status = statusConfig[doc.status] || statusConfig.uploading;
                  return (
                    <tr
                      key={doc.id}
                      className="transition-colors group hover:bg-slate-50 dark:hover:bg-slate-800/50"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <span className="material-symbols-outlined text-primary text-2xl">
                            picture_as_pdf
                          </span>
                          <div>
                            <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
                              {doc.title || doc.file_name}
                            </p>
                            <p className="text-xs text-slate-500">
                              {formatFileSize(doc.file_size)}
                              {doc.total_pages ? ` • ${doc.total_pages} pages` : ''}
                              {` • Added ${formatDate(doc.created_at)}`}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          {doc.author || '—'}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                          {doc.year || '—'}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${status.badgeClass}`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${status.dotClass}`} />
                          {status.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-end">
                        <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg"
                            title={t('docEditMetadata') || 'Edit Metadata'}
                            onClick={() => setEditingDoc(doc)}
                          >
                            <span className="material-symbols-outlined text-xl">edit</span>
                          </button>
                          <button
                            className={`p-1.5 transition-colors rounded-lg ${
                              confirmDeleteId === doc.id
                                ? 'text-red-500 bg-red-50 dark:bg-red-900/20'
                                : 'text-slate-400 hover:text-red-500'
                            }`}
                            title={
                              confirmDeleteId === doc.id
                                ? (t('docConfirmDelete') || 'Click again to confirm')
                                : (t('docDelete') || 'Delete')
                            }
                            onClick={() => handleDelete(doc.id)}
                          >
                            <span className="material-symbols-outlined text-xl">
                              {confirmDeleteId === doc.id ? 'delete_forever' : 'delete'}
                            </span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {/* Footer */}
          <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <p className="text-xs text-slate-500 font-medium">
              {documents.length} of {total} {t('docDocuments') || 'documents'}
            </p>
          </div>
        </div>
      )}

      {/* Metadata edit modal */}
      {editingDoc && (
        <DocumentMetadataEdit
          document={editingDoc}
          onClose={() => setEditingDoc(null)}
        />
      )}
    </div>
  );
}
