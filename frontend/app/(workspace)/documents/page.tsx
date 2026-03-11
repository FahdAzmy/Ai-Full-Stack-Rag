'use client';

import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '@/store/store';
import { fetchDocuments } from '@/store/documents/document-actions';
import { DocumentsView } from '@/components/documents/documents-view';

export default function DocumentsPage() {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    dispatch(fetchDocuments(undefined));
  }, [dispatch]);

  return <DocumentsView />;
}
