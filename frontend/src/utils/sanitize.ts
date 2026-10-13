import DOMPurify from 'dompurify';

const CSP_META = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:;">`;

/**
 * Build a safe srcdoc string for iframe sandboxing.
 * Ensures CSP meta is present, DOMPurify cleans the content.
 */
export function buildSandboxedSrcdoc(htmlContent: string): string {
  // Client-side DOMPurify pass (defense in depth; server-side already cleaned)
  const cleaned = DOMPurify.sanitize(htmlContent, {
    FORCE_BODY: true,
    FORBID_TAGS: ['script', 'style', 'form', 'input', 'button', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onerror', 'onclick', 'onload', 'onmouseover', 'onfocus', 'onblur',
                  'onchange', 'onsubmit', 'onkeydown', 'onkeyup', 'onkeypress'],
  });

  // Ensure CSP meta is in the head
  if (cleaned.includes('<head>')) {
    return cleaned.replace('<head>', `<head>\n${CSP_META}`);
  }
  return `<!DOCTYPE html><html><head>${CSP_META}</head><body>${cleaned}</body></html>`;
}

/**
 * Sanitize markdown output for safe client-side rendering.
 * Used as fallback when DOMPurify is applied to raw HTML passthrough.
 */
export function sanitizeMarkdown(content: string): string {
  return DOMPurify.sanitize(content, {
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form'],
  });
}
