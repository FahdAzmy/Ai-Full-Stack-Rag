'use client';

import { useCallback, useState, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { uploadDocument } from '@/store/documents/document-actions';
import { fetchDocuments } from '@/store/documents/document-actions';
import { setUploadProgress } from '@/store/documents/document-slice';
import { useLanguage } from '@/lib/language-context';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export function DocumentUpload() {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { uploading, uploadProgress, error } = useSelector(
    (state: RootState) => state.documents
  );
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setLocalError(null);
      setSuccess(false);

      // Validate file type
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        setLocalError(t('docErrFileType') || 'Only PDF files are accepted');
        return;
      }

      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        setLocalError(t('docErrFileSize') || 'File size exceeds 50MB limit');
        return;
      }

      try {
        await dispatch(
          uploadDocument({
            file,
            onProgress: (percent) => {
              dispatch(setUploadProgress(percent));
            },
          })
        ).unwrap();

        setSuccess(true);
        // Refresh the document list
        dispatch(fetchDocuments(undefined));

        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(false), 3000);
      } catch {
        // Error is already set in the Redux state
      }
    },
    [dispatch]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
    // Reset input so same file can be re-selected
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const displayError = localError || error;

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`
        border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center 
        transition-all duration-200 cursor-pointer group
        ${dragActive
          ? 'border-primary bg-primary/5 dark:bg-primary/10 scale-[1.01]'
          : 'border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 hover:border-primary/50'
        }
      `}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileInput}
        className="hidden"
      />

      {/* Icon */}
      <div className={`
        p-3 rounded-lg transition-colors
        ${dragActive ? 'bg-primary/20 text-primary' : 'bg-primary/10 text-primary/70 group-hover:bg-primary/20 group-hover:text-primary'}
      `}>
        <span className="material-symbols-outlined text-3xl">cloud_upload</span>
      </div>

      {/* Title */}
      <h3 className="text-slate-900 dark:text-slate-100 font-bold text-lg mt-4">
        {dragActive
          ? (t('docDropHere') || 'Drop your PDF here')
          : (t('docDragDrop') || 'Drag and Drop Upload')}
      </h3>
      <p className="text-slate-500 dark:text-slate-400 text-sm max-w-sm mt-1">
        {t('docSupportedFormats') || 'Supported format: PDF (max 50MB). Your papers will be automatically parsed and indexed for chat.'}
      </p>

      {/* Browse button */}
      {!uploading && (
        <button
          className="mt-4 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 shadow-sm transition-all"
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
        >
          {t('docBrowseFiles') || 'Browse Files'}
        </button>
      )}

      {/* Upload progress bar */}
      {uploading && (
        <div className="mt-4 w-full max-w-xs">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>{t('docUploading') || 'Uploading...'}</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Success message */}
      {success && (
        <div className="mt-3 flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-sm font-medium animate-in fade-in duration-200">
          <span className="material-symbols-outlined text-lg">check_circle</span>
          {t('docUploadSuccess') || 'File uploaded successfully!'}
        </div>
      )}

      {/* Error message */}
      {displayError && (
        <div className="mt-3 flex items-center gap-2 text-red-500 text-sm font-medium animate-in fade-in duration-200">
          <span className="material-symbols-outlined text-lg">error</span>
          {displayError}
        </div>
      )}
    </div>
  );
}
