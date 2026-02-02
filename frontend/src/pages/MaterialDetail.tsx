import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getArtifact } from '../api/client';
import Mermaid from '../components/Mermaid';

export default function MaterialDetail() {
  const { id } = useParams<{ id: string }>();
  const [material, setMaterial] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        setLoading(true);
        const response = await getArtifact(id);
        setMaterial(response || null);
      } catch (error) {
        console.error('Failed to load material', error);
        setErrorMessage('Unable to load material.');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-gray-500">Loading material...</div>
      </div>
    );
  }

  if (!material || errorMessage) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="text-gray-500">{errorMessage || 'Material not found.'}</div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-center gap-2 text-sm text-gray-500">
        <Link to="/" className="hover:text-trust-blue flex items-center gap-1">
          <ArrowLeft className="w-3 h-3" /> Dashboard
        </Link>
        <span>/</span>
        <span>Material</span>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="text-xs uppercase tracking-wide text-gray-400 font-semibold mb-2">
          {material.artifact_type || 'material'}
        </div>
        <h1 className="text-2xl font-semibold text-gray-900 mb-3">
          Generated Material
        </h1>
        <div className="max-w-none text-gray-700">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                // Extract code string and clean it up
                let codeString = String(children);
                // Remove trailing newlines
                codeString = codeString.replace(/\n+$/, '');
                // Remove leading newlines
                codeString = codeString.replace(/^\n+/, '');
                const isInline = !className || !match;
                
                if (!isInline && match && match[1] === 'mermaid') {
                  return <Mermaid chart={codeString} />;
                }
                
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
              h1: ({ ...props }) => (
                <h1 className="text-3xl font-bold mt-8 mb-4 text-gray-900" {...props} />
              ),
              h2: ({ ...props }) => (
                <h2 className="text-2xl font-semibold mt-6 mb-3 text-gray-900" {...props} />
              ),
              h3: ({ ...props }) => (
                <h3 className="text-xl font-semibold mt-4 mb-2 text-gray-900" {...props} />
              ),
              h4: ({ ...props }) => (
                <h4 className="text-lg font-semibold mt-3 mb-2 text-gray-900" {...props} />
              ),
              p: ({ ...props }) => (
                <p className="mb-4 leading-relaxed" {...props} />
              ),
              ul: ({ ...props }) => (
                <ul className="list-disc list-inside mb-4 space-y-2 ml-4" {...props} />
              ),
              ol: ({ ...props }) => (
                <ol className="list-decimal list-inside mb-4 space-y-2 ml-4" {...props} />
              ),
              li: ({ ...props }) => (
                <li className="mb-1" {...props} />
              ),
              blockquote: ({ ...props }) => (
                <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4 text-gray-600" {...props} />
              ),
              a: ({ ...props }) => (
                <a className="text-trust-blue hover:text-blue-700 underline" {...props} />
              ),
              strong: ({ ...props }) => (
                <strong className="font-semibold" {...props} />
              ),
              em: ({ ...props }) => (
                <em className="italic" {...props} />
              ),
              hr: ({ ...props }) => (
                <hr className="my-6 border-gray-300" {...props} />
              ),
              pre: ({ ...props }) => (
                <pre className="bg-gray-100 rounded-lg p-4 overflow-x-auto mb-4" {...props} />
              ),
              table: ({ ...props }) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full border-collapse border border-gray-300" {...props} />
                </div>
              ),
              thead: ({ ...props }) => (
                <thead className="bg-gray-100" {...props} />
              ),
              tbody: ({ ...props }) => (
                <tbody {...props} />
              ),
              tr: ({ ...props }) => (
                <tr className="border-b border-gray-300" {...props} />
              ),
              th: ({ ...props }) => (
                <th className="border border-gray-300 px-4 py-2 text-left font-semibold" {...props} />
              ),
              td: ({ ...props }) => (
                <td className="border border-gray-300 px-4 py-2" {...props} />
              ),
            }}
          >
            {material.content || 'No content available.'}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
