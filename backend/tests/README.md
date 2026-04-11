# Mentra Backend Test Suite

Comprehensive test suite for the Mentra AI-driven personal tutor backend.

## Quick Start

### Prerequisites
```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/test_llm_service.py -v

# Spaced repetition tests
pytest tests/test_spaced_repetition.py -v

# API endpoint tests
pytest tests/test_api_endpoints.py -v

# Excluding slow tests
pytest -m "not slow"

# Only LLM service tests
pytest -m llm
```

## Test Organization

### `conftest.py`
Shared fixtures and test database setup:
- `db_session`: In-memory SQLite database for each test
- `sample_user`: Pre-created test user
- `sample_subject`, `sample_topics`: Test subject/topic hierarchy
- `sample_questions`: Pre-generated questions with options
- `sample_user_progress`: User progress records
- `sample_user_answers`: Sample answer history
- `sample_user_sessions`: Learning session data

### `test_llm_service.py`
Tests for AI-powered feedback and question generation:
- **Feedback Generation**: Correct/incorrect answer handling, LLM integration
- **Fallback Behavior**: Graceful degradation when LLM unavailable
- **Prompt Building**: Proper prompt structure and JSON formatting
- **Response Parsing**: Handling valid/invalid LLM outputs
- **Performance Prediction**: Trend analysis and forecasting
- **Question Generation**: Adaptive difficulty adjustment

### `test_spaced_repetition.py`
Tests for optimal review scheduling (Ebbinghaus algorithm):
- **Review Dates**: Interval calculation based on accuracy, difficulty
- **Due Topics**: Prioritization based on forgetting curve
- **Mastery Estimation**: Days-to-mastery prediction with confidence
- **Priority Scoring**: Multi-factor review urgency calculation
- **Session Analytics**: Streak tracking, consistency scoring, peak hours
- **Ebbinghaus Validation**: Algorithm correctness (7-day intervals: [1, 3, 7, 14, 30, 60, 120])

### `test_feedback_service.py`
Tests for LLM-integrated feedback service:
- **Async Integration**: LLMService integration via async/await
- **Confidence Tracking**: Storing confidence levels with answers
- **Time Analysis**: Average time per topic calculation
- **Confidence Distribution**: Categorizing user confidence (low/medium/high)
- **Quality Assurance**: Feedback format and content validation

### `test_api_endpoints.py`
Integration tests for REST API endpoints:
- **Question Endpoints**: Getting questions, adaptive selection, answer submission
- **Recommendation Endpoints**: Due-for-review, mastery prediction, session stats
- **Authentication**: Endpoint security and auth requirements
- **Error Handling**: 404s, invalid IDs, missing data
- **Feature Flags**: Disabled feature behavior (503 Service Unavailable)
- **Response Schemas**: Proper format and field validation

## Test Fixtures

### User & Content Fixtures
```python
@pytest.fixture
def sample_user(db_session):
    """Single test user with credentials"""
    
@pytest.fixture
def sample_topics(db_session, sample_subject):
    """3 topics: Algebra (2), Geometry (3), Calculus (4) difficulty"""
    
@pytest.fixture
def sample_questions(db_session, sample_topics):
    """5 questions per topic with multiple choice options"""
```

### Progress & History Fixtures
```python
@pytest.fixture
def sample_user_progress(db_session, sample_user, sample_topics):
    """Progress records: 10 attempts, 7 correct (70% accuracy)"""
    
@pytest.fixture
def sample_user_answers(db_session, sample_user, sample_questions):
    """10 answers: 2/3 correct rate, confidence levels, time tracking"""
    
@pytest.fixture
def sample_user_sessions(db_session, sample_user):
    """7 learning sessions over 7 days, 1 hour each"""
```

## Test Patterns

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await LLMService.generate_feedback(...)
    assert result is not None
```

### Mocking External Services
```python
with patch.object(LLMService, '_generate_ollama_feedback', new_callable=AsyncMock) as mock_ollama:
    mock_ollama.return_value = {"explanation": "..."}
    feedback = await LLMService.generate_feedback(...)
    mock_ollama.assert_called_once()
```

### Database Assertions
```python
def test_with_database(db_session, sample_user):
    progress = SpacedRepetitionService.get_topics_due_for_review(
        db_session, 
        sample_user.id
    )
    assert len(progress) > 0
```

## Coverage Goals

### Target Coverage by Component
- **LLMService**: 85%+ (critical for AI integration)
- **SpacedRepetitionService**: 90%+ (core algorithm)
- **SessionAnalyticsService**: 85%+ (engagement tracking)
- **FeedbackService**: 80%+ (user feedback)
- **API Endpoints**: 75%+ (integration tests)
- **Overall**: 80%+ target

### Coverage Report
```bash
# Generate and view coverage
pytest --cov=app --cov-report=html --cov-report=term-missing
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
- name: Run tests
  run: pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

### Pre-commit Hook
```bash
# Run before committing
pytest && black . && flake8 .
```

## Known Limitations

1. **LLM Service Mocking**: Uses mocked Ollama responses (real integration tested manually)
2. **Database**: Uses in-memory SQLite (different from production PostgreSQL)
3. **Async Tests**: Require `pytest-asyncio` with `asyncio_mode = auto`
4. **Session Model**: Tests use mocked UserSession (requires migration in production DB)

## Debugging Tests

### Verbose Output
```bash
pytest -vv -s   # -s prints stdout from tests
```

### Run Single Test
```bash
pytest tests/test_llm_service.py::TestLLMServiceFeedbackGeneration::test_generate_feedback_with_correct_answer -v
```

### Drop into Debugger
```python
pytest.set_trace()  # or pdb.set_trace()
```

### Show Local Variables on Failure
```bash
pytest -l   # --showlocals
```

## Adding New Tests

1. Create test file: `tests/test_new_feature.py`
2. Import fixtures from `conftest.py`
3. Write test functions starting with `test_`
4. Use descriptive names: `test_service_action_condition_result()`
5. Mark if async: `@pytest.mark.asyncio`
6. Run: `pytest tests/test_new_feature.py -v`

## Performance Testing

For slow operations, mark with `@pytest.mark.slow`:
```python
@pytest.mark.slow
def test_large_dataset_performance():
    # Test with 10,000 records
    pass
```

Run without slow tests:
```bash
pytest -m "not slow"
```

## Documentation

- **Test Docstrings**: Explain what is tested and why
- **Fixture Docstrings**: Describe what data is created
- **Comments**: For non-obvious test logic

Example:
```python
def test_priority_score_factors(self):
    """
    Test priority score calculation considers:
    - Accuracy (50% weight): lower accuracy = higher priority
    - Days overdue (30% weight): longer = more urgent
    - Difficulty (20% weight): harder topics prioritized
    
    Verifies that weak, overdue, difficult topics surface first
    """
    # Test implementation...
```

## Troubleshooting

### `ModuleNotFoundError: sqlalchemy`
```bash
pip install -r requirements.txt
```

### `AsyncioDeprecationWarning` in async tests
Update pytest.ini: `asyncio_mode = auto`

### `Session` fixture issues
Ensure `conftest.py` is in tests directory with proper imports

### LLM test failures
LLM tests use mocks; they won't call real Ollama. For integration:
```bash
# Run with real Ollama running
pytest -m "not mock" --integration
```

## Next Steps

1. **Run test suite**: `pytest --cov=app --cov-report=html`
2. **Fix failing tests**: Review error messages and adjust
3. **Add frontend tests**: Update frontend React components to match new endpoints
4. **Deploy to staging**: Verify tests pass in CI/CD before production
5. **Monitor in production**: Track LLM quality and learning outcomes
