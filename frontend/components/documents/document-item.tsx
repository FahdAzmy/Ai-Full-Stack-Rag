'use client';

import { useDispatch } from 'react-redux';
import { AppDispatch } from '@/store/store';
import { deleteDocument } from '@/store/documents/document-actions';
import { toggleDocumentSelection } from '@/store/documents/document-slice';
import { DocumentListItem } from '@/lib/api/documents';
import { useLanguage } from '@/lib/language-context';
import { useState } from 'react';

interface DocumentItemProps {
  document: DocumentListItem;
  isSelected: boolean;
  selectable?: boolean; // true in sidebar mode (for chat filtering)
  onEditMetadata?: (doc: DocumentListItem) => void;
}

export function DocumentItem({
  document: doc,
  isSelected,
  selectable = false,
  onEditMetadata,
}: DocumentItemProps) {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleDelete = () => {
    if (confirmDelete) {
      dispatch(deleteDocument(doc.id));
      setConfirmDelete(false);
    } else {
      setConfirmDelete(true);
      // Auto-reset confirm after 3 seconds
      setTimeout(() => setConfirmDelete(false), 3000);
    }
  };

  const handleSelect = () => {
    if (selectable && doc.status === 'ready') {
      dispatch(toggleDocumentSelection(doc.id));
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

  const status = statusConfig[doc.status] || statusConfig.uploading;

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

  return (
    <div
      className={`
        group flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-150
        ${selectable && doc.status === 'ready' ? 'cursor-pointer' : ''}
        ${isSelected
          ? 'bg-primary/5 border border-primary/20 dark:bg-primary/10 dark:border-primary/30'
          : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-transparent'
        }
      `}
      onClick={handleSelect}
    >
      {/* Selection checkbox (in sidebar mode) */}
      {selectable && (
        <div className={`
          w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors
          ${isSelected
            ? 'bg-primary border-primary text-white'
            : 'border-slate-300 dark:border-slate-600'
          }
          ${doc.status !== 'ready' ? 'opacity-30' : ''}
        `}>
          {isSelected && (
            <span className="material-symbols-outlined text-xs">check</span>
          )}
        </div>
      )}

      {/* PDF Icon */}
      <span className="material-symbols-outlined text-primary text-xl shrink-0">
        picture_as_pdf
      </span>

      {/* Document info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
          {doc.title || doc.file_name}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {[
            formatFileSize(doc.file_size),
            doc.total_pages ? `${doc.total_pages} pages` : null,
            formatDate(doc.created_at),
          ]
            .filter(Boolean)
            .join(' • ')}
        </p>
      </div>

      {/* Status badge */}
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold shrink-0 ${status.badgeClass}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${status.dotClass}`} />
        {status.label}
      </span>

      {/* Actions */}
      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
        onClick={(e) => e.stopPropagation()}
      >
        {onEditMetadata && (
          <button
            className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg"
            title={t('docEditMetadata') || 'Edit Metadata'}
            onClick={() => onEditMetadata(doc)}
          >
            <span className="material-symbols-outlined text-lg">edit</span>
          </button>
        )}
        <button
          className={`p-1.5 transition-colors rounded-lg ${
            confirmDelete
              ? 'text-red-500 bg-red-50 dark:bg-red-900/20'
              : 'text-slate-400 hover:text-red-500'
          }`}
          title={confirmDelete ? (t('docConfirmDelete') || 'Click again to confirm') : (t('docDelete') || 'Delete')}
          onClick={handleDelete}
        >
          <span className="material-symbols-outlined text-lg">
            {confirmDelete ? 'delete_forever' : 'delete'}
          </span>
        </button>
      </div>
    </div>
  );
}
