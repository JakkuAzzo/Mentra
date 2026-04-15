"""
Local LLM Service for generating intelligent feedback and explanations.
Supports Ollama for locally-hosted models without external API dependencies.
"""

import httpx
import json
from typing import Optional
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with local LLM (Ollama)"""
    
    @staticmethod
    async def generate_feedback(
        question_text: str,
        user_answer: str,
        correct_answer: Optional[str] = None,
        is_correct: bool = False
    ) -> dict:
        """
        Generate intelligent, step-by-step feedback using local LLM.
        
        Args:
            question_text: The original question
            user_answer: The user's provided answer
            correct_answer: The correct answer (if multiple choice)
            is_correct: Whether the answer was correct
            
        Returns:
            dict with explanation, key_concepts, and recommendations
        """
        started = time.perf_counter()
        try:
            if settings.LLM_PROVIDER == "ollama":
                result = await LLMService._generate_ollama_feedback(
                    question_text, user_answer, correct_answer, is_correct
                )
            elif settings.LLM_PROVIDER == "openai":
                result = await LLMService._generate_openai_feedback(
                    question_text, user_answer, correct_answer, is_correct
                )
            else:
                result = LLMService._generate_fallback_feedback(
                    question_text, user_answer, is_correct
                )
            result["llm_latency_ms"] = int((time.perf_counter() - started) * 1000)
            result["feedback_quality_score"] = LLMService._quality_score(result)
            return result
        except Exception as e:
            logger.error(f"LLM feedback generation failed: {e}")
            fallback = LLMService._generate_fallback_feedback(
                question_text, user_answer, is_correct
            )
            fallback["fallback_reason"] = str(e)
            fallback["llm_latency_ms"] = int((time.perf_counter() - started) * 1000)
            fallback["feedback_quality_score"] = LLMService._quality_score(fallback)
            return fallback
    
    @staticmethod
    async def _generate_ollama_feedback(
        question_text: str,
        user_answer: str,
        correct_answer: Optional[str] = None,
        is_correct: bool = False
    ) -> dict:
        """Generate feedback using Ollama local LLM"""
        
        prompt = LLMService._build_feedback_prompt(
            question_text, user_answer, correct_answer, is_correct
        )
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": settings.LLM_TEMPERATURE,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    feedback_text = result.get("response", "")
                    return LLMService._parse_feedback_response(feedback_text)
                else:
                    logger.warning(f"Ollama returned status {response.status_code}")
                    return LLMService._generate_fallback_feedback(
                        question_text, user_answer, is_correct
                    )
        except httpx.ConnectError:
            logger.error("Could not connect to Ollama service")
            fallback = LLMService._generate_fallback_feedback(
                question_text, user_answer, is_correct
            )
            fallback["fallback_reason"] = "ollama_unreachable"
            return fallback
    
    @staticmethod
    async def _generate_openai_feedback(
        question_text: str,
        user_answer: str,
        correct_answer: Optional[str] = None,
        is_correct: bool = False
    ) -> dict:
        """Generate feedback using OpenAI API (fallback)"""
        # Placeholder for OpenAI integration
        return LLMService._generate_fallback_feedback(
            question_text, user_answer, is_correct
        )
    
    @staticmethod
    def _build_feedback_prompt(
        question_text: str,
        user_answer: str,
        correct_answer: Optional[str] = None,
        is_correct: bool = False
    ) -> str:
        """Build the prompt for feedback generation"""
        
        status = "CORRECT" if is_correct else "INCORRECT"
        
        prompt = f"""
You are an expert educational tutor. Provide clear, helpful feedback for a student answering an exam question.

QUESTION: {question_text}
STUDENT'S ANSWER: {user_answer}
STATUS: {status}
"""
        if correct_answer:
            prompt += f"CORRECT ANSWER: {correct_answer}\n"
        
        prompt += """
Generate feedback that:
1. Is encouraging but honest
2. Explains WHY the answer is right or wrong
3. Breaks down the concept step-by-step
4. Identifies key concepts involved
5. Suggests what to study next if wrong

Format your response as JSON with these fields:
{{
    "explanation": "detailed step-by-step explanation",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "confidence_score": 0.85,
    "next_step": "recommendation for what to study",
    "effort_level": "easy/medium/hard"
}}

