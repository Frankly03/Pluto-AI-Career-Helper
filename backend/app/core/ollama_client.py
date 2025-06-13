# backend/app/core/ollama_client.py

import httpx
import json
import logging
from typing import List, Dict, Any, Optional

from .config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    A client for interacting with an Ollama API.
    Assumes Ollama server is running and accessible at OLLAMA_BASE_URL.
    """
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.api_generate_url = f"{self.base_url}/api/generate"

    async def generate_response(
        self, 
        prompt: str, 
        model_override: Optional[str] = None,
        stream: bool = False, # Ollama supports streaming, but we'll use non-streaming for simplicity here
        context: Optional[List[int]] = None, # For conversational context
        options: Optional[Dict[str, Any]] = None # Ollama specific options (e.g. temperature)
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a prompt to the Ollama API and gets a response.

        Args:
            prompt: The input prompt for the LLM.
            model_override: Optionally override the default model.
            stream: Whether to stream the response. Defaults to False.
            context: Optional conversational context.
            options: Optional Ollama parameters.

        Returns:
            A dictionary containing the Ollama API response, or None if an error occurs.
        """
        current_model = model_override if model_override else self.model
        payload = {
            "model": current_model,
            "prompt": prompt,
            "stream": stream,
        }
        if context:
            payload["context"] = context
        if options:
            payload["options"] = options

        logger.debug(f"Sending request to Ollama: {self.api_generate_url} with model {current_model}")
        # logger.debug(f"Payload: {json.dumps(payload, indent=2)}") # Be careful logging full prompts if sensitive

        try:
            async with httpx.AsyncClient(timeout=120.0) as client: # Increased timeout for LLM
                response = await client.post(self.api_generate_url, json=payload)
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                
                # For non-streaming, response is a single JSON object
                # For streaming, it would be a series of JSON objects, newline-delimited
                if stream:
                    # This part would need to be handled differently if true streaming is implemented
                    # For now, assuming stream=False, so this won't be hit with current usage.
                    full_response_content = ""
                    async for line in response.aiter_lines():
                        if line:
                            json_line = json.loads(line)
                            full_response_content += json_line.get("response", "")
                            if json_line.get("done"):
                                # Capture final context if needed
                                final_context = json_line.get("context") 
                                return {"response": full_response_content, "context": final_context, "done": True}
                    return None # Should not happen if done is always true at the end

                else: # stream=False
                    response_data = response.json()
                    logger.debug(f"Ollama response received (model: {current_model}).")
                    # Example non-streaming response structure:
                    # {
                    #   "model": "llama3",
                    #   "created_at": "2023-08-04T18:54:27.653783Z",
                    #   "response": "The sky is blue because of Rayleigh scattering...",
                    #   "done": true,
                    #   "context": [123, 456, ...], (optional, for follow-up)
                    #   "total_duration": 5032962750,
                    #   "load_duration": 2039875,
                    #   "prompt_eval_count": 26,
                    #   "prompt_eval_duration": 325953000,
                    #   "eval_count": 190,
                    #   "eval_duration": 4691954000
                    # }
                    return response_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while calling Ollama API: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while calling Ollama API: {e}", exc_info=True)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response from Ollama API: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred in OllamaClient: {e}", exc_info=True)
        
        return None

    async def get_text_response(self, prompt: str, model_override: Optional[str] = None) -> Optional[str]:
        """
        Helper method to get just the text response from Ollama.
        """
        response_data = await self.generate_response(prompt, model_override=model_override, stream=False)
        if response_data and "response" in response_data:
            return response_data["response"].strip()
        return None

# Example usage (can be run with `python -m app.core.ollama_client` from backend dir if __main__ is added)
# async def main():
#     client = OllamaClient()
#     prompt = "Why is the sky blue?"
#     response_text = await client.get_text_response(prompt)
#     if response_text:
#         print("Ollama's Response:")
#         print(response_text)
#     else:
#         print("Failed to get response from Ollama.")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
