import { useEffect, useRef, useState } from 'react'

interface MermaidProps {
  chart: string
}

export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null)
  const mermaidRef = useRef<any>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (isInitialized) return
    let cancelled = false
    const loadMermaid = async () => {
      try {
        const mod = await import('mermaid/dist/mermaid.js')
        const instance = (mod as { default?: any }).default ?? mod
        if (cancelled || !instance) return
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
    void loadMermaid()
    return () => {
      cancelled = true
    }
  }, [isInitialized])

  useEffect(() => {
    if (ref.current && chart && isInitialized && mermaidRef.current) {
      // Clear previous content
      ref.current.innerHTML = ''
      
      const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      mermaidRef.current.render(id, chart).then((result: { svg?: string }) => {
        if (ref.current && result.svg) {
          ref.current.innerHTML = result.svg
        }
      }).catch((error: unknown) => {
        console.error('Mermaid rendering error:', error)
        if (ref.current) {
          ref.current.innerHTML = '<p class="text-red-500">Error rendering diagram</p>'
        }
      })
    }
  }, [chart, isInitialized])

  return <div ref={ref} className="mermaid-container" />
}
