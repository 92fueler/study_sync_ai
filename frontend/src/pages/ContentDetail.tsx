import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, FileText, Clock, Tag } from 'lucide-react';
import { getContent } from '../api/client';

export default function ContentDetail() {
  const { id } = useParams<{ id: string }>();
  const [userId, setUserId] = useState('');
  const [content, setContent] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const storedUserId = localStorage.getItem('user_id');
    if (storedUserId) {
      setUserId(storedUserId);
    } else {
      const tempUserId = `user_${Date.now()}`;
      localStorage.setItem('user_id', tempUserId);
      setUserId(tempUserId);
    }
  }, []);

  useEffect(() => {
    if (!id || !userId) return;
    const load = async () => {
      try {
        setLoading(true);
        const response = await getContent(userId, id, true);
        setContent(response || null);
      } catch (error: any) {
        console.error('Failed to load content', error);
        setErrorMessage(error.response?.data?.detail || 'Unable to load content.');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [id, userId]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-gray-500">Loading content...</div>
      </div>
    );
  }

  if (!content || errorMessage) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-red-600">{errorMessage || 'Content not found.'}</div>
        <Link to="/" className="text-trust-blue hover:underline mt-4 inline-block">
          ← Back to Knowledge Bank
        </Link>
      </div>
    );
  }

  const topics = typeof content.topics === 'string' 
    ? JSON.parse(content.topics || '[]') 
    : (content.topics || []);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-trust-blue flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Knowledge Bank
        </Link>
        <span>/</span>
        <span>Content</span>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-5 h-5 text-gray-400" />
              <span className="text-xs uppercase tracking-wide text-gray-400 font-semibold">
                {content.media_type || 'CONTENT'}
              </span>
            </div>
            <h1 className="text-2xl font-semibold text-gray-900 mb-3">
              {content.title || 'Untitled Content'}
            </h1>
            
            <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
              {content.word_count && (
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>~{Math.ceil(content.word_count / 200)} min read</span>
                </div>
              )}
              {content.status && (
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  content.status === 'PROCESSED' 
                    ? 'bg-green-100 text-green-700' 
                    : content.status === 'PROCESSING'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {content.status}
                </span>
              )}
            </div>

            {topics.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {topics.map((topic: string, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                  >
                    <Tag className="w-3 h-3" />
                    {topic}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-gray-200 pt-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Content</h2>
          <div className="prose max-w-none">
            {content.raw_text ? (
              <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border border-gray-200 overflow-x-auto">
                {content.raw_text}
              </pre>
            ) : (
              <p className="text-gray-500 italic">No content available.</p>
            )}
          </div>
        </div>

        {content.uploaded_at && (
          <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500">
            Uploaded: {new Date(content.uploaded_at).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}
