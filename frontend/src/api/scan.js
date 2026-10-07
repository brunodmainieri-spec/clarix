const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * Run a disk scan on the backend and return the hierarchical tree.
 * @param {{ path?: string, max_depth?: number, max_children?: number }} [opts]
 * @returns {Promise<{ ok: boolean, saved_to: string, disk_tree: object }>}
 */
export async function startScan(opts = {}) {
  const res = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: opts.path ?? '',
      max_depth: opts.max_depth ?? 2,
      max_children: opts.max_children ?? 12,
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
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return res.json()
}

/**
 * List files/folders inside a directory (for the files table).
 * @param {string} path
 * @param {number} [maxChildren]
 */
export async function fetchScanEntries(path, maxChildren = 200) {
  const url = new URL(`${API_BASE}/scan/entries`)
  url.searchParams.set('path', path)
  url.searchParams.set('max_children', String(maxChildren))

  const res = await fetch(url)
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return res.json()
}
