/** Keep post copy as text. Only section headings are removed from copied content. */
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
