import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Clock, Target, BookOpen, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';
import { getPriorityQueue, recalculatePriority } from '../api/client';

interface PriorityItem {
  content_id: string;
  title: string;
  topics: string[];
  priority_score: number;
  priority_reasoning: string;
  signals?: {
    goal_match?: number;
    trending?: number;
    prerequisites?: number;
    behavior?: number;
  };
  word_count?: number;
  difficulty?: string;
}

interface PriorityQueueProps {
  userId: string;
  limit?: number;
  showContextMode?: boolean;
}

export default function PriorityQueue({ userId, limit = 10, showContextMode = false }: PriorityQueueProps) {
  const [queue, setQueue] = useState<PriorityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recalculating, setRecalculating] = useState(false);
  const [contextMode, setContextMode] = useState<'growth' | 'cram' | 'exploration'>('growth');

  const loadQueue = async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getPriorityQueue(userId, limit);
      if (response.status === 'success' && Array.isArray(response.queue)) {
        setQueue(response.queue);
      } else if (response.status === 'error') {
        setError(response.error || 'Failed to load priority queue');
        setQueue([]);
      } else {
        setError('Unexpected response format');
        setQueue([]);
      }
    } catch (err: any) {
      console.error('Failed to load priority queue', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load priority queue');
      setQueue([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    if (!userId) return;
    setRecalculating(true);
    try {
      await recalculatePriority(userId);
      await loadQueue();
    } catch (err: any) {
      console.error('Failed to recalculate priority', err);
      setError(err.response?.data?.detail || 'Failed to recalculate priority');
    } finally {
      setRecalculating(false);
    }
  };

  useEffect(() => {
    void loadQueue();
  }, [userId, limit]);

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600 bg-green-50';
    if (score >= 0.5) return 'text-blue-600 bg-blue-50';
    return 'text-gray-600 bg-gray-50';
  };

  const formatScore = (score: number) => {
    return (score * 100).toFixed(0);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <TrendingUp className="w-5 h-5 text-trust-blue" />
          <h2 className="text-xl font-semibold text-gray-900">Priority Queue</h2>
        </div>
        <div className="text-center py-8 text-gray-500">Loading prioritized content...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-red-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900">Priority Queue</h2>
        </div>
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={loadQueue}
          className="px-4 py-2 bg-trust-blue text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-5 h-5 text-trust-blue" />
          <h2 className="text-xl font-semibold text-gray-900">What to Study Next</h2>
        </div>
        <div className="flex items-center gap-2">
          {showContextMode && (
            <select
              value={contextMode}
              onChange={(e) => setContextMode(e.target.value as any)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-trust-blue focus:border-trust-blue"
            >
              <option value="growth">Growth Mode</option>
              <option value="cram">Cram Mode</option>
              <option value="exploration">Exploration</option>
            </select>
          )}
          <button
            onClick={handleRecalculate}
            disabled={recalculating}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors disabled:opacity-50"
            title="Recalculate priorities"
          >
            <RefreshCw className={`w-4 h-4 ${recalculating ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {queue.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-sm">No content available to prioritize.</p>
          <p className="text-xs text-gray-400 mt-1">Upload some materials to get started!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map((item, index) => (
            <Link
              key={item.content_id || index}
              to={`/content/${item.content_id}`}
              className="block p-4 border border-gray-200 rounded-lg hover:border-trust-blue hover:shadow-md transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3 mb-2">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-trust-blue/10 flex items-center justify-center text-sm font-semibold text-trust-blue">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 group-hover:text-trust-blue transition-colors line-clamp-2">
                        {item.title || 'Untitled Content'}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {item.priority_reasoning || 'Prioritized for your learning goals'}
                      </p>
                    </div>
                  </div>

                  {item.topics && item.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2 ml-11">
                      {item.topics.slice(0, 3).map((topic, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
                        >
                          {topic}
                        </span>
                      ))}
                      {item.topics.length > 3 && (
                        <span className="px-2 py-0.5 text-gray-400 text-xs">
                          +{item.topics.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {item.signals && (
                    <div className="flex items-center gap-4 mt-3 ml-11 text-xs text-gray-500">
                      {item.signals.goal_match !== undefined && (
                        <div className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          <span>Goal: {formatScore(item.signals.goal_match)}%</span>
                        </div>
                      )}
                      {item.signals.trending !== undefined && (
                        <div className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          <span>Recent: {formatScore(item.signals.trending)}%</span>
                        </div>
                      )}
                      {item.word_count && (
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>~{Math.ceil(item.word_count / 200)} min</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0">
                  <div className={`px-3 py-1.5 rounded-lg font-semibold text-sm ${getScoreColor(item.priority_score)}`}>
                    {formatScore(item.priority_score)}%
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {queue.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-500 text-center">
          <Sparkles className="w-3 h-3 inline mr-1" />
          Prioritized by goal alignment, recency, prerequisites, and your learning patterns
        </div>
      )}
    </div>
  );
}
