"""
Tests for LLMService - AI-powered feedback generation and question creation.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.llm_service import LLMService
from datetime import datetime

class TestLLMServiceFeedbackGeneration:
    """Test feedback generation with LLM integration"""
    
    @pytest.mark.asyncio
    async def test_generate_feedback_with_correct_answer(self):
        """Test feedback generation for correct answers"""
        db = MagicMock()
        question = MagicMock()
        question.question_text = "What is 2 + 2?"
        question.explanation = "The answer is 4"
        question.topic.name = "Arithmetic"
        
        with patch.object(LLMService, '_generate_ollama_feedback', new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = {
                "explanation": "Great! You correctly identified that 2 + 2 = 4.",
                "steps": ["Start with 2", "Add 2", "Result is 4"],
                "next_topic": "Multiplication"
            }
            
            feedback = await LLMService.generate_feedback(
                db=db,
                question=question,
                user_answer="4",
                is_correct=True
            )
            
            assert feedback['is_correct'] is True
            assert 'explanation' in feedback
            mock_ollama.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_feedback_with_wrong_answer(self):
        """Test feedback generation for incorrect answers"""
        db = MagicMock()
        question = MagicMock()
        question.question_text = "What is 5 * 6?"
        question.explanation = "The answer is 30"
        question.topic.name = "Multiplication"
        
        with patch.object(LLMService, '_generate_ollama_feedback', new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = {
                "explanation": "Not quite. Let's break this down: 5 × 6 = 30",
                "steps": ["Count by fives six times", "5, 10, 15, 20, 25, 30"],
                "common_mistake": "You may have added instead of multiplied",
                "hint": "Try counting by fives"
            }
            
            feedback = await LLMService.generate_feedback(
                db=db,
                question=question,
                user_answer="11",
                is_correct=False
            )
            
            assert feedback['is_correct'] is False
            assert 'explanation' in feedback
            mock_ollama.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_feedback_fallback_on_llm_failure(self):
        """Test fallback behavior when LLM is unavailable"""
        db = MagicMock()
        question = MagicMock()
        question.question_text = "Test question"
        question.explanation = "Test explanation"
        question.topic.name = "Test Topic"
        
        with patch.object(LLMService, '_generate_ollama_feedback', new_callable=AsyncMock) as mock_ollama:
            mock_ollama.side_effect = Exception("Ollama connection failed")
            
            feedback = await LLMService.generate_feedback(
                db=db,
                question=question,
                user_answer="answer",
                is_correct=False
            )
            
            # Should still return feedback (fallback)
            assert 'explanation' in feedback
            assert 'effort_level' in feedback

class TestLLMServicePromptBuilding:
    """Test prompt construction for LLM"""
    
    def test_build_feedback_prompt_structure(self):
        """Test that feedback prompts are properly structured"""
        question = MagicMock()
        question.question_text = "What is 2 + 2?"
        question.explanation = "Basic arithmetic"
        question.topic.name = "Arithmetic"
        
        prompt = LLMService._build_feedback_prompt(
            question=question,
            user_answer="4",
            correct_answer="4",
            is_correct=True
        )
        
        assert "question" in prompt.lower() or "what is" in prompt.lower()
        assert "json" in prompt.lower() or "{" in prompt
        assert isinstance(prompt, str)
    
    def test_build_question_prompt_includes_topic(self):
        """Test that question prompts include topic context"""
        prompt = LLMService._build_question_prompt(
            topic_name="Algebra",
            difficulty=3,
            weakness_areas=["Solving for x"]
        )
        
        assert "Algebra" in prompt
        assert "difficulty" in prompt.lower() or "3" in prompt or "medium" in prompt.lower()
        assert "Solving for x" in prompt

class TestLLMServiceResponseParsing:
    """Test parsing LLM responses"""
    
    def test_parse_feedback_response_valid_json(self):
        """Test parsing valid JSON responses from LLM"""
        response = """
        {
            "explanation": "This is correct",
            "steps": ["Step 1", "Step 2"],
            "confidence": 0.95
        }
        """
        
        parsed = LLMService._parse_feedback_response(response)
        
        assert parsed['explanation'] == "This is correct"
        assert len(parsed['steps']) == 2
        assert parsed['confidence'] == 0.95
    
    def test_parse_feedback_response_with_extra_text(self):
        """Test parsing JSON embedded in extra text"""
        response = """
        Here's my analysis:
        
        {
            "explanation": "The answer is correct",
            "confidence": 0.9
        }
        
        That's my final answer.
        """
        
        parsed = LLMService._parse_feedback_response(response)
        
        assert parsed['explanation'] == "The answer is correct"
        assert parsed['confidence'] == 0.9
    
    def test_parse_feedback_response_invalid_json(self):
        """Test handling of invalid JSON responses"""
        response = "This is not JSON {invalid json}"
        
        parsed = LLMService._parse_feedback_response(response)
        
        # Should have default structure or error handling
        assert isinstance(parsed, dict)

class TestLLMServicePerformancePrediction:
    """Test performance prediction"""
    
    @pytest.mark.asyncio
    async def test_predict_performance_improvement_trend(self):
        """Test predicting performance with improvement trend"""
        db = MagicMock()
        
        # Mock user answers showing improvement
        mock_answers = [
            MagicMock(is_correct=False, created_at=datetime(2024, 1, 1)),
            MagicMock(is_correct=False, created_at=datetime(2024, 1, 2)),
            MagicMock(is_correct=True, created_at=datetime(2024, 1, 3)),
            MagicMock(is_correct=True, created_at=datetime(2024, 1, 4)),
            MagicMock(is_correct=True, created_at=datetime(2024, 1, 5)),
        ]
        
        prediction = await LLMService.predict_performance(
            recent_answers=mock_answers,
            topic_difficulty=2
        )
        
        assert 'predicted_accuracy' in prediction
        assert 'improvement_trend' in prediction
        assert prediction['improvement_trend'] == 'improving'
    
    @pytest.mark.asyncio
    async def test_predict_performance_declining_trend(self):
        """Test predicting performance with declining trend"""
        db = MagicMock()
        
        # Mock user answers showing decline
        mock_answers = [
            MagicMock(is_correct=True, created_at=datetime(2024, 1, 1)),
            MagicMock(is_correct=True, created_at=datetime(2024, 1, 2)),
            MagicMock(is_correct=False, created_at=datetime(2024, 1, 3)),
            MagicMock(is_correct=False, created_at=datetime(2024, 1, 4)),
            MagicMock(is_correct=False, created_at=datetime(2024, 1, 5)),
        ]
        
        prediction = await LLMService.predict_performance(
            recent_answers=mock_answers,
            topic_difficulty=3
        )
        
        assert prediction['improvement_trend'] in ['declining', 'stable']

class TestLLMServiceQuestionGeneration:
    """Test adaptive question generation"""
    
    @pytest.mark.asyncio
    async def test_generate_question_at_appropriate_difficulty(self):
        """Test question generation at appropriate difficulty level"""
        question = await LLMService.generate_question(
            topic_name="Algebra",
            difficulty=3,
            weakness_areas=["Solving quadratic equations"]
        )
        
        assert isinstance(question, dict)
        assert 'question_text' in question
        assert 'options' in question or 'answer_type' in question
        assert 'Algebra' in question.get('question_text', '')
