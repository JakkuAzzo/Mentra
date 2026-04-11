import React, { useEffect, useState } from 'react';
import apiClient from '@/utils/api';
import { useAuthStore } from '@/stores/store';

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

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const [learningPath, setLearningPath] = useState<LearningPath[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [user?.id]);

  const fetchDashboardData = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const [pathRes, summaryRes] = await Promise.all([
        apiClient.get(`/recommendations/learning-path/${user.id}`),
        apiClient.get(`/progress/summary/${user.id}`),
      ]);

      setLearningPath(pathRes.data.path || []);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
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
        {/* Header */}
        <div className="mb-8">
          <h1 className="section-title">Welcome back, {user?.full_name || user?.username}!</h1>
          <p className="text-gray-600">Continue your personalized learning journey</p>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Questions Attempted</p>
              <p className="text-3xl font-bold text-blue-600">
                {summary.total_questions_attempted}
              </p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Overall Accuracy</p>
              <p className="text-3xl font-bold text-green-600">
                {summary.total_accuracy.toFixed(1)}%
              </p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Topics Studied</p>
              <p className="text-3xl font-bold text-purple-600">
                {summary.topics_studied}
              </p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm font-medium">Learning Consistency</p>
              <p className="text-3xl font-bold text-orange-600">🔥</p>
            </div>
          </div>
        )}

        {/* Weak Topics Alert */}
        {summary && summary.weak_topics.length > 0 && (
          <div className="card bg-orange-50 border-l-4 border-orange-400 mb-8">
            <h3 className="subsection-title text-orange-800">
              Areas for Improvement
            </h3>
            <p className="text-orange-700 mb-3">
              These topics need your attention based on your recent performance:
            </p>
            <div className="flex flex-wrap gap-2">
              {summary.weak_topics.map((topic) => (
                <span
                  key={topic}
                  className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Learning Path */}
        <div className="card">
          <h3 className="subsection-title">Your Personalized Learning Path</h3>
          <p className="text-gray-600 text-sm mb-6">
            Topics sorted by priority based on your performance and learning goals
          </p>

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
                  <button className="btn btn-primary ml-4">
                    Practice
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-center py-8">
              Get started by answering questions to build your personalized path!
            </p>
          )}
        </div>

        {/* Strong Topics */}
        {summary && summary.strong_topics.length > 0 && (
          <div className="card mt-8 bg-green-50">
            <h3 className="subsection-title text-green-800">🎉 Mastered Topics</h3>
            <div className="flex flex-wrap gap-2">
              {summary.strong_topics.map((topic) => (
                <span
                  key={topic}
                  className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                >
                  ✓ {topic}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
