import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { getArtifact } from '../api/client';

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
        <div className="prose max-w-none text-gray-700 whitespace-pre-line">
          {material.content || 'No content available.'}
        </div>
      </div>
    </div>
  );
}
