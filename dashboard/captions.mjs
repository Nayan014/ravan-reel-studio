/** Split the saved authoring text without changing its content. */
export function captionSections(text) {
  const lines = text.replace(/\r\n?/g, '\n').split('\n');
  const sections = [];
  let label = 'Caption', content = [];
  const flush = () => {
    const value = content.join('\n').trim();
    if (value) sections.push({ label, text: value });
    content = [];
  };
  for (const line of lines) {
    if (/^\s*[-=]{4,}\s*$/.test(line)) continue;
    // A document title is context, not part of a caption. Hashtags remain untouched.
    if (/^#\s+/.test(line)) continue;
    const heading = /^#{2,6}\s+(.+?)\s*#*\s*$/.exec(line)
      || /^\s*(INSTAGRAM|YOUTUBE(?: SHORTS)?|TIKTOK|LINKEDIN)\s*$/i.exec(line);
    if (heading) { flush(); label = heading[1]; continue; }
    const field = /^\s*(Title|Description):\s*(.*)$/i.exec(line);
    if (field && /youtube/i.test(label)) {
      flush(); label = `YouTube ${field[1].toLowerCase()}`;
      if (field[2]) content.push(field[2]);
      continue;
    }
    content.push(line);
  }
  flush();
  return sections.length ? sections : text.trim() ? [{ label: 'Caption', text: text.trim() }] : [];
}

const escapeHtml = value => value.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

/** Presentation order is independent of source order and copy indices. */
export function captionRows(sections) {
  const entries = sections.map((section, index) => ({ section, index }));
  const take = labels => labels.flatMap(label => entries.filter(item => item.section.label.trim().toLowerCase() === label));
  const rows = [take(['instagram', 'tiktok']), take(['youtube title', 'youtube description'])].filter(row => row.length);
  const linkedin = take(['linkedin']);
  const placed = new Set([...rows.flat(), ...linkedin].map(item => item.index));
  return [...rows, ...entries.filter(item => !placed.has(item.index)).map(item => [item]), ...(linkedin.length ? [linkedin] : [])];
}

/** Small, non-nested emphasis markers; never interpret source HTML as markup. */
export function formatCaption({ label, text }) {
  let html = '', plain = '', end = 0, styled = false;
  const markers = /\*\*([^\n]+?)\*\*|\*([^*\n]+)\*|~~([^\n]+?)~~/g;
  for (const match of text.matchAll(markers)) {
    const value = match[1] ?? match[2] ?? match[3];
    if (value !== value.trim() || text[match.index - 1] === '\\') continue;
    const before = text.slice(end, match.index);
    const tag = match[1] !== undefined ? 'strong' : match[2] !== undefined ? 'em' : 's';
    html += escapeHtml(before) + `<${tag}>${escapeHtml(value)}</${tag}>`;
    plain += before + value;
    end = match.index + match[0].length;
    styled = true;
  }
  html += escapeHtml(text.slice(end));
  plain += text.slice(end);
  const linkedin = label.trim().toLowerCase() === 'linkedin';
  const rich = linkedin || label.trim().toLowerCase() === 'youtube description';
  return {
    text: plain,
    html: rich ? html : escapeHtml(plain),
    clipboardHtml: rich && styled ? `<div>${html.replace(/\n/g, '<br>')}</div>` : '',
    hint: linkedin
      ? 'Copy formatted includes styled text. Check the result in your LinkedIn post composer after pasting; available styles can vary by account.'
      : rich
      ? 'YouTube descriptions support bold, italic and strikethrough. Check the result in YouTube Studio after pasting; use its formatting toolbar if styles are removed.'
      : 'Copies as normal text. Paragraphs, bullet characters, hashtags and mentions are preserved.',
  };
}

/** Include normal text in every copy, and fall back when rich clipboard access fails. */
export async function writeCaptionClipboard({ text, clipboardHtml = '' }, clipboard = globalThis.navigator?.clipboard, Item = globalThis.ClipboardItem) {
  if (clipboardHtml && Item && clipboard?.write) {
    try {
      await clipboard.write([new Item({
        'text/plain': new Blob([text], { type: 'text/plain' }),
        'text/html': new Blob([clipboardHtml], { type: 'text/html' }),
      })]);
      return 'formatted';
    } catch { /* The normal-text attempt below must succeed before reporting a copy. */ }
  }
  await clipboard.writeText(text);
  return 'plain';
}
