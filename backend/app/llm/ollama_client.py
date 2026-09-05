import time
import logging
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger("healthcare_chatbot.llm.ollama")


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""

    pass


class OllamaConnectionError(OllamaClientError):
    """Raised when Ollama server is unreachable."""

    pass


class OllamaModelNotFoundError(OllamaClientError):
    """Raised when requested model is not pulled in Ollama."""

    pass


class OllamaTimeoutError(OllamaClientError):
    """Raised when Ollama inference times out."""

    pass


class OllamaClient:
    """Service client for local Ollama HTTP API."""

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model: str = settings.OLLAMA_MODEL,
        timeout_sec: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_sec = timeout_sec

    def check_health(self) -> Dict[str, Any]:
        """Verifies connection to Ollama server and checks model availability."""
        try:
            url = f"{self.base_url}/api/tags"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                if response.status_code != 200:
                    raise OllamaConnectionError(
                        f"Ollama server returned HTTP {response.status_code}"
                    )

                data = response.json()
                models = [
                    m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)
                ]

                # Match model name (e.g., qwen3:8b or qwen3:8b-latest)
                model_found = any(
                    self.model in m or m in self.model for m in models
                )
                if not model_found:
                    raise OllamaModelNotFoundError(
                        f"Model '{self.model}' not found in Ollama. Available: {models}"
                    )

                return {"status": "healthy", "available_models": models}

        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {str(e)}")
            raise OllamaConnectionError(
                f"Ollama service is unreachable at {self.base_url}"
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout checking Ollama health: {str(e)}")
            raise OllamaTimeoutError("Ollama health check timed out") from e

    def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sends a chat generation request to Ollama using /api/chat.

        Args:
            prompt: User prompt or formatted context prompt.
            system_prompt: System instruction prompt.

        Returns:
            Dictionary containing generated text and latency metadata.
        """
        url = f"{self.base_url}/api/chat"
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for deterministic grounded facts
                "top_p": 0.9,
                "num_predict": 350,  # Cap output tokens for prompt response speed
            },
        }

        start_time = time.time()
        logger.info(
            f"Sending chat request to Ollama model '{self.model}' (messages={len(messages)})"
        )

        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                response = client.post(url, json=payload)

                if response.status_code == 404:
                    raise OllamaModelNotFoundError(
                        f"Model '{self.model}' not loaded in Ollama."
                    )
                elif response.status_code != 200:
                    raise OllamaClientError(
                        f"Ollama returned HTTP error {response.status_code}: {response.text}"
                    )

                result = response.json()
                latency = round(time.time() - start_time, 3)

                message_obj = result.get("message", {})
                answer = message_obj.get("content", "").strip() if isinstance(message_obj, dict) else ""

                logger.info(
                    f"Received response from Ollama in {latency}s (tokens={result.get('eval_count', 'N/A')})"
                )

                return {
                    "response": answer,
                    "latency_sec": latency,
                    "model": self.model,
                    "eval_count": result.get("eval_count"),
                }

        except httpx.ConnectError as e:
            logger.error(f"Ollama connection error during generate: {str(e)}")
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self.base_url}"
            ) from e
        except httpx.TimeoutException as e:
            logger.error(
                f"Ollama generate request timed out (> {self.timeout_sec}s): {str(e)}"
            )
            raise OllamaTimeoutError(
                f"Ollama inference timed out after {self.timeout_sec} seconds"
            ) from e
