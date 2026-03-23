'use client';

import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { fetchDocuments } from '@/store/documents/document-actions';
import { clearSelection } from '@/store/documents/document-slice';
import { DocumentItem } from './document-item';
import { DocumentUpload } from './document-upload';
import { DocumentMetadataEdit } from './document-metadata-edit';
import { DocumentListItem } from '@/lib/api/documents';
import { useLanguage } from '@/lib/language-context';

interface DocumentSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function DocumentSidebar({ isOpen, onToggle }: DocumentSidebarProps) {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { documents, loading, selectedDocumentIds } = useSelector(
    (state: RootState) => state.documents
  );
  const [editingDoc, setEditingDoc] = useState<DocumentListItem | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch documents on mount
  useEffect(() => {
    dispatch(fetchDocuments(undefined));
  }, [dispatch]);

  const hasProcessing = documents.some(
    (d) => d.status === 'processing' || d.status === 'uploading'
  );

  // Poll every 5 seconds while any document is 'processing' or 'uploading'
  useEffect(() => {
    if (hasProcessing && !pollingRef.current) {
      pollingRef.current = setInterval(() => {
        dispatch(fetchDocuments(undefined));
      }, 5000);
    } else if (!hasProcessing && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    // Only clear on complete unmount, not on every re-render
    return () => {
      // Cleanup is mostly for unmounting. 
      // We do NOT clear it here on re-renders while hasProcessing is true
      // because that would reset the timer every time the documents change!
      if (!hasProcessing && pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [hasProcessing, dispatch]);

  // Make sure we clear the interval if the component fully unmounts
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const readyCount = documents.filter((d) => d.status === 'ready').length;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          w-[300px] flex-shrink-0 border-l border-slate-200 dark:border-gray-800 
          bg-white dark:bg-gray-950 flex flex-col 
          transition-all duration-300 ease-in-out z-30 h-full
          ${isOpen
            ? 'translate-x-0'
            : 'translate-x-full lg:translate-x-0 lg:w-0 lg:border-0 lg:overflow-hidden'
          }
          fixed lg:relative inset-y-0 end-0 lg:inset-auto
        `}
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                {t('docPanelTitle') || 'Documents'}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {readyCount} {t('docReady') || 'ready'} / {documents.length} {t('docTotal') || 'total'}
              </p>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="p-1.5 text-primary hover:bg-primary/10 rounded-lg transition-colors"
                title={t('docUpload') || 'Upload PDF'}
              >
                <span className="material-symbols-outlined text-lg">upload_file</span>
              </button>
              {selectedDocumentIds.length > 0 && (
                <button
                  onClick={() => dispatch(clearSelection())}
                  className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg transition-colors"
                  title={t('docClearSelection') || 'Clear selection'}
                >
                  <span className="material-symbols-outlined text-lg">deselect</span>
                </button>
              )}
            </div>
          </div>

          {/* Selection indicator */}
          {selectedDocumentIds.length > 0 && (
            <div className="mt-2 px-2 py-1 bg-primary/10 rounded-lg text-xs font-medium text-primary">
              {selectedDocumentIds.length} {t('docSelected') || 'selected for chat filtering'}
            </div>
          )}
        </div>

        {/* Upload zone (collapsible) */}
        {showUpload && (
          <div className="p-3 border-b border-slate-200 dark:border-slate-800">
            <DocumentUpload />
          </div>
        )}

        {/* Document list */}
        <div className="flex-1 overflow-y-auto chat-scrollbar p-2 space-y-1">
          {loading && documents.length === 0 ? (
            // Skeleton loader
            <div className="space-y-2 p-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse flex items-center gap-3 p-3">
                  <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                    <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : documents.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center h-full text-center p-6">
              <span className="material-symbols-outlined text-4xl text-slate-300 dark:text-slate-600">
                description
              </span>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-3">
                {t('docEmptyTitle') || 'No documents yet'}
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                {t('docEmptySubtitle') || 'Upload your first research paper to get started'}
              </p>
              <button
                onClick={() => setShowUpload(true)}
                className="mt-4 px-4 py-2 bg-primary text-white text-xs font-bold rounded-lg hover:opacity-90 transition-opacity"
              >
                {t('docUploadFirst') || 'Upload PDF'}
              </button>
            </div>
          ) : (
            documents.map((doc) => (
              <DocumentItem
                key={doc.id}
                document={doc}
                isSelected={selectedDocumentIds.includes(doc.id)}
                selectable
                onEditMetadata={setEditingDoc}
              />
            ))
          )}
        </div>
      </aside>

      {/* Metadata edit modal */}
      {editingDoc && (
        <DocumentMetadataEdit
          document={editingDoc}
          onClose={() => setEditingDoc(null)}
        />
      )}
    </>
  );
}
