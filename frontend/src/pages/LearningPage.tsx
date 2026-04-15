import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { useAuthStore } from '@/stores/store';
import apiClient from '@/utils/api';

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
  llm_source: string;
  llm_latency_ms: number;
  feedback_quality_score: number;
  fallback_reason?: string;
  formative_rubric: Record<string, string>;
}

interface AdaptiveHandoff {
  topic_id: number;
  topic_name: string;
  handoff_reason: string;
}

export default function LearningPage() {
  const navigate = useNavigate();
  const { topicId } = useParams();
  const user = useAuthStore((state) => state.user);

  const [question, setQuestion] = useState<Question | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [nextBestHandoff, setNextBestHandoff] = useState<AdaptiveHandoff | null>(null);
  const [loading, setLoading] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNextQuestion();
  }, [topicId, user?.id]);

  const fetchNextQuestion = async () => {
    if (!topicId || !user?.id) return;

    try {
      setLoading(true);
      setError(null);

      let nextQuestion: Question | null = null;

      try {
        const response = await apiClient.get(`/questions/adaptive/${user.id}/${topicId}`);
        nextQuestion = response.data;
      } catch {
        // Fall back to first topic question if adaptive endpoint has no match yet.
      }

      if (!nextQuestion || !nextQuestion.id) {
        const topicResponse = await apiClient.get(`/questions/topic/${topicId}`, {
          params: { limit: 1 },
        });
        nextQuestion = topicResponse.data.questions?.[0] || null;
      }

      if (nextQuestion?.id && (!nextQuestion.options || nextQuestion.options.length === 0)) {
        const fullQuestionResponse = await apiClient.get(`/questions/${nextQuestion.id}`);
        nextQuestion = fullQuestionResponse.data;
      }

      setQuestion(nextQuestion);
      setUserAnswer('');
      setFeedback(null);
      setShowFeedback(false);
      setNextBestHandoff(null);
    } catch (fetchErr) {
      console.error('Failed to fetch question:', fetchErr);
      setQuestion(null);
      setError('Unable to load a question right now. Please try another topic.');
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

      const handoffResponse = await apiClient.get(`/questions/adaptive-next/${user.id}/${topicId}`);
      if (handoffResponse.data?.topic_id) {
        setNextBestHandoff(handoffResponse.data);
      }

      await apiClient.post(`/progress/experiments/${user.id}/events`, {
        event_name: 'answer_submitted',
        session_token: `learn-${topicId}`,
        event_payload: {
          topic_id: Number(topicId),
          question_id: question.id,
          is_correct: Boolean(response.data?.is_correct),
          llm_source: response.data?.llm_source || 'fallback',
          llm_latency_ms: Number(response.data?.llm_latency_ms || 0),
          quality_score: Number(response.data?.feedback_quality_score || 0),
        },
      });
    } catch (submitError) {
      console.error('Failed to submit answer:', submitError);
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
          {error && <p className="text-red-600 mt-2 text-sm">{error}</p>}
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
            <div className="card mb-6" role="region" aria-label="Question panel">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-medium text-gray-500">Difficulty: {question?.difficulty}/5</span>
                  <span className="text-sm font-medium text-gray-500">Type: {question?.question_type}</span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">{question?.question_text}</h2>
              </div>

              {!showFeedback ? (
                <div className="space-y-3">
                  {(question?.options || []).map((option) => (
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

            <div className="card mb-6 bg-blue-50 border-l-4 border-blue-400" role="note" aria-label="Academic integrity guidance">
              <h3 className="font-semibold text-blue-900 mb-2">Ethics Guardrail</h3>
              <p className="text-blue-800 text-sm">
                Explain your reasoning before selecting answers. Avoid copy/paste or external answer bots so progress metrics remain valid and trustworthy.
              </p>
            </div>

            {showFeedback && feedback && (
              <div
                className={`card mb-6 border-l-4 ${
                  feedback.is_correct ? 'border-green-400 bg-green-50' : 'border-orange-400 bg-orange-50'
                }`}
                aria-live="polite"
              >
                <div className="flex items-start gap-4">
                  <div className="text-3xl">{feedback.is_correct ? '✅' : '❌'}</div>
                  <div className="w-full">
                    <h3 className={`font-bold ${feedback.is_correct ? 'text-green-800' : 'text-orange-800'}`}>
                      {feedback.is_correct ? 'Correct!' : 'Not quite right'}
                    </h3>
                    <p className="text-gray-700 mt-2 mb-4">{feedback.explanation}</p>

                    {feedback.llm_source !== 'ollama' && (
                      <div className="mb-4 p-3 rounded bg-yellow-50 border border-yellow-200 text-yellow-900 text-sm">
                        Fallback feedback mode: deterministic guidance is active.
                        {feedback.fallback_reason ? ` Reason: ${feedback.fallback_reason}` : ''}
                      </div>
                    )}

                    {feedback.key_concepts.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Key Concepts:</p>
                        <div className="flex flex-wrap gap-2">
                          {feedback.key_concepts.map((concept, idx) => (
                            <span key={idx} className="bg-white text-gray-700 px-3 py-1 rounded text-sm">
                              {concept}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mb-4 p-3 rounded bg-white border border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-2">Formative Rubric</p>
                      <p className="text-sm text-gray-700">
                        Error class: <span className="font-medium">{feedback.formative_rubric?.conceptual_error_class || 'none'}</span>
                      </p>
                      <p className="text-sm text-gray-700">
                        Misconception tag: <span className="font-medium">{feedback.formative_rubric?.misconception_tag || 'none'}</span>
                      </p>
                      <p className="text-sm text-gray-700">
                        Next remediation step:{' '}
                        <span className="font-medium">{feedback.formative_rubric?.remediation_step || 'Continue targeted practice.'}</span>
                      </p>
                    </div>

                    <div className="text-xs text-gray-600 bg-white border border-gray-200 rounded p-3">
                      <div>Feedback source: {feedback.llm_source}</div>
                      <div>Model latency: {feedback.llm_latency_ms} ms</div>
                      <div>Feedback quality score: {(feedback.feedback_quality_score * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {showFeedback && nextBestHandoff && (
              <div className="card mb-6 bg-indigo-50 border-l-4 border-indigo-400" role="region" aria-label="Adaptive handoff recommendation">
                <h3 className="font-semibold text-indigo-900">Adaptive next-best handoff</h3>
                <p className="text-indigo-800 text-sm mt-2">
                  Move to <span className="font-semibold">{nextBestHandoff.topic_name}</span> for your strongest expected gain.
                </p>
                <button onClick={() => navigate(`/learn/${nextBestHandoff.topic_id}`)} className="btn btn-secondary mt-3">
                  Switch to next-best topic
                </button>
              </div>
            )}

            <div className="card mb-6 bg-gray-100" role="status" aria-label="Accessibility verification">
              <h3 className="font-semibold text-gray-900 mb-2">Accessibility verification</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>Keyboard-selectable options are available via native radio controls.</li>
                <li>Feedback updates announce through an aria-live region.</li>
                <li>Color-coded statuses include text labels for non-color interpretation.</li>
              </ul>
            </div>

            <div className="flex gap-4">
              {!showFeedback ? (
                <button onClick={handleSubmitAnswer} disabled={!userAnswer || loading} className="btn btn-primary flex-1">
                  {loading ? 'Checking...' : 'Submit Answer'}
                </button>
              ) : (
                <button onClick={handleNextQuestion} disabled={loading} className="btn btn-primary flex-1">
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
