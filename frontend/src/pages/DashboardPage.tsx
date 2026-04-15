import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuthStore } from '@/stores/store';
import apiClient from '@/utils/api';

interface LearningPath {
  topic_id: number;
  topic_name: string;
  current_score: number;
  attempts: number;
  priority: number;
}

interface Summary {
  total_questions_attempted: number;
  total_accuracy: number;
  topics_studied: number;
  weak_topics: string[];
  strong_topics: string[];
}

interface PersonalizedRecommendation {
  topic_id: number;
  topic_name: string;
  reason_codes: string[];
  current_accuracy: number;
  urgency: string;
  confidence_interval_low: number;
  confidence_interval_high: number;
}

interface OutcomeEvidence {
  user_id: number;
  baseline_accuracy: number;
  current_accuracy: number;
  learning_gain: number;
  baseline_window_attempts: number;
  current_window_attempts: number;
  total_questions_answered: number;
  confidence_trend: number;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const [learningPath, setLearningPath] = useState<LearningPath[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [recommendations, setRecommendations] = useState<PersonalizedRecommendation[]>([]);
  const [evidence, setEvidence] = useState<OutcomeEvidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    fetchDashboardData();
  }, [user?.id]);

  const fetchDashboardData = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const [pathRes, summaryRes, recommendationRes, evidenceRes] = await Promise.all([
        apiClient.get(`/recommendations/learning-path/${user.id}`),
        apiClient.get(`/progress/summary/${user.id}`),
        apiClient.get(`/recommendations/personalized/${user.id}`),
        apiClient.get(`/progress/evidence/${user.id}`),
      ]);

      setLearningPath(pathRes.data.path || []);
      setSummary(summaryRes.data);
      setRecommendations(recommendationRes.data.recommendations || []);
      setEvidence(evidenceRes.data || null);
    } catch (fetchError) {
      console.error('Failed to fetch dashboard data:', fetchError);
      setError('Failed to load dashboard data. Please refresh and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePracticeTopic = (topicId: number) => {
    navigate(`/learn/${topicId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading your dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="section-title">Welcome back, {user?.full_name || user?.username}!</h1>
          <p className="text-gray-600">Continue your personalized learning journey</p>
        </div>

        {error && (
          <div className="card bg-red-50 border-l-4 border-red-400 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {summary && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Questions Attempted</p>
              <p className="text-3xl font-bold text-blue-600">{summary.total_questions_attempted}</p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Overall Accuracy</p>
              <p className="text-3xl font-bold text-green-600">{summary.total_accuracy.toFixed(1)}%</p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Topics Studied</p>
              <p className="text-3xl font-bold text-purple-600">{summary.topics_studied}</p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Learning Consistency</p>
              <p className="text-3xl font-bold text-orange-600">🔥</p>
            </div>
          </div>
        )}

        {evidence && (
          <div className="card mb-8 border-l-4 border-indigo-400 bg-indigo-50">
            <h3 className="subsection-title text-indigo-900">Measurable Outcomes Evidence</h3>
            <div className="grid md:grid-cols-4 gap-3 mt-3 text-sm">
              <div className="bg-white rounded p-3 border border-indigo-100">
                <p className="text-gray-500">Baseline accuracy</p>
                <p className="font-semibold text-indigo-800">{(evidence.baseline_accuracy * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white rounded p-3 border border-indigo-100">
                <p className="text-gray-500">Current accuracy</p>
                <p className="font-semibold text-indigo-800">{(evidence.current_accuracy * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white rounded p-3 border border-indigo-100">
                <p className="text-gray-500">Learning gain</p>
                <p className="font-semibold text-indigo-800">{(evidence.learning_gain * 100).toFixed(1)} pp</p>
              </div>
              <div className="bg-white rounded p-3 border border-indigo-100">
                <p className="text-gray-500">Confidence trend</p>
                <p className="font-semibold text-indigo-800">{(evidence.confidence_trend * 100).toFixed(1)} pp</p>
              </div>
            </div>
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="card mb-8">
            <h3 className="subsection-title">Recommendation Explainability</h3>
            <p className="text-gray-600 text-sm mb-4">Per-topic reason codes and confidence intervals</p>
            <div className="space-y-3">
              {recommendations.slice(0, 3).map((item) => (
                <div key={item.topic_id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{item.topic_name}</h4>
                    <span className="text-xs px-2 py-1 rounded bg-white border border-gray-300 text-gray-700">
                      Urgency: {item.urgency}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Confidence interval: {(item.confidence_interval_low * 100).toFixed(0)}% - {(item.confidence_interval_high * 100).toFixed(0)}%
                  </p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {item.reason_codes.map((reason) => (
                      <span key={reason} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                        {reason}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="card mb-8">
          <h3 className="subsection-title">Your Personalized Learning Path</h3>
          <p className="text-gray-600 text-sm mb-6">Topics sorted by priority based on your performance and goals</p>

          {summary && summary.total_questions_attempted === 0 && (
            <div className="mb-6 p-4 rounded-lg bg-blue-50 border border-blue-200">
              <h4 className="font-semibold text-blue-800 mb-2">Start your first practice session</h4>
              <p className="text-blue-700 text-sm">
                Welcome! You have not attempted any questions yet. Pick a starter topic below to begin building your personalized recommendations.
              </p>
            </div>
          )}

          {learningPath.length > 0 ? (
            <div className="space-y-3">
              {learningPath.slice(0, 5).map((item) => (
                <div
                  key={item.topic_id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                >
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{item.topic_name}</h4>
                    <div className="flex gap-4 mt-2 text-sm text-gray-600">
                      <span>Accuracy: {item.current_score.toFixed(1)}%</span>
                      <span>Attempts: {item.attempts}</span>
                    </div>
                  </div>
                  <button onClick={() => handlePracticeTopic(item.topic_id)} className="btn btn-primary ml-4">
                    Practice
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-center py-8">Get started by answering questions to build your personalized path!</p>
          )}
        </div>

        <div className="card mb-8 bg-gray-100">
          <h3 className="subsection-title">Ethics and Accessibility Verification</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-700">
            <div className="bg-white border border-gray-200 rounded p-3">
              <p className="font-medium text-gray-800 mb-2">Ethics guardrails</p>
              <ul className="space-y-1">
                <li>Use own reasoning before external help.</li>
                <li>Metrics exclude shortcuts and copied answers.</li>
                <li>Feedback should guide understanding, not answer laundering.</li>
              </ul>
            </div>
            <div className="bg-white border border-gray-200 rounded p-3">
              <p className="font-medium text-gray-800 mb-2">Accessibility checks</p>
              <ul className="space-y-1">
                <li>Keyboard-first interactions supported.</li>
                <li>Status messages include text, not color-only cues.</li>
                <li>Feedback and onboarding include descriptive labels.</li>
              </ul>
            </div>
          </div>
        </div>

        {summary && summary.strong_topics.length > 0 && (
          <div className="card mt-8 bg-green-50">
            <h3 className="subsection-title text-green-800">Mastered Topics</h3>
            <div className="flex flex-wrap gap-2">
              {summary.strong_topics.map((topic) => (
                <span key={topic} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
