import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

interface MermaidProps {
  chart: string
}

export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (!isInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
        },
      })
      setIsInitialized(true)
    }
  }, [isInitialized])

  useEffect(() => {
    if (ref.current && chart && isInitialized) {
      // Clear previous content
      ref.current.innerHTML = ''
      
      const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      mermaid.render(id, chart).then((result) => {
        if (ref.current) {
          ref.current.innerHTML = result.svg
        }
      }).catch((error) => {
        console.error('Mermaid rendering error:', error)
        if (ref.current) {
          ref.current.innerHTML = '<p class="text-red-500">Error rendering diagram</p>'
        }
      })
    }
  }, [chart, isInitialized])

  return <div ref={ref} className="mermaid-container" />
}
