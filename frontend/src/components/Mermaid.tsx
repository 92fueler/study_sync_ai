import { useEffect, useRef, useState } from 'react'
import type mermaid from 'mermaid'

interface MermaidProps {
  chart: string
}

// Helper function to escape HTML
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

// Helper function to sanitize Mermaid diagram code
// Fixes common syntax issues like unquoted labels with special characters
const sanitizeMermaidCode = (code: string): string => {
  let sanitized = code.trim()
  
  // Fix node labels in square brackets that contain special characters
  // Pattern: matches [label] where label contains problematic chars but isn't quoted
  sanitized = sanitized.replace(/\[([^\]]+)\]/g, (match, label) => {
    // Trim whitespace from label
    const trimmedLabel = label.trim()
    
    // Check if label contains special characters that need quoting
    // Special chars: parentheses, question marks
    // Only quote if not already quoted
    const needsQuoting = /[()?]/.test(trimmedLabel) && 
                         !trimmedLabel.startsWith('"') && 
                         !trimmedLabel.endsWith('"')
    
    if (needsQuoting) {
      // Escape any existing quotes and backslashes in the label
      const escapedLabel = trimmedLabel
        .replace(/\\/g, '\\\\')  // Escape backslashes first
        .replace(/"/g, '\\"')    // Escape quotes
      return `["${escapedLabel}"]`
    }
    return match
  })
  
  return sanitized
}

export default function Mermaid({ chart }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null)
  const mermaidRef = useRef<typeof mermaid | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isInitialized) return
    let cancelled = false
    const loadMermaid = async () => {
      try {
        // Prefer explicit ESM entry to avoid package entry resolution issues
        let mermaidModule: any
        try {
          mermaidModule = await import('mermaid/dist/mermaid.esm.mjs')
        } catch {
          mermaidModule = await import('mermaid')
        }
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
      // Clear previous content and error state
      ref.current.innerHTML = ''
      setError(null)
      
      // Clean and validate chart code
      let cleanedChart = chart.trim()
      
      // Basic validation: check if chart is not empty
      if (!cleanedChart) {
        setError('Empty diagram code')
        if (ref.current) {
          ref.current.innerHTML = '<p class="text-sm text-gray-500 italic">No diagram content</p>'
        }
        return
      }
      
      // Sanitize Mermaid code to fix common syntax issues
      cleanedChart = sanitizeMermaidCode(cleanedChart)
      
      const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      mermaidRef.current.render(id, cleanedChart).then((result: { svg?: string }) => {
        if (ref.current && result.svg) {
          ref.current.innerHTML = result.svg
          setError(null)
        } else {
          setError('Failed to generate diagram')
          if (ref.current) {
            ref.current.innerHTML = '<p class="text-sm text-red-500">Failed to render diagram</p>'
          }
        }
      }).catch((error: unknown) => {
        const errorMessage = error instanceof Error ? error.message : String(error)
        console.error('Mermaid rendering error:', error)
        setError(errorMessage)
        
        if (ref.current) {
          // Show user-friendly error message
          const errorDisplay = `
            <div class="border border-red-200 bg-red-50 rounded-lg p-4">
              <p class="text-sm font-semibold text-red-800 mb-2">Diagram Rendering Error</p>
              <p class="text-xs text-red-600 mb-2">${escapeHtml(errorMessage)}</p>
              <details class="text-xs text-red-500">
                <summary class="cursor-pointer hover:text-red-700">Show diagram code</summary>
                <pre class="mt-2 p-2 bg-red-100 rounded text-xs overflow-x-auto">${escapeHtml(cleanedChart)}</pre>
              </details>
            </div>
          `
          ref.current.innerHTML = errorDisplay
        }
      })
    }
  }, [chart, isInitialized])

  return <div ref={ref} className="mermaid-container" />
}
