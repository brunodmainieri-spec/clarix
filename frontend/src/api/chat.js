const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * Send a chat message to the Clarix ReAct agent.
 * @param {string} message
 * @param {string | null} threadId
 * @returns {Promise<{ thread_id: string, reply: string, ui_actions?: object[] }>}
 */
export async function sendChat(message, threadId = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      thread_id: threadId,
    }),
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  return res.json()
}
