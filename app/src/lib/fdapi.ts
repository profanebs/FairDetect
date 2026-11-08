export type ModelSpec = { id: string; label: string; role: string; available?: boolean; status?: string }
export type JudgeSpec = { id: string; label: string; shield?: string; spear?: string }
export type ModelScore = { pct50: number; mean100: number; nwin: number; words: number; windows: number[] }
export type AiRate = { basis: string; rate_word: number; rate_sent: number; n_flagged: number; n_sent: number; g0: number; r0: number }
export type JudgeVerdict = { rule: string; g: number; r: number; S: number; tier: string; band: string; flag: boolean; ai_rate?: AiRate }
export type ResultItem = { name: string; error: string | null; models: Record<string, ModelScore>; judge: Record<string, JudgeVerdict> }
export type Job = { id: string; status: string; done: number; total: number; current: string; results: ResultItem[] }

async function jpost<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!r.ok) throw new Error(await r.text())
  return r.json() as Promise<T>
}

export async function fetchModels(): Promise<{ models: ModelSpec[]; judges: JudgeSpec[] }> {
  const r = await fetch('/api/models')
  return r.json()
}

export async function submitJob(files: { name: string; data_b64: string }[], models: string[], judges: string[]) {
  return jpost<{ id: string; total: number }>('/api/jobs', { files, models, judges })
}

export async function getJob(id: string): Promise<Job> {
  const r = await fetch('/api/jobs/' + id)
  return r.json() as Promise<Job>
}

export function toBase64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf)
  let bin = ''
  const chunk = 0x8000
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode(...bytes.subarray(i, i + chunk))
  }
  return btoa(bin)
}

export function scoreColor(pct: number): string {
  if (pct < 20) return '#2e9e5b'
  if (pct < 50) return '#c9a227'
  if (pct < 80) return '#e07a1f'
  return '#c0392b'
}
