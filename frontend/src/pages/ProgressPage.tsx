import { useEffect, useState } from 'react';

import { useAuthStore } from '@/stores/store';
import apiClient from '@/utils/api';

interface ProgressData {
  id: number;
  user_id: number;
  topic_id: number;
  questions_attempted: number;
  questions_correct: number;
  accuracy_score: number;
  last_attempted: string;
}

interface Summary {
  total_questions_attempted: number;
  total_accuracy: number;
  topics_studied: number;
  weak_topics: string[];
  strong_topics: string[];
}

interface LearningPathItem {
  topic_id: number;
  topic_name: string;
}

interface EvidenceData {
  baseline_accuracy: number;
  current_accuracy: number;
  learning_gain: number;
  baseline_window_attempts: number;
  current_window_attempts: number;
  total_questions_answered: number;
  confidence_trend: number;
}

interface EventRow {
  id: number;
  event_name: string;
  created_at: string;
}

export default function ProgressPage() {
  const user = useAuthStore((state) => state.user);

  const [progress, setProgress] = useState<ProgressData[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [topicNames, setTopicNames] = useState<Record<number, string>>({});
  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    fetchProgressData();
  }, [user?.id]);

  const fetchProgressData = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [progressRes, summaryRes, pathRes, evidenceRes, eventsRes] = await Promise.all([
        apiClient.get(`/progress/user/${user.id}`),
        apiClient.get(`/progress/summary/${user.id}`),
        apiClient.get(`/recommendations/learning-path/${user.id}`),
        apiClient.get(`/progress/evidence/${user.id}`),
        apiClient.get(`/progress/experiments/${user.id}/events`),
      ]);

      setProgress(progressRes.data.progress_records || []);
      setSummary(summaryRes.data);
      setEvidence(evidenceRes.data || null);
      setEvents(eventsRes.data.events || []);

      const namesById: Record<number, string> = {};
      (pathRes.data.path || []).forEach((item: LearningPathItem) => {
        namesById[item.topic_id] = item.topic_name;
      });
      setTopicNames(namesById);
    } catch (fetchErr) {
      console.error('Failed to fetch progress data:', fetchErr);
      setError('Failed to load progress data. Please refresh and try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading progress...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="section-title">Your Learning Progress</h1>

        {error && (
          <div className="card bg-red-50 border-l-4 border-red-400 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {summary && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <p className="text-gray-600 text-sm">Total Questions</p>
              <p className="text-3xl font-bold text-blue-600">{summary.total_questions_attempted}</p>
              <p className="text-xs text-gray-500 mt-2">{summary.total_accuracy.toFixed(1)}% average accuracy</p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm">Topics Mastered</p>
              <p className="text-3xl font-bold text-green-600">{summary.strong_topics.length}</p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm">Areas to Focus</p>
              <p className="text-3xl font-bold text-orange-600">{summary.weak_topics.length}</p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm">Experiment Events</p>
              <p className="text-3xl font-bold text-indigo-600">{events.length}</p>
            </div>
          </div>
        )}

        {evidence && (
          <div className="card mb-8 bg-indigo-50 border-l-4 border-indigo-400">
            <h3 className="subsection-title text-indigo-800">Dissertation Evidence Layer</h3>
            <div className="grid md:grid-cols-4 gap-3 mt-3 text-sm">
              <div className="bg-white border border-indigo-100 rounded p-3">
                <p className="text-gray-500">Baseline</p>
                <p className="font-semibold text-indigo-800">{(evidence.baseline_accuracy * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white border border-indigo-100 rounded p-3">
                <p className="text-gray-500">Current</p>
                <p className="font-semibold text-indigo-800">{(evidence.current_accuracy * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white border border-indigo-100 rounded p-3">
                <p className="text-gray-500">Gain</p>
                <p className="font-semibold text-indigo-800">{(evidence.learning_gain * 100).toFixed(1)} pp</p>
              </div>
              <div className="bg-white border border-indigo-100 rounded p-3">
                <p className="text-gray-500">Confidence trend</p>
                <p className="font-semibold text-indigo-800">{(evidence.confidence_trend * 100).toFixed(1)} pp</p>
              </div>
            </div>
          </div>
        )}

        <div className="card">
          <h3 className="subsection-title">Performance by Topic</h3>

          {progress.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Topic</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Attempted</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Correct</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Accuracy</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {progress.map((item) => (
                    <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{topicNames[item.topic_id] || `Topic ${item.topic_id}`}</td>
                      <td className="text-center py-3 px-4 text-gray-600">{item.questions_attempted}</td>
                      <td className="text-center py-3 px-4 text-gray-600">{item.questions_correct}</td>
                      <td className="text-center py-3 px-4">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                item.accuracy_score >= 80
                                  ? 'bg-green-500'
                                  : item.accuracy_score >= 60
                                    ? 'bg-orange-500'
                                    : 'bg-red-500'
                              }`}
                              style={{ width: `${item.accuracy_score}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">{item.accuracy_score.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="text-center py-3 px-4">
                        {item.accuracy_score >= 80 ? (
                          <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">Mastered</span>
                        ) : item.accuracy_score >= 60 ? (
                          <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm">Review</span>
                        ) : (
                          <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm">Focus</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center py-8 text-gray-600">No progress data yet. Start learning to see your progress!</p>
          )}
        </div>

        {events.length > 0 && (
          <div className="card mt-8">
            <h3 className="subsection-title">Experiment Instrumentation Feed</h3>
            <p className="text-sm text-gray-600 mb-3">Recent telemetry events supporting evidence and A/B analysis.</p>
            <div className="space-y-2">
              {events.slice(0, 8).map((event) => (
                <div key={event.id} className="text-sm border border-gray-200 rounded p-2 bg-gray-50">
                  <span className="font-semibold text-gray-800">{event.event_name}</span>
                  <span className="text-gray-500 ml-2">{new Date(event.created_at).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
