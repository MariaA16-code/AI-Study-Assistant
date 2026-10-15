// Keeps each document's chat in memory only. It survives moving between pages
// (for example after taking a quiz) but disappears when the browser page is refreshed,
// because chat history is not saved on the server.

const chats = new Map()

export function getChat(documentId) {
  return chats.get(String(documentId)) || []
}

export function saveChat(documentId, messages) {
  chats.set(String(documentId), messages)
}

export function clearChats() {
  chats.clear()
}