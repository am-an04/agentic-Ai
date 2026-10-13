import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Type, Generator, Union
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Price table: per 1,000,000 tokens (USD)
# [prompt_price_per_m, completion_price_per_m]
MODEL_PRICING: Dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    # Anthropic
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-opus-20240229": (15.00, 75.00),
    # Gemini
    "gemini-2.5-flash": (0.075, 0.30),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    # Ollama / Local
    "ollama": (0.0, 0.0),
    "llama3": (0.0, 0.0),
}

class LLMMessage(BaseModel):
    role: str  # system | user | assistant
    content: str

class LLMResponse(BaseModel):
    content: str
    parsed: Optional[Any] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0
    provider: str = ""
    model: str = ""
    validation_retries: int = 0

    def to_trace_log(self, step_name: str = "LLM Call") -> Dict[str, Any]:
        """Formats response metadata as a trace log entry compatible with DataPilot."""
        return {
            "step": step_name,
            "description": (
                f"LLM [{self.provider}:{self.model}] executed in {self.latency_ms:.1f}ms. "
                f"Tokens: {self.total_tokens} (prompt: {self.prompt_tokens}, completion: {self.completion_tokens}). "
                f"Est Cost: ${self.estimated_cost_usd:.6f}"
                + (f" (Self-repaired after {self.validation_retries} retries)" if self.validation_retries > 0 else "")
            ),
            "timestamp": time.time(),
            "llm_usage": {
                "provider": self.provider,
                "model": self.model,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "estimated_cost_usd": self.estimated_cost_usd,
                "latency_ms": self.latency_ms,
                "retries": self.validation_retries
            }
        }

def _clean_json_markdown(text: str) -> str:
    """Strips markdown code blocks ```json ... ``` or ``` ... ``` if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def _estimate_tokens(text: str, model_name: str = "gpt-4o") -> int:
    """Estimates token count using tiktoken with fallback to word count."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, len(text.split()) * 4 // 3)

