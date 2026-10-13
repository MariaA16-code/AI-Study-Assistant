// Merge sources that point to the same place, so the list has no repeats.
export function mergeSources(sources) {
  const merged = new Map()
  for (const s of sources) {
    const key = `${s.chapter}|${s.page}|${s.page_end}`
    if (!merged.has(key)) merged.set(key, { ...s, snippets: [] })
    if (s.snippet) merged.get(key).snippets.push(s.snippet)
  }
  return [...merged.values()]
}

// PDFs have real page numbers. DOCX and TXT only have approximate sections.
export function pageLabel(source, isPdf) {
  if (source.page == null) return ''
  const range =
    source.page_end && source.page_end !== source.page
      ? `${source.page}–${source.page_end}`
      : `${source.page}`
  return isPdf ? `PDF page ${range}` : `Section ~${range}`
}