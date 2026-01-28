import { useState, useEffect, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Headphones, Video, Link as LinkIcon, Code, Search, MoreVertical, Clock } from 'lucide-react'
import { cn } from '../utils/cn'
import { uploadFiles, listArtifacts } from '../api/client'

interface Artifact {
  id: string
  title: string
  description: string
  type: 'text' | 'audio' | 'video' | 'pdf' | 'markdown' | 'link' | 'code'
  status: 'processing' | 'complete'
  size?: string
  duration?: string
  createdAt: string
}

interface KnowledgeBankProps {
  userId: string
}

const typeIcons = {
  text: FileText,
  audio: Headphones,
  video: Video,
  pdf: FileText,
  markdown: FileText,
  link: LinkIcon,
  code: Code,
}

const typeColors = {
  text: 'text-blue-600',
  audio: 'text-purple-600',
  video: 'text-pink-600',
  pdf: 'text-red-600',
  markdown: 'text-green-600',
  link: 'text-green-600',
  code: 'text-indigo-600',
}

export default function KnowledgeBank({ userId }: KnowledgeBankProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<string>('all')
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  useEffect(() => {
    loadArtifacts()
  }, [userId])

  const loadArtifacts = async () => {
    if (!userId || userId.trim() === '') {
      console.warn('Cannot load artifacts: userId is missing')
      return
    }
    try {
      const response = await listArtifacts(userId)
      // Transform API response to match our Artifact interface
      // This is a mock transformation - adjust based on actual API response
      setArtifacts(response.artifacts || [])
    } catch (error: any) {
      console.error('Failed to load artifacts:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to load artifacts'
      console.error('Error details:', errorMessage)
    }
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true)
    try {
      const response = await uploadFiles(userId, acceptedFiles)
      
      // Add uploaded files to artifacts list with processing status
      const newArtifacts: Artifact[] = response.results.map((result: any) => ({
        id: result.content_id || result.task_id || `temp_${Date.now()}`,
        title: result.filename || 'Untitled',
        description: 'Processing...',
        type: getFileType(result.filename || ''),
        status: result.status === 'error' ? 'complete' : 'processing',
        createdAt: new Date().toISOString(),
      }))
      
      setArtifacts((prev) => [...newArtifacts, ...prev])
      
      // Poll for status updates
      response.results.forEach((result: any) => {
        if (result.task_id && result.status === 'processing') {
          pollUploadStatus(result.task_id, result.filename || '')
        }
      })
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }, [userId])

  const pollUploadStatus = async (taskId: string, filename: string) => {
    // In a real implementation, you'd poll the status endpoint
    // For now, we'll simulate completion after a delay
    setTimeout(() => {
      setArtifacts((prev) =>
        prev.map((artifact) =>
          artifact.id === taskId
            ? { ...artifact, status: 'complete', description: 'Processing complete' }
            : artifact
        )
      )
    }, 5000)
  }

  const getFileType = (filename: string): Artifact['type'] => {
    const ext = filename.toLowerCase().split('.').pop()
    if (['mp3', 'wav'].includes(ext || '')) return 'audio'
    if (['mp4', 'mov'].includes(ext || '')) return 'video'
    if (ext === 'pdf') return 'pdf'
    if (['md', 'markdown'].includes(ext || '')) return 'markdown'
    return 'text'
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'audio/*': ['.mp3', '.wav'],
      'video/*': ['.mp4', '.mov'],
    },
    multiple: true,
  })

  const filteredArtifacts = artifacts.filter((artifact) => {
    const matchesSearch = artifact.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      artifact.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = filter === 'all' || 
      (filter === 'processing' && artifact.status === 'processing') ||
      (filter === 'complete' && artifact.status === 'complete') ||
      (filter === artifact.type)
    return matchesSearch && matchesFilter
  })

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    return `${Math.floor(diffHours / 24)} day${Math.floor(diffHours / 24) > 1 ? 's' : ''} ago`
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Knowledge Bank</h1>
        <p className="text-gray-600">Automated ingestion & processing of your learning materials.</p>
      </div>

      {/* Bulk Dump Zone */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-16 text-center mb-8 transition-colors cursor-pointer',
          isDragActive ? 'border-blue-600 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
        <p className="text-lg text-gray-700 mb-2">
          Drag and drop raw inputs here (PDF, MP3, MP4, Markdown, URL) to start processing instantly.
        </p>
        <button
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          Browse Files
        </button>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search master notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'processing', 'complete', 'audio', 'video'].map((filterOption) => (
            <button
              key={filterOption}
              onClick={() => setFilter(filterOption)}
              className={cn(
                'px-4 py-2 rounded-lg font-medium text-sm transition-colors capitalize',
                filter === filterOption
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {filterOption}
            </button>
          ))}
        </div>
      </div>

      {/* Artifacts Grid */}
      {isUploading && (
        <div className="mb-4 text-blue-600">Uploading files...</div>
      )}
      
      {filteredArtifacts.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">No artifacts found</p>
          <p className="text-sm">Upload files to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredArtifacts.map((artifact) => {
            const Icon = typeIcons[artifact.type] || FileText
            return (
              <div
                key={artifact.id}
                className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={cn('p-2 rounded-lg bg-gray-100', typeColors[artifact.type])}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 line-clamp-1">{artifact.title}</h3>
                    </div>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>

                <div className="mb-4">
                  <span
                    className={cn(
                      'inline-block px-2 py-1 rounded text-xs font-medium',
                      artifact.status === 'processing'
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-green-100 text-green-700'
                    )}
                  >
                    {artifact.status === 'processing' ? 'Processing' : 'Complete'}
                  </span>
                </div>

                <p className="text-sm text-gray-600 mb-4 line-clamp-2">{artifact.description}</p>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-4">
                    {artifact.duration && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {artifact.duration}
                      </span>
                    )}
                    {artifact.size && <span>{artifact.size}</span>}
                  </div>
                  <span>{formatTimeAgo(artifact.createdAt)}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
