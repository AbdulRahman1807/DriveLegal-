'use client';

import { useCallback, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { BookOpen, ExternalLink, X, ChevronDown, ChevronUp } from 'lucide-react';
import { ApiService, type Citation, type LegalSectionDetail } from '@/services/api';
import styles from './CitationChip.module.css';

type CitationChipProps = {
  citation: Citation;
};

function briefFromDetail(detail: LegalSectionDetail) {
  if (detail.explanation_text?.trim()) return detail.explanation_text.trim();
  const clean = detail.full_text.replace(/\s+/g, ' ').trim();
  if (clean.length <= 320) return clean;
  return `${clean.slice(0, 320).trim()}…`;
}

function citationHasInlineDetail(citation: Citation) {
  return Boolean(citation.brief || citation.full_text);
}

function inlineToDetail(citation: Citation): LegalSectionDetail {
  return {
    id: citation.id ?? '',
    act_name: citation.act_name,
    section_number: citation.section,
    chapter: citation.chapter,
    clause: citation.clause,
    explanation_text: citation.brief,
    full_text: citation.full_text ?? citation.brief ?? '',
    source_url: citation.source_url,
  };
}

export default function CitationChip({ citation }: CitationChipProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<LegalSectionDetail | null>(
    citationHasInlineDetail(citation) ? inlineToDetail(citation) : null,
  );
  const [showFull, setShowFull] = useState(false);

  const fetchDetail = useCallback(async () => {
    if (citationHasInlineDetail(citation)) {
      setDetail(inlineToDetail(citation));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = citation.id
        ? await ApiService.getLegalSection(citation.id)
        : await ApiService.lookupLegalSection(citation.act_name, citation.section);
      setDetail(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not load this section.');
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [citation]);

  const handleOpen = () => {
    setOpen(true);
    setShowFull(false);
    if (!detail && !loading) {
      void fetchDetail();
    }
  };

  const handleClose = () => {
    setOpen(false);
    setShowFull(false);
  };

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  const label = `${citation.act_name} — Section ${citation.section}`;
  const displayDetail = detail ?? (citationHasInlineDetail(citation) ? inlineToDetail(citation) : null);
  const brief = displayDetail
    ? displayDetail.explanation_text || briefFromDetail(displayDetail)
    : citation.brief;

  return (
    <>
      <button type="button" className={styles.chip} onClick={handleOpen} title={`View brief: ${label}`}>
        <BookOpen size={12} />
        <span>
          {citation.act_name} · Sec. {citation.section}
        </span>
      </button>

      {open &&
        createPortal(
          <div className={styles.overlay} onClick={handleClose} role="presentation">
            <div
              className={styles.modal}
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="citation-modal-title"
            >
              <div className={styles.modalHeader}>
                <div>
                  <p className={styles.modalKicker}>From this answer</p>
                  <h3 id="citation-modal-title" className={styles.modalTitle}>
                    Section {citation.section}
                  </h3>
                  <p className={styles.modalAct}>{citation.act_name}</p>
                </div>
                <button type="button" className={styles.closeBtn} onClick={handleClose} aria-label="Close">
                  <X size={18} />
                </button>
              </div>

              <div className={styles.modalBody}>
                {loading && <p className={styles.loading}>Loading section details…</p>}

                {error && !loading && (
                  <div className={styles.errorBox}>
                    <p>{error}</p>
                    <button type="button" className={styles.retryBtn} onClick={() => void fetchDetail()}>
                      Try again
                    </button>
                  </div>
                )}

                {displayDetail && !loading && !error && (
                  <>
                    {(displayDetail.chapter || displayDetail.clause || citation.clause) && (
                      <div className={styles.metaRow}>
                        {displayDetail.chapter && <span>Chapter {displayDetail.chapter}</span>}
                        {(displayDetail.clause || citation.clause) && (
                          <span>Clause {displayDetail.clause || citation.clause}</span>
                        )}
                        {citation.relevance_score != null && (
                          <span>Relevance {Math.round(citation.relevance_score * 100)}%</span>
                        )}
                      </div>
                    )}

                    <div className={styles.briefBox}>
                      <p className={styles.briefLabel}>Brief</p>
                      <p className={styles.briefText}>
                        {showFull ? displayDetail.full_text : brief}
                      </p>
                      {displayDetail.full_text.length > 320 && (
                        <button
                          type="button"
                          className={styles.expandBtn}
                          onClick={() => setShowFull((v) => !v)}
                        >
                          {showFull ? (
                            <>
                              Show brief <ChevronUp size={14} />
                            </>
                          ) : (
                            <>
                              Read full statute <ChevronDown size={14} />
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {(displayDetail.source_url || citation.source_url) && (
                      <a
                        href={displayDetail.source_url || citation.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.sourceLink}
                      >
                        <ExternalLink size={14} />
                        View official source
                      </a>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>,
          document.body,
        )}
    </>
  );
}
