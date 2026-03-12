'use client';

import { useLanguage } from '@/lib/language-context';

export function DocumentsView() {
  const { t } = useLanguage();

  return (
    <div className="flex-1 overflow-y-auto p-8 chat-scrollbar">
      {/* Page Title & Upload */}
      <div className="flex flex-col gap-6 mb-8">
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
              {t('docLibraryTitle') || 'Document Library'}
            </h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              {t('docLibrarySubtitle') || 'Manage and organize your research papers for AI analysis.'}
            </p>
          </div>
          <div className="flex gap-3">
            <button className="flex items-center gap-2 px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-semibold bg-white dark:bg-slate-800 hover:bg-slate-50 transition-colors">
              <span className="material-symbols-outlined text-lg text-slate-500">filter_list</span>
              {t('docFilter') || 'Filter'}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-bold shadow-sm hover:opacity-90 transition-opacity">
              <span className="material-symbols-outlined text-lg">upload_file</span>
              {t('docAddPaper') || 'Add New Paper'}
            </button>
          </div>
        </div>
        {/* Upload Zone */}
        <div className="border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl bg-white/50 dark:bg-slate-900/50 p-10 flex flex-col items-center justify-center text-center transition-colors hover:border-primary group">
          <div className="px-4 py-2 bg-primary/20 text-primary rounded-lg text-xs font-bold hover:bg-primary/30 transition-all">
            <span className="material-symbols-outlined text-3xl">cloud_upload</span>
          </div>
          <h3 className="text-slate-900 dark:text-slate-100 font-bold text-lg mt-4">
            {t('docDragDrop') || 'Drag and Drop Upload'}
          </h3>
          <p className="text-slate-500 dark:text-slate-400 text-sm max-w-sm mt-1">
            {t('docSupportedFormats') || 'Supported formats: PDF, BIB, RIS. Your papers will be automatically parsed and indexed for chat.'}
          </p>
          <div className="mt-4 flex gap-2">
            <button className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 shadow-sm transition-all">
              {t('docBrowseFiles') || 'Browse Files'}
            </button>
            <button className="px-4 py-2 bg-primary/20 text-primary rounded-lg text-xs font-bold hover:bg-primary/30 transition-all">
              {t('docImportZotero') || 'Import from Zotero'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Data Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-start border-collapse">
            <thead>
              <tr className="dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 bg-stone-50">
                <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('docColTitle') || 'Title'}</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('docColAuthors') || 'Authors'}</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('docColJournal') || 'Journal'}</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-center">{t('docColYear') || 'Year'}</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{t('docColStatus') || 'Status'}</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-end">{t('docColActions') || 'Actions'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {/* Row 1 */}
              <tr className="table-row-hover transition-colors group hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary text-2xl">picture_as_pdf</span>
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-slate-100">Attention Is All You Need</p>
                      <p className="text-xs text-slate-500">1.2 MB • Added Oct 12</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400">Vaswani, A. et al.</p>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400 italic">NeurIPS</p>
                </td>
                <td className="px-6 py-4 text-center">
                  <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">2017</p>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400"></span> 
                    {t('docStatusReady') || 'Ready'}
                  </span>
                </td>
                <td className="px-6 py-4 text-end">
                  <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Open Document">
                      <span className="material-symbols-outlined text-xl">open_in_new</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Reprocess AI Index">
                      <span className="material-symbols-outlined text-xl">refresh</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-red-500 transition-colors rounded-lg" title="Delete">
                      <span className="material-symbols-outlined text-xl">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
              {/* Row 2 */}
              <tr className="table-row-hover transition-colors group hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary text-2xl">picture_as_pdf</span>
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-slate-100">Language Models are Few-Shot Learners</p>
                      <p className="text-xs text-slate-500">2.8 MB • Added Oct 11</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400">Brown, T. B. et al.</p>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400 italic">arXiv</p>
                </td>
                <td className="px-6 py-4 text-center">
                  <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">2020</p>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-50 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-blue-400 animate-pulse"></span>
                    {t('docStatusProcessing') || 'Processing'}
                  </span>
                </td>
                <td className="px-6 py-4 text-end">
                  <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Open Document">
                      <span className="material-symbols-outlined text-xl">open_in_new</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Reprocess AI Index">
                      <span className="material-symbols-outlined text-xl">refresh</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-red-500 transition-colors rounded-lg" title="Delete">
                      <span className="material-symbols-outlined text-xl">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
              {/* Row 3 */}
              <tr className="table-row-hover transition-colors group hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary text-2xl">picture_as_pdf</span>
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-slate-100">LoRA: Low-Rank Adaptation</p>
                      <p className="text-xs text-slate-500">850 KB • Added Oct 10</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400">Hu, E. J. et al.</p>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400 italic">ICLR</p>
                </td>
                <td className="px-6 py-4 text-center">
                  <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">2021</p>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                    {t('docStatusUploading') || 'Uploading'}
                  </span>
                </td>
                <td className="px-6 py-4 text-end">
                  <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Open Document">
                      <span className="material-symbols-outlined text-xl">open_in_new</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Reprocess AI Index">
                      <span className="material-symbols-outlined text-xl">refresh</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-red-500 transition-colors rounded-lg" title="Delete">
                      <span className="material-symbols-outlined text-xl">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
              {/* Row 4 */}
              <tr className="table-row-hover transition-colors group hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary text-2xl">picture_as_pdf</span>
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-slate-100">Deep Residual Learning for Image Recognition</p>
                      <p className="text-xs text-slate-500">4.5 MB • Added Oct 08</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400">He, K. et al.</p>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400 italic">CVPR</p>
                </td>
                <td className="px-6 py-4 text-center">
                  <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">2016</p>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                     <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400"></span> 
                     {t('docStatusReady') || 'Ready'}
                  </span>
                </td>
                <td className="px-6 py-4 text-end">
                  <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Open Document">
                      <span className="material-symbols-outlined text-xl">open_in_new</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Reprocess AI Index">
                      <span className="material-symbols-outlined text-xl">refresh</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-red-500 transition-colors rounded-lg" title="Delete">
                      <span className="material-symbols-outlined text-xl">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
              {/* Row 5 */}
              <tr className="table-row-hover transition-colors group hover:bg-slate-50 dark:hover:bg-slate-800/50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary text-2xl">picture_as_pdf</span>
                    <div>
                      <p className="text-sm font-bold text-slate-900 dark:text-slate-100">The Power of Scale for Parameter-Efficient Prompt Tuning</p>
                      <p className="text-xs text-slate-500">1.8 MB • Added Oct 05</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400">Lester, B. et al.</p>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-600 dark:text-slate-400 italic">EMNLP</p>
                </td>
                <td className="px-6 py-4 text-center">
                  <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">2021</p>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                     <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400"></span> 
                     {t('docStatusReady') || 'Ready'}
                  </span>
                </td>
                <td className="px-6 py-4 text-end">
                  <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Open Document">
                      <span className="material-symbols-outlined text-xl">open_in_new</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-primary transition-colors rounded-lg" title="Reprocess AI Index">
                      <span className="material-symbols-outlined text-xl">refresh</span>
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-red-500 transition-colors rounded-lg" title="Delete">
                      <span className="material-symbols-outlined text-xl">delete</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <p className="text-xs text-slate-500 font-medium">{t('docPaginationText') || 'Showing 1 to 5 of 48 documents'}</p>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold bg-white dark:bg-slate-800 text-slate-600 hover:bg-slate-50 disabled:opacity-50" disabled>
              {t('docPaginationPrev') || 'Previous'}
            </button>
            <button className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold bg-white dark:bg-slate-800 text-slate-600 hover:bg-slate-50">
              {t('docPaginationNext') || 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
