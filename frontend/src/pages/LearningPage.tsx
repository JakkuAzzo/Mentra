import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '@/utils/api';
import { useAuthStore } from '@/stores/store';

interface Question {
  id: number;
  question_text: string;
  question_type: string;
  difficulty: number;
  options: Array<{
    id: number;
    option_text: string;
    order: number;
  }>;
}

interface Feedback {
  is_correct: boolean;
  explanation: string;
  key_concepts: string[];
  confidence_score: number;
}

export default function LearningPage() {
  const { topicId } = useParams();
  const user = useAuthStore((state) => state.user);
  const [question, setQuestion] = useState<Question | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [loading, setLoading] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    fetchNextQuestion();
  }, [topicId, user?.id]);

  const fetchNextQuestion = async () => {
    if (!topicId || !user?.id) return;

    try {
      setLoading(true);
      const response = await apiClient.get(
        `/questions/adaptive/${user.id}/${topicId}`
      );
      setQuestion(response.data);
      setUserAnswer('');
      setFeedback(null);
      setShowFeedback(false);
    } catch (error) {
      console.error('Failed to fetch question:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!question || !user?.id || !userAnswer) return;

    try {
      setLoading(true);
      const response = await apiClient.post(
        '/questions/submit-answer',
        {
          question_id: question.id,
          user_answer: userAnswer,
          time_spent: 0,
        },
        {
          params: { user_id: user.id },
        }
      );

      setFeedback(response.data);
      setShowFeedback(true);
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = () => {
    fetchNextQuestion();
  };

  if (!question && !loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">📖</div>
          <p className="text-gray-600">No questions found for this topic</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        {loading && !question ? (
          <div className="card">
            <p className="text-center text-gray-600">Loading question...</p>
          </div>
        ) : (
          <>
            {/* Question Card */}
            <div className="card mb-6">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-medium text-gray-500">
                    Difficulty: {question?.difficulty}/5
                  </span>
                  <span className="text-sm font-medium text-gray-500">
                    Type: {question?.question_type}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {question?.question_text}
                </h2>
              </div>

              {!showFeedback ? (
                // Question Options
                <div className="space-y-3">
                  {question?.options.map((option) => (
                    <label
                      key={option.id}
                      className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-blue-50 cursor-pointer transition"
                    >
                      <input
                        type="radio"
                        name="answer"
                        value={option.id}
                        checked={userAnswer === String(option.id)}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        className="w-4 h-4 text-blue-600"
                      />
                      <span className="ml-3 text-gray-900">{option.option_text}</span>
                    </label>
                  ))}
                </div>
              ) : null}
            </div>

            {/* Feedback Section */}
            {showFeedback && feedback && (
              <div
                className={`card mb-6 border-l-4 ${
                  feedback.is_correct
                    ? 'border-green-400 bg-green-50'
                    : 'border-orange-400 bg-orange-50'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="text-3xl">
                    {feedback.is_correct ? '✅' : '❌'}
                  </div>
                  <div>
                    <h3
                      className={`font-bold ${
                        feedback.is_correct ? 'text-green-800' : 'text-orange-800'
                      }`}
                    >
                      {feedback.is_correct ? 'Correct!' : 'Not quite right'}
                    </h3>
                    <p className="text-gray-700 mt-2 mb-4">
                      {feedback.explanation}
                    </p>
                    {feedback.key_concepts.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">
                          Key Concepts:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {feedback.key_concepts.map((concept, idx) => (
                            <span
                              key={idx}
                              className="bg-white text-gray-700 px-3 py-1 rounded text-sm"
                            >
                              {concept}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              {!showFeedback ? (
                <button
                  onClick={handleSubmitAnswer}
                  disabled={!userAnswer || loading}
                  className="btn btn-primary flex-1"
                >
                  {loading ? 'Checking...' : 'Submit Answer'}
                </button>
              ) : (
                <button
                  onClick={handleNextQuestion}
                  disabled={loading}
                  className="btn btn-primary flex-1"
                >
                  Next Question →
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
