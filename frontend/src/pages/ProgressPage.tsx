import React, { useEffect, useState } from 'react';
import apiClient from '@/utils/api';
import { useAuthStore } from '@/stores/store';

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

export default function ProgressPage() {
  const user = useAuthStore((state) => state.user);
  const [progress, setProgress] = useState<ProgressData[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProgressData();
  }, [user?.id]);

  const fetchProgressData = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const [progressRes, summaryRes] = await Promise.all([
        apiClient.get(`/progress/user/${user.id}`),
        apiClient.get(`/progress/summary/${user.id}`),
      ]);

      setProgress(progressRes.data.progress_records || []);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to fetch progress data:', error);
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

        {/* Overall Statistics */}
        {summary && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <p className="text-gray-600 text-sm">Total Questions</p>
              <p className="text-3xl font-bold text-blue-600">
                {summary.total_questions_attempted}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                {summary.total_accuracy.toFixed(1)}% average accuracy
              </p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm">Topics Mastered</p>
              <p className="text-3xl font-bold text-green-600">
                {summary.strong_topics.length}
              </p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm">Areas to Focus</p>
              <p className="text-3xl font-bold text-orange-600">
                {summary.weak_topics.length}
              </p>
            </div>
            <div className="card">
              <p className="text-gray-600 text-sm">Consistent Learner</p>
              <p className="text-3xl font-bold">📊</p>
            </div>
          </div>
        )}

        {/* Topics List */}
        <div className="card">
          <h3 className="subsection-title">Performance by Topic</h3>

          {progress.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      Topic
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      Attempted
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      Correct
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      Accuracy
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {progress.map((item) => (
                    <tr key={item.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">
                        Topic {item.topic_id}
                      </td>
                      <td className="text-center py-3 px-4 text-gray-600">
                        {item.questions_attempted}
                      </td>
                      <td className="text-center py-3 px-4 text-gray-600">
                        {item.questions_correct}
                      </td>
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
                              style={{
                                width: `${item.accuracy_score}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {item.accuracy_score.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="text-center py-3 px-4">
                        {item.accuracy_score >= 80 ? (
                          <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm">
                            ✓ Mastered
                          </span>
                        ) : item.accuracy_score >= 60 ? (
                          <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm">
                            → Review
                          </span>
                        ) : (
                          <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm">
                            Focus
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center py-8 text-gray-600">
              No progress data yet. Start learning to see your progress!
            </p>
          )}
        </div>

        {/* Strong Areas */}
        {summary && summary.strong_topics.length > 0 && (
          <div className="card mt-8 bg-green-50 border-l-4 border-green-400">
            <h3 className="subsection-title text-green-800">
              🌟 Topics You've Mastered
            </h3>
            <div className="flex flex-wrap gap-3">
              {summary.strong_topics.map((topic) => (
                <span
                  key={topic}
                  className="bg-green-100 text-green-800 px-4 py-2 rounded-lg font-medium"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Areas to Focus */}
        {summary && summary.weak_topics.length > 0 && (
          <div className="card mt-8 bg-orange-50 border-l-4 border-orange-400">
            <h3 className="subsection-title text-orange-800">
              📚 Topics to Focus On
            </h3>
            <p className="text-orange-700 mb-4 text-sm">
              These topics need more practice to improve your understanding:
            </p>
            <div className="flex flex-wrap gap-3">
              {summary.weak_topics.map((topic) => (
                <span
                  key={topic}
                  className="bg-orange-100 text-orange-800 px-4 py-2 rounded-lg font-medium"
                >
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
