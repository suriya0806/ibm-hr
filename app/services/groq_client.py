import json
import re
from typing import Dict, Any, Optional
from config import Config

class GroqService:
    _llm = None
    _client = None

    @classmethod
    def get_llm(cls):
        if cls._llm is None and Config.GROQ_API_KEY:
            try:
                from langchain_groq import ChatGroq
                cls._llm = ChatGroq(
                    groq_api_key=Config.GROQ_API_KEY,
                    model_name=Config.GROQ_MODEL,
                    temperature=0.2,
                    max_retries=2
                )
            except Exception as e:
                print(f"[GroqService] Warning: Could not initialize ChatGroq: {e}")
                cls._llm = None
        return cls._llm

    @classmethod
    def call_llm(cls, prompt: str, system_message: str = "You are an expert HR Recruitment AI.") -> str:
        """
        Executes a prompt against Groq LLM.
        """
        llm = cls.get_llm()
        if llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=prompt)
                ]
                response = llm.invoke(messages)
                return response.content.strip()
            except Exception as e:
                print(f"[GroqService] Groq API call error: {e}")
                # Try fallback model if configured
                try:
                    from langchain_groq import ChatGroq
                    fallback = ChatGroq(
                        groq_api_key=Config.GROQ_API_KEY,
                        model_name=Config.GROQ_FALLBACK_MODEL,
                        temperature=0.2
                    )
                    from langchain_core.messages import HumanMessage, SystemMessage
                    messages = [
                        SystemMessage(content=system_message),
                        HumanMessage(content=prompt)
                    ]
                    response = fallback.invoke(messages)
                    return response.content.strip()
                except Exception as e2:
                    print(f"[GroqService] Fallback model also failed: {e2}")

        # If LLM unavailable or API key not set, return empty string for fallback handling
        return ""

    @classmethod
    def call_structured_json(cls, prompt: str, system_message: str) -> Optional[Dict[str, Any]]:
        """
        Calls Groq with strict JSON output instruction and parses JSON.
        """
        json_system_message = (
            f"{system_message}\n"
            "CRITICAL: Return ONLY a valid JSON object. Do not include markdown code blocks (```json), "
            "do not include introductory or concluding text. Output purely valid JSON."
        )
        content = cls.call_llm(prompt, system_message=json_system_message)
        if not content:
            return None

        # Clean markdown wrappers if any
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        elif clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        clean_content = clean_content.strip()

        try:
            return json.loads(clean_content)
        except json.JSONDecodeError:
            # Attempt regex extraction of the first {...} block
            match = re.search(r"\{.*\}", clean_content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            print(f"[GroqService] JSON parse error for content: {clean_content[:200]}...")
            return None