def calculate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Calculates approximate cost in USD for a given model and token count."""
    for model_key, (in_price, out_price) in MODEL_PRICING.items():
        if model_key.lower() in model.lower():
            return (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000.0
    # Default fallback rate: $1 per 1M tokens
    return (prompt_tokens * 1.0 + completion_tokens * 2.0) / 1_000_000.0

class LLMService:
    """
    Unified, provider-agnostic LLM interface for DataPilot.
    Supports Anthropic, OpenAI, Gemini, and Ollama with:
    - Structured Pydantic output validation and 2x feedback self-repair retry
    - Exponential backoff and retry for network/rate-limit errors
    - Token tracking and cost logging
    - Synchronous invoke and streaming variants
    """
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        max_validation_retries: int = 2
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        self.api_key = api_key
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.temperature = float(temperature if temperature is not None else os.getenv("LLM_TEMPERATURE", "0.2"))
        self.timeout = float(timeout if timeout is not None else os.getenv("LLM_TIMEOUT", "60.0"))
        self.max_validation_retries = max_validation_retries

        # Set default model per provider if not specified
        if model:
            self.model = model
        else:
            default_models = {
                "openai": os.getenv("LLM_MODEL", "gpt-4o"),
                "anthropic": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
                "gemini": os.getenv("LLM_MODEL", "gemini-2.5-flash"),
                "ollama": os.getenv("LLM_MODEL", "llama3"),
            }
            self.model = default_models.get(self.provider, "gemini-2.5-flash")

    def is_configured(self) -> bool:
        """Returns True if the provider has necessary API credentials configured."""
        if self.provider == "ollama":
            return True
        if self.provider == "openai":
            return bool(self.api_key or os.getenv("OPENAI_API_KEY"))
        if self.provider == "anthropic":
            return bool(self.api_key or os.getenv("ANTHROPIC_API_KEY"))
        if self.provider == "gemini":
            return bool(self.api_key or os.getenv("GEMINI_API_KEY"))
        return False

    def _normalize_messages(self, messages: Union[str, List[Union[Dict[str, str], LLMMessage]]]) -> List[Dict[str, str]]:
        """Converts diverse message formats into standard [{'role': ..., 'content': ...}]."""
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        norm = []
        for m in messages:
            if isinstance(m, LLMMessage):
                norm.append({"role": m.role, "content": m.content})
            elif isinstance(m, dict):
                norm.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            else:
                norm.append({"role": "user", "content": str(m)})
        return norm

    def _call_raw_provider(self, messages: List[Dict[str, str]]) -> tuple[str, int, int]:
        """Calls the configured provider and returns (response_text, prompt_tokens, completion_tokens)."""
        if self.provider == "openai":
            return self._call_openai(messages)
        elif self.provider == "anthropic":
            return self._call_anthropic(messages)
        elif self.provider == "gemini":
            return self._call_gemini(messages)
        elif self.provider == "ollama":
            return self._call_ollama(messages)
        else:
            raise ValueError(f"Unsupported LLM provider '{self.provider}'. Supported: openai, anthropic, gemini, ollama")

    def _call_openai(self, messages: List[Dict[str, str]]) -> tuple[str, int, int]:
        key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is not set.")
        from openai import OpenAI
        client = OpenAI(api_key=key, timeout=self.timeout)
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        text = resp.choices[0].message.content or ""
        p_toks = resp.usage.prompt_tokens if resp.usage else _estimate_tokens(" ".join(m["content"] for m in messages))
        c_toks = resp.usage.completion_tokens if resp.usage else _estimate_tokens(text)
        return text, p_toks, c_toks

    def _call_ollama(self, messages: List[Dict[str, str]]) -> tuple[str, int, int]:
        from openai import OpenAI
        # Ollama exposes an OpenAI-compatible API at base_url
        client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",
            timeout=self.timeout
        )
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        text = resp.choices[0].message.content or ""
        p_toks = resp.usage.prompt_tokens if resp.usage else _estimate_tokens(" ".join(m["content"] for m in messages))
        c_toks = resp.usage.completion_tokens if resp.usage else _estimate_tokens(text)
        return text, p_toks, c_toks

    def _call_anthropic(self, messages: List[Dict[str, str]]) -> tuple[str, int, int]:
        key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=self.timeout)
        
        system_prompt = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_prompt += m["content"] + "\n\n"
            else:
                user_msgs.append({"role": m["role"], "content": m["content"]})
        if not user_msgs:
            user_msgs = [{"role": "user", "content": "Please proceed."}]

        resp = client.messages.create(
            model=self.model,
            system=system_prompt.strip() if system_prompt else None,
            messages=user_msgs,
            temperature=self.temperature,
            max_tokens=4096
        )
        text = resp.content[0].text if resp.content else ""
        p_toks = resp.usage.input_tokens if resp.usage else _estimate_tokens(system_prompt + " ".join(m["content"] for m in user_msgs))
        c_toks = resp.usage.output_tokens if resp.usage else _estimate_tokens(text)
        return text, p_toks, c_toks

    def _call_gemini(self, messages: List[Dict[str, str]]) -> tuple[str, int, int]:
        key = self.api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not set.")
        import google.generativeai as genai
        genai.configure(api_key=key)
        
        # Prepare contents and system instruction
        system_instruction = None
        gemini_contents = []
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            else:
                role = "user" if m["role"] == "user" else "model"
                gemini_contents.append({"role": role, "parts": [m["content"]]})
        
        if not gemini_contents:
            gemini_contents = [{"role": "user", "parts": ["Proceed."]}]

        model_kwargs = {"model_name": self.model}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        g_model = genai.GenerativeModel(**model_kwargs)
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
        )
        
        resp = g_model.generate_content(
            gemini_contents,
            generation_config=generation_config,
            request_options={"timeout": self.timeout}
        )
        text = resp.text if hasattr(resp, "text") and resp.text else ""
        p_toks = _estimate_tokens(" ".join(m["content"] for m in messages))
        c_toks = _estimate_tokens(text)
        return text, p_toks, c_toks

    def invoke(
        self,
        messages: Union[str, List[Union[Dict[str, str], LLMMessage]]],
        response_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Invokes the LLM with structured output enforcement and self-repair validation retries.
        """
        norm_messages = self._normalize_messages(messages)
        start_time = time.time()
        
        total_p_toks = 0
        total_c_toks = 0
        validation_retries = 0

        # If structured output is requested, append JSON formatting guidance
        if response_schema is not None:
            schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
            schema_instruction = (
                f"\n\nCRITICAL REQUIREMENT: Output MUST be a valid JSON object strictly matching this schema:\n"
                f"{schema_json}\n"
                f"Respond with JSON ONLY. Do not include markdown code fences or explanatory text outside the JSON."
            )
            # Append instruction to system message or last user message
            if norm_messages and norm_messages[0]["role"] == "system":
                norm_messages[0]["content"] += schema_instruction
            else:
                norm_messages.append({"role": "user", "content": schema_instruction})

        working_messages = list(norm_messages)
        parsed_result = None
        raw_text = ""

        # Retry loop for validation failures
        max_attempts = 1 + (self.max_validation_retries if response_schema else 0)

        for attempt in range(max_attempts):
            raw_text, p_tok, c_tok = self._call_raw_provider(working_messages)
            total_p_toks += p_tok
            total_c_toks += c_tok

            if response_schema is None:
                # Unstructured invocation succeeds immediately
                break

            # Try parsing structured JSON
            cleaned_json = _clean_json_markdown(raw_text)
            try:
                data = json.loads(cleaned_json)
                parsed_result = response_schema.model_validate(data)
                # Success!
                break
            except (json.JSONDecodeError, ValidationError, Exception) as err:
                validation_retries += 1
                if attempt < max_attempts - 1:
                    # Feed the validation error back to the LLM to self-repair
                    err_msg = f"Validation failed with error: {str(err)}. Invalid JSON payload was: {cleaned_json[:500]}"
                    feedback_prompt = (
                        f"Your previous response produced a validation error:\n{err_msg}\n\n"
                        f"Please fix the error and output ONLY the valid JSON object conforming strictly to the schema."
                    )
                    working_messages.append({"role": "assistant", "content": raw_text})
                    working_messages.append({"role": "user", "content": feedback_prompt})
                else:
                    # Final attempt failed
                    raise ValueError(
                        f"Failed to produce valid output matching {response_schema.__name__} after {max_attempts} attempts. "
                        f"Last error: {err}. Output was:\n{raw_text}"
                    )

        latency = (time.time() - start_time) * 1000.0
        total_tokens = total_p_toks + total_c_toks
        cost = calculate_cost(total_p_toks, total_c_toks, self.model)

        return LLMResponse(
            content=raw_text,
            parsed=parsed_result,
            prompt_tokens=total_p_toks,
            completion_tokens=total_c_toks,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            latency_ms=latency,
            provider=self.provider,
            model=self.model,
            validation_retries=validation_retries
        )

    def stream(
        self,
        messages: Union[str, List[Union[Dict[str, str], LLMMessage]]],
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming generator yielding text chunks incrementally."""
        norm_messages = self._normalize_messages(messages)

        if self.provider in ["openai", "ollama"]:
            from openai import OpenAI
            client = OpenAI(
                base_url=self.base_url if self.provider == "ollama" else None,
                api_key=self.api_key or ("ollama" if self.provider == "ollama" else os.getenv("OPENAI_API_KEY")),
                timeout=self.timeout
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=norm_messages,
                temperature=self.temperature,
                stream=True
            )
            for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices else ""
                if delta:
                    yield delta

        elif self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(
                api_key=self.api_key or os.getenv("ANTHROPIC_API_KEY"),
                timeout=self.timeout
            )
            system_prompt = ""
            user_msgs = []
            for m in norm_messages:
                if m["role"] == "system":
                    system_prompt += m["content"] + "\n\n"
                else:
                    user_msgs.append({"role": m["role"], "content": m["content"]})
            if not user_msgs:
                user_msgs = [{"role": "user", "content": "Please proceed."}]

            with client.messages.stream(
                model=self.model,
                system=system_prompt.strip() if system_prompt else None,
                messages=user_msgs,
                max_tokens=4096,
                temperature=self.temperature
            ) as stream:
                for text in stream.text_stream:
                    yield text

        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key or os.getenv("GEMINI_API_KEY"))
            gemini_contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in norm_messages if m["role"] != "system"]
            g_model = genai.GenerativeModel(model_name=self.model)
            response = g_model.generate_content(gemini_contents, stream=True)
            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
        else:
            raise ValueError(f"Streaming not supported for provider '{self.provider}'")

# Global singleton helper
_DEFAULT_CLIENT: Optional[LLMService] = None

def get_llm_service(reload: bool = False, **kwargs) -> LLMService:
    """Returns singleton LLMService instance or reloads with custom arguments."""
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None or reload:
        _DEFAULT_CLIENT = LLMService(**kwargs)
    return _DEFAULT_CLIENT
