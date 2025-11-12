"""
LLM Client for Flight School Data Extraction

Provides unified interface for Claude 3.5 Sonnet (AWS Bedrock) and GPT-4o (OpenAI) APIs.
Handles automatic fallback, token counting, and error recovery.

Author: Cursor Agent White (PR-1.4)
Created: 2025-11-11
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, Union, Tuple
import hashlib

import boto3
from anthropic import Anthropic
from openai import OpenAI
from botocore.exceptions import BotoCoreError, ClientError
import httpx

from error_handler import ExtractionError, ErrorSeverity


class LLMProvider(Enum):
    """Available LLM providers."""
    CLAUDE_BEDROCK = "claude_bedrock"
    OPENAI_GPT4O = "openai_gpt4o"


@dataclass
class LLMResponse:
    """Structured response from LLM API."""
    content: str
    provider: LLMProvider
    tokens_used: int
    confidence_score: float
    raw_response: Dict[str, Any]
    processing_time: float


class LLMClient:
    """
    Unified LLM client with automatic fallback and caching.

    Primary: Claude 3.5 Sonnet via AWS Bedrock
    Fallback: GPT-4o via OpenAI API
    """

    def __init__(self):
        # Initialize clients
        self.anthropic = None
        self.openai_client = None
        self.bedrock_client = None

        # Configuration
        self.max_retries = 3
        self.retry_delay = 2.0
        self.cache = {}  # Simple in-memory cache

        # Token counting (approximate)
        self.token_counts = {
            LLMProvider.CLAUDE_BEDROCK: 0,
            LLMProvider.OPENAI_GPT4O: 0
        }

        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize LLM API clients with error handling."""
        try:
            # Claude via Anthropic API (if API key available)
            claude_key = os.getenv('ANTHROPIC_API_KEY')
            if claude_key:
                self.anthropic = Anthropic(api_key=claude_key)

            # OpenAI (fallback)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)

            # AWS Bedrock (primary for Claude)
            try:
                self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
            except Exception as e:
                print(f"Warning: Could not initialize Bedrock client: {e}")

        except Exception as e:
            raise ExtractionError(
                f"Failed to initialize LLM clients: {e}",
                severity=ErrorSeverity.CRITICAL,
                component="llm_client"
            )

    def _get_cache_key(self, prompt: str, provider: LLMProvider) -> str:
        """Generate cache key for prompt."""
        content = f"{prompt}:{provider.value}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _call_claude_bedrock(self, prompt: str, temperature: float = 0.1) -> LLMResponse:
        """Call Claude 3.5 Sonnet via AWS Bedrock."""
        if not self.bedrock_client:
            raise ExtractionError("Bedrock client not available", severity=ErrorSeverity.WARNING)

        start_time = time.time()

        try:
            # Prepare Bedrock request
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "system": "You are a specialized data extraction assistant for flight school information. Always respond with valid JSON."
            })

            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                body=body,
                contentType="application/json",
                accept="application/json"
            )

            response_body = json.loads(response['body'].read())

            content = response_body['content'][0]['text']
            tokens_used = self._estimate_tokens(prompt + content)

            processing_time = time.time() - start_time

            return LLMResponse(
                content=content,
                provider=LLMProvider.CLAUDE_BEDROCK,
                tokens_used=tokens_used,
                confidence_score=0.95,  # Claude typically has high confidence
                raw_response=response_body,
                processing_time=processing_time
            )

        except (BotoCoreError, ClientError) as e:
            raise ExtractionError(f"Bedrock API error: {e}", severity=ErrorSeverity.WARNING)
        except Exception as e:
            raise ExtractionError(f"Unexpected Bedrock error: {e}", severity=ErrorSeverity.WARNING)

    async def _call_openai_gpt4o(self, prompt: str, temperature: float = 0.1) -> LLMResponse:
        """Call GPT-4o via OpenAI API (fallback)."""
        if not self.openai_client:
            raise ExtractionError("OpenAI client not available", severity=ErrorSeverity.WARNING)

        start_time = time.time()

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a specialized data extraction assistant for flight school information. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4096,
                temperature=temperature,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            processing_time = time.time() - start_time

            return LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI_GPT4O,
                tokens_used=tokens_used,
                confidence_score=0.85,  # Slightly lower confidence than Claude
                raw_response=response.model_dump(),
                processing_time=processing_time
            )

        except Exception as e:
            raise ExtractionError(f"OpenAI API error: {e}", severity=ErrorSeverity.WARNING)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(text) // 4

    async def extract_with_fallback(self, prompt: str, use_cache: bool = True) -> LLMResponse:
        """
        Extract data using primary provider with automatic fallback.

        Args:
            prompt: The extraction prompt
            use_cache: Whether to use response caching

        Returns:
            LLMResponse with extracted data
        """
        cache_key = self._get_cache_key(prompt, LLMProvider.CLAUDE_BEDROCK)

        # Check cache first
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]

        # Try primary provider (Claude via Bedrock)
        try:
            response = await self._call_claude_bedrock(prompt)
            if use_cache:
                self.cache[cache_key] = response
            self.token_counts[LLMProvider.CLAUDE_BEDROCK] += response.tokens_used
            return response

        except ExtractionError as e:
            print(f"Primary provider failed: {e}. Trying fallback...")

            # Try fallback provider (GPT-4o)
            try:
                response = await self._call_openai_gpt4o(prompt)
                if use_cache:
                    self.cache[cache_key] = response
                self.token_counts[LLMProvider.OPENAI_GPT4O] += response.tokens_used
                return response

            except ExtractionError as fallback_error:
                raise ExtractionError(
                    f"Both LLM providers failed. Primary: {e}, Fallback: {fallback_error}",
                    severity=ErrorSeverity.ERROR,
                    component="llm_client"
                )

    def get_token_usage(self) -> Dict[str, int]:
        """Get current token usage by provider."""
        return {
            "claude_bedrock": self.token_counts[LLMProvider.CLAUDE_BEDROCK],
            "openai_gpt4o": self.token_counts[LLMProvider.OPENAI_GPT4O],
            "total": sum(self.token_counts.values())
        }

    def clear_cache(self):
        """Clear the response cache."""
        self.cache.clear()


# Global client instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def extract_flight_school_data(prompt: str) -> LLMResponse:
    """
    Convenience function for flight school data extraction.

    Args:
        prompt: Extraction prompt

    Returns:
        LLMResponse with structured data
    """
    client = get_llm_client()
    return await client.extract_with_fallback(prompt)


if __name__ == "__main__":
    # Test the client
    async def test():
        client = get_llm_client()

        test_prompt = "Extract flight school information from: 'ABC Flight School offers PPL training for $8000. Located in Miami, FL. Contact: (305) 555-0123'"

        try:
            response = await client.extract_with_fallback(test_prompt, use_cache=False)
            print(f"Provider: {response.provider.value}")
            print(f"Tokens: {response.tokens_used}")
            print(f"Content: {response.content[:200]}...")
            print(f"Token usage: {client.get_token_usage()}")

        except Exception as e:
            print(f"Test failed: {e}")

    asyncio.run(test())
