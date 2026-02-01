import { useEffect, useRef, useState } from 'react'
import type mermaid from 'mermaid'

interface MermaidProps {
  chart: string
}

export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null)
  const mermaidRef = useRef<typeof mermaid | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (isInitialized) return
    let cancelled = false
    const loadMermaid = async () => {
      try {
        // Try standard import first
        const mermaidModule = await import('mermaid')
        // Handle different export formats
        const instance = 
          mermaidModule.default || 
          (mermaidModule as any).mermaid || 
          mermaidModule
        
        if (cancelled || !instance) return
        
        // Check if initialize method exists
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
        console.error('Error details:', {
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined
        })
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