Respond ONLY with valid JSON, no other text."""
        
        return prompt
    
    @staticmethod
    def _parse_feedback_response(response_text: str) -> dict:
        """Parse LLM response into structured feedback"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                feedback = json.loads(json_str)
                
                return {
                    "explanation": feedback.get("explanation", "Good attempt!"),
                    "key_concepts": feedback.get("key_concepts", []),
                    "confidence_score": feedback.get("confidence_score", 0.8),
                    "next_step": feedback.get("next_step", "Continue practicing"),
                    "effort_level": feedback.get("effort_level", "medium"),
                    "llm_source": "ollama",
                    "fallback_reason": None,
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response")
        
        fallback = LLMService._generate_fallback_feedback("", "", False)
        fallback["fallback_reason"] = "json_parse_error"
        return fallback
    
    @staticmethod
    def _generate_fallback_feedback(
        question_text: str,
        user_answer: str,
        is_correct: bool
    ) -> dict:
        """Generate basic feedback when LLM unavailable"""
        
        if is_correct:
            explanation = "Excellent! Your answer is correct. Keep up the good work!"
            confidence_score = 0.95
        else:
            explanation = f"Your answer needs review. Let's think through this step-by-step. The question asked: {question_text}. Your approach was: {user_answer}. Let me guide you to the correct thinking process..."
            confidence_score = 0.7
        
        return {
            "explanation": explanation,
            "key_concepts": ["Concept1", "Concept2", "Concept3"],
            "confidence_score": confidence_score,
            "next_step": "Review key concepts and try similar questions",
            "effort_level": "medium",
            "llm_source": "fallback",
            "fallback_reason": "deterministic_rule_engine",
        }

    @staticmethod
    def _quality_score(feedback: dict) -> float:
        explanation = feedback.get("explanation", "") or ""
        concepts = feedback.get("key_concepts", []) or []
        concept_score = min(1.0, len(concepts) / 3)
        explanation_score = min(1.0, len(explanation) / 180)
        return round((concept_score * 0.4) + (explanation_score * 0.6), 2)
    
    @staticmethod
    async def generate_question(
        topic: str,
        difficulty: int,
        user_weakness_areas: Optional[list] = None
    ) -> dict:
        """
        Generate an adaptive question for a topic.
        Can focus on weakness areas.
        """
        prompt = f"""
Generate a challenging but fair exam question for {topic} at difficulty level {difficulty}/5.
"""
        if user_weakness_areas:
            prompt += f"Focus on these areas: {', '.join(user_weakness_areas)}\n"
        
        prompt += """
Format as JSON:
{{
    "question_text": "the question",
    "question_type": "multiple_choice|short_answer",
    "options": ["option1", "option2", "option3", "option4"],
    "correct_answer": "the correct option or answer",
    "explanation": "why this is correct"
}}
"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    # Parse JSON from response
                    try:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        if json_start != -1:
                            question_data = json.loads(response_text[json_start:json_end])
                            return question_data
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
        
        # Fallback question
        return {
            "question_text": f"What is a key concept in {topic}?",
            "question_type": "multiple_choice",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "This is the correct answer because..."
        }
    
    @staticmethod
    async def predict_performance(
        user_id: int,
        topic_id: int,
        recent_accuracy: float,
        attempts_count: int
    ) -> dict:
        """
        Predict user's future performance on a topic based on recent history.
        Returns confidence level and predicted accuracy.
        """
        prompt = f"""
Based on a student's learning pattern:
- Recent accuracy: {recent_accuracy}%
- Attempts so far: {attempts_count}
- Trend: {('improving' if recent_accuracy > 70 else 'needs work')}

Predict their performance and provide learning recommendations.
Response format:
{{
    "predicted_accuracy": 0.85,
    "confidence": "high/medium/low",
    "time_to_mastery_days": 7,
    "recommended_actions": ["action1", "action2"]
}}
"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    try:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        if json_start != -1:
                            prediction = json.loads(response_text[json_start:json_end])
                            return prediction
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Performance prediction failed: {e}")
        
        # Fallback prediction
        return {
            "predicted_accuracy": min(100, recent_accuracy + 10),
            "confidence": "medium",
            "time_to_mastery_days": max(1, 14 - (attempts_count // 5)),
            "recommended_actions": [
                "Continue practicing",
                "Review weak concepts",
                "Take practice tests"
            ]
        }
