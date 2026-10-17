// Keeps each document's revision guide in memory only.
// It survives moving between tabs and pages, and disappears on refresh or logout.

const guides = new Map()

export const getGuide = (documentId) => guides.get(String(documentId)) || null
export const saveGuide = (documentId, guide) => guides.set(String(documentId), guide)
export const clearGuides = () => guides.clear()