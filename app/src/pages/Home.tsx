import { useEffect, useRef, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import zh from '@/locales/zh.json'
import { fetchModels, getJob, scoreColor, submitJob, toBase64, type Job, type JudgeSpec, type ModelSpec } from '@/lib/fdapi'

type FileEntry = { name: string; b64: string; size: number }

const TIER: Record<string, string> = { caught: zh.tier_caught, t2: zh.tier_t2, t1: zh.tier_t1 }

export default function Home() {
  const [models, setModels] = useState<ModelSpec[]>([])
  const [judges, setJudges] = useState<JudgeSpec[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [selectedJudges, setSelectedJudges] = useState<string[]>([])
  const [files, setFiles] = useState<FileEntry[]>([])
  const [paste, setPaste] = useState('')
  const [job, setJob] = useState<Job | null>(null)
  const [busy, setBusy] = useState(false)
  const [drag, setDrag] = useState(false)
  const pollRef = useRef(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchModels().then((r) => {
      setModels(r.models)
      setJudges(r.judges)
      const firstJudge = r.judges[0]
      if (firstJudge) {
        setSelectedJudges([firstJudge.id])
        const ids = r.models
          .filter((m) => m.available && (m.id === firstJudge.shield || m.id === firstJudge.spear))
          .map((m) => m.id)
        setSelected(ids.length ? ids : r.models.filter((m) => m.available).map((m) => m.id))
      } else {
        setSelected(r.models.filter((m) => m.available).map((m) => m.id))
      }
    }).catch(() => {})
    return () => window.clearTimeout(pollRef.current)
  }, [])

  async function addFiles(list: FileList | File[]) {
    const arr = Array.from(list).filter((f) => f.size <= 8 * 1024 * 1024)
    const out: FileEntry[] = []
    for (const f of arr) {
      const buf = await f.arrayBuffer()
      out.push({ name: f.name, b64: toBase64(buf), size: f.size })
    }
    setFiles((prev) => [...prev, ...out])
  }

  function addPasted() {
    const t = paste.trim()
    if (t.length < 30) return
    const name = 'pasted-' + new Date().toISOString().slice(11, 19) + '.txt'
    const bytes = new TextEncoder().encode(t)
    let bin = ''
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000))
    setFiles((prev) => [...prev, { name, b64: btoa(bin), size: bytes.length }])
    setPaste('')
  }

  async function start() {
    if (!files.length || !selected.length || busy) return
    setBusy(true)
    setJob(null)
    try {
      const { id } = await submitJob(files.map((f) => ({ name: f.name, data_b64: f.b64 })), selected, selectedJudges)
      const tick = async () => {
        const j = await getJob(id)
        setJob(j)
        if (j.status !== 'done') pollRef.current = window.setTimeout(tick, 800)
        else setBusy(false)
      }
      await tick()
    } catch (e) {
      setBusy(false)
      window.alert(String(e))
    }
  }

  const toggleModel = (id: string) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  const toggleJudge = (id: string) =>
    setSelectedJudges((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  const pct = job ? Math.round((100 * job.done) / Math.max(1, job.total)) : 0

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <header className="flex items-baseline justify-between">
          <div>
            <h1 className="text-2xl font-bold">{zh.app_title}</h1>
            <p className="text-sm text-muted-foreground">{zh.subtitle}</p>
          </div>
          <Badge variant="secondary">local · {window.location.host}</Badge>
        </header>

        <div className="grid gap-6 md:grid-cols-5">
          <Card className="md:col-span-3">
            <CardHeader>
              <CardTitle className="text-base">{zh.input_title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className={
                  'flex min-h-24 cursor-pointer items-center justify-center rounded-md border-2 border-dashed p-6 text-center text-sm ' +
                  (drag ? 'border-primary bg-muted' : 'border-muted-foreground/30')
                }
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => { e.preventDefault(); setDrag(false); addFiles(e.dataTransfer.files) }}
              >
                {drag ? zh.drop_active : zh.drop_hint}
                <input
                  ref={inputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => { if (e.target.files) addFiles(e.target.files); e.currentTarget.value = '' }}
                />
              </div>
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">{zh.paste_label}</p>
                <textarea
                  className="h-24 w-full rounded-md border bg-transparent p-2 text-sm"
                  placeholder={zh.paste_placeholder}
                  value={paste}
                  onChange={(e) => setPaste(e.target.value)}
                />
                <Button variant="outline" size="sm" onClick={addPasted} disabled={paste.trim().length < 30}>
                  {zh.add_pasted}
                </Button>
              </div>
              {files.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">{zh.files_label} ({files.length})</p>
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center justify-between rounded border px-2 py-1 text-sm">
                      <span className="truncate">{f.name}</span>
                      <span className="ml-2 shrink-0 text-xs text-muted-foreground">{Math.ceil(f.size / 1024)} KB</span>
                    </div>
                  ))}
                  <Button variant="ghost" size="sm" onClick={() => setFiles([])}>{zh.clear}</Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">{zh.options_title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">{zh.models_label}</p>
                {models.map((m) => (
                  <label key={m.id} className={'flex items-center gap-2 text-sm' + (m.available === false ? ' opacity-50' : '')}>
                    <Checkbox checked={selected.includes(m.id)} disabled={m.available === false} onCheckedChange={() => toggleModel(m.id)} />
                    <span>{m.label}{m.available === false ? ' (model missing)' : ''}</span>
                  </label>
                ))}
                {models.length === 0 && <p className="text-xs text-muted-foreground">No models configured. Edit config/models.json.</p>}
                {models.length > 0 && models.every((m) => m.available === false) && (
                  <p className="text-xs text-muted-foreground">
                    No model is ready. Put checkpoints in models/ and edit config/models.json (see docs/MODEL-CONTRACT.md).
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">{zh.judge_label}</p>
                {judges.map((j) => (
                  <label key={j.id} className="flex items-center gap-2 text-sm">
                    <Checkbox checked={selectedJudges.includes(j.id)} onCheckedChange={() => toggleJudge(j.id)} />
                    {j.label}
                  </label>
                ))}
              </div>
              <Button className="w-full" onClick={start} disabled={!files.length || !selected.length || !selectedJudges.length || busy}>
                {busy ? zh.detecting : zh.start}
              </Button>
            </CardContent>
          </Card>
        </div>

        {job && (
          <Card>
            <CardContent className="space-y-2 pt-6">
              <div className="flex items-center justify-between text-sm">
                <span>{zh.progress_label}</span>
                <span className="text-muted-foreground">
                  {job.done}/{job.total} {job.current ? '· ' + job.current : ''}
                </span>
              </div>
              <Progress value={pct} />
              {job.status === 'done' && (
                <div className="space-y-3 pt-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <Button size="sm" onClick={() => window.open('/api/jobs/' + job.id + '/report', '_blank')}>
                      {zh.report}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        const a = document.createElement('a')
                        a.href = '/api/jobs/' + job.id + '/pdf'
                        a.download = 'FairDetect-' + job.id + '.pdf'
                        document.body.appendChild(a)
                        a.click()
                        a.remove()
                      }}
                    >
                      {zh.export_pdf}
                    </Button>
                    <a
                      className="text-xs text-muted-foreground underline"
                      href={'/api/jobs/' + job.id + '/report'}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {zh.report_new_tab}
                    </a>
                  </div>
                  <p className="text-xs font-medium text-muted-foreground">{zh.report_inline}</p>
                  <iframe
                    className="w-full rounded-md border"
                    style={{ height: '900px' }}
                    src={'/api/jobs/' + job.id + '/report'}
                    title={zh.report_inline}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="space-y-4">
          <h2 className="text-lg font-semibold">{zh.results_title}</h2>
          {!job && <p className="text-sm text-muted-foreground">{zh.no_results}</p>}
          {job?.results.map((r, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{r.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {r.error ? (
                  <p className="text-sm text-destructive">{r.error}</p>
                ) : (
                  <>
                    <div className="flex flex-wrap gap-2">
                      {selectedJudges.filter((id) => r.judge[id]).map((id) => {
                        const j = r.judge[id]
                        const label = judges.find((x) => x.id === id)?.label ?? id.toUpperCase()
                        return (
                          <Badge key={id} variant={j.S >= 20 ? 'destructive' : 'secondary'}>
                            {label} · {zh.ai_rate} {j.ai_rate ? j.ai_rate.rate_word + '%' : '—'} · S={j.S} · {TIER[j.tier] ?? j.tier}{j.flag ? ' · ' + zh.flag_mark : ''}
                          </Badge>
                        )
                      })}
                    </div>
                    <div className="space-y-2">
                      {Object.entries(r.models).map(([mid, s]) => {
                        const m = models.find((x) => x.id === mid)
                        return (
                            <div key={mid} className="flex flex-wrap items-center gap-3">
                              <span className="w-44 truncate text-xs text-muted-foreground">{m?.label ?? mid}</span>
                              <span
                                className="inline-flex min-w-12 justify-center rounded px-2 py-0.5 text-xs font-semibold text-white"
                                style={{ background: scoreColor(s.pct50) }}
                              >
                                {s.pct50}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {s.words} {zh.words} · {s.nwin} {zh.windows_n} · {zh.mean} {s.mean100}
                              </span>
                              <span className="flex flex-1 flex-wrap gap-0.5">
                                {s.windows.map((w, k) => (
                                  <span
                                    key={k}
                                    className="inline-block h-3 w-1.5 rounded-sm"
                                    style={{ background: scoreColor(w * 100) }}
                                    title={w.toFixed(2)}
                                  />
                                ))}
                              </span>
                            </div>
                        )
                      })}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <p className="text-xs text-muted-foreground">{zh.score_note}</p>
      </div>
    </div>
  )
}
