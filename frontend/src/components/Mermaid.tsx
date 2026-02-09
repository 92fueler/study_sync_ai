import { useEffect, useRef, useState } from 'react'

interface MermaidProps {
  chart: string
}

interface MermaidLike {
  initialize: (config: Record<string, unknown>) => void
  render: (id: string, chart: string) => Promise<{ svg?: string }>
}

declare global {
  interface Window {
    mermaid?: MermaidLike
  }
}

const MERMAID_SCRIPT_ID = 'studysync-mermaid-runtime'
const MERMAID_CDN_URL = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js'
let mermaidLoaderPromise: Promise<MermaidLike> | null = null

const escapeHtml = (text: string): string => {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }
  return text.replace(/[&<>"']/g, (m) => map[m])
}

const sanitizeMermaidCode = (code: string): string => {
  let sanitized = code.trim()
  sanitized = sanitized.replace(/\[([^\]]+)\]/g, (match, label) => {
    const trimmedLabel = label.trim()
    const needsQuoting =
      /[()?]/.test(trimmedLabel) &&
      !trimmedLabel.startsWith('"') &&
      !trimmedLabel.endsWith('"')

    if (needsQuoting) {
      const escapedLabel = trimmedLabel.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
      return `["${escapedLabel}"]`
    }
    return match
  })
  return sanitized
}

const waitForMermaidGlobal = (timeoutMs: number): Promise<MermaidLike> =>
  new Promise((resolve, reject) => {
    const startedAt = Date.now()
    const timer = window.setInterval(() => {
      if (window.mermaid) {
        window.clearInterval(timer)
        resolve(window.mermaid)
        return
      }
      if (Date.now() - startedAt > timeoutMs) {
        window.clearInterval(timer)
        reject(new Error('Mermaid runtime failed to initialize'))
      }
    }, 50)
  })

const loadMermaidRuntime = (): Promise<MermaidLike> => {
  if (window.mermaid) return Promise.resolve(window.mermaid)
  if (mermaidLoaderPromise) return mermaidLoaderPromise

  mermaidLoaderPromise = new Promise((resolve, reject) => {
    const existing = document.getElementById(MERMAID_SCRIPT_ID) as HTMLScriptElement | null
    if (existing) {
      void waitForMermaidGlobal(5000).then(resolve).catch(reject)
      return
    }

    const script = document.createElement('script')
    script.id = MERMAID_SCRIPT_ID
    script.src = MERMAID_CDN_URL
    script.async = true
    script.onload = () => {
      if (window.mermaid) {
        resolve(window.mermaid)
      } else {
        reject(new Error('Mermaid runtime not found on window'))
      }
    }
    script.onerror = () => reject(new Error('Failed to load Mermaid runtime'))
    document.head.appendChild(script)
  })

  return mermaidLoaderPromise
}

export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null)
  const mermaidRef = useRef<MermaidLike | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isInitialized) return
    let cancelled = false

    const init = async () => {
      try {
        const instance = await loadMermaidRuntime()
        if (cancelled || !instance) return
        if (typeof instance.initialize !== 'function') {
          console.error('Mermaid instance does not have initialize method', instance)
          return
        }
        mermaidRef.current = instance
        instance.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
          },
        })
        setIsInitialized(true)
      } catch (error) {
        console.error('Mermaid load error:', error)
      }
    }

    void init()
    return () => {
      cancelled = true
    }
  }, [isInitialized])

  useEffect(() => {
    if (!ref.current || !chart || !isInitialized || !mermaidRef.current) return
    ref.current.innerHTML = ''
    setError(null)

    let cleanedChart = chart.trim()
    if (!cleanedChart) {
      setError('Empty diagram code')
      ref.current.innerHTML = '<p class="text-sm text-gray-500 italic">No diagram content</p>'
      return
    }
    cleanedChart = sanitizeMermaidCode(cleanedChart)

    const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
    mermaidRef.current
      .render(id, cleanedChart)
      .then((result) => {
        if (ref.current && result.svg) {
          ref.current.innerHTML = result.svg
          setError(null)
          return
        }
        setError('Failed to generate diagram')
        if (ref.current) {
          ref.current.innerHTML = '<p class="text-sm text-red-500">Failed to render diagram</p>'
        }
      })
      .catch((error: unknown) => {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error('Mermaid rendering error:', error)
        setError(errorMessage)
        if (ref.current) {
          ref.current.innerHTML = `
            <div class="border border-red-200 bg-red-50 rounded-lg p-4">
              <p class="text-sm font-semibold text-red-800 mb-2">Diagram Rendering Error</p>
              <p class="text-xs text-red-600 mb-2">${escapeHtml(errorMessage)}</p>
              <details class="text-xs text-red-500">
                <summary class="cursor-pointer hover:text-red-700">Show diagram code</summary>
                <pre class="mt-2 p-2 bg-red-100 rounded text-xs overflow-x-auto">${escapeHtml(cleanedChart)}</pre>
              </details>
            </div>
          `
        }
      })
  }, [chart, isInitialized])

  return <div ref={ref} className="mermaid-container" />
}
