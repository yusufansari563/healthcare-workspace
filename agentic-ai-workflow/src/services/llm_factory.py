import logging
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from src.config import settings

logger = logging.getLogger(__name__)

def get_llm(temperature: float = 0.2) -> BaseChatModel:
    """
    Factory method to instantiate a Chat Model according to configuration.
    Supports Ollama, OpenAI, Groq, OpenRouter, and graceful mock fallback.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        try:
            from langchain_openai import ChatOpenAI
            logger.info(f"Initializing Ollama LLM model '{settings.OLLAMA_MODEL}' via {settings.OLLAMA_BASE_URL}...")
            return ChatOpenAI(
                base_url=f"{settings.OLLAMA_BASE_URL.rstrip('/')}/v1",
                api_key="ollama",
                model=settings.OLLAMA_MODEL,
                temperature=temperature
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatOpenAI wrapper for Ollama: {e}")

    elif provider == "openai":
        if settings.OPENAI_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o-mini",
                temperature=temperature
            )
        else:
            logger.warning("LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set.")

    elif provider == "groq":
        if settings.GROQ_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.GROQ_API_KEY,
                model="llama-3.1-8b-instant",
                temperature=temperature
            )

    elif provider == "openrouter":
        if settings.OPENROUTER_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                model="meta-llama/llama-3.2-3b-instruct",
                temperature=temperature
            )

    # Fallback / Mock LLM wrapper when no live endpoint is available
    logger.info("Using Fallback / Mock LLM runner for agent execution.")
    return MockLLM()


class MockLLM(BaseChatModel):
    """
    Lightweight Mock LLM for local testing without external API keys or Ollama instance.
    Generates intelligent structured answers based on user inputs.
    """
    
    @property
    def _llm_type(self) -> str:
        return "mock_llm"

    def _generate(self, messages: Any, stop: Any = None, run_manager: Any = None, **kwargs: Any) -> Any:
        from langchain_core.outputs import ChatResult, ChatGeneration
        from langchain_core.messages import AIMessage

        last_msg = messages[-1].content if messages else ""
        
        if "plan" in last_msg.lower() or "planner" in last_msg.lower() or "step" in last_msg.lower():
            response_content = """```json
[
  {
    "task_id": 1,
    "title": "Analyze and setup project architecture",
    "description": "Examine current codebase structure, configure dependencies and environment requirements.",
    "action": "setup_config"
  },
  {
    "task_id": 2,
    "title": "Implement core logic changes and middleware",
    "description": "Build requested features and business logic according to target specification.",
    "action": "implement_feature"
  },
  {
    "task_id": 3,
    "title": "Add test suites and documentation updates",
    "description": "Write automated unit tests and update README instruction guides.",
    "action": "test_and_document"
  }
]
```"""
        else:
            response_content = f"Mock LLM Processed: '{last_msg[:100]}...' Successfully generated task execution results and patch diff."

        ai_msg = AIMessage(content=response_content)
        return ChatResult(generations=[ChatGeneration(message=ai_msg)])
