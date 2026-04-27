# src/inference/translator.py
import ollama
import asyncio
import json
import re


class NuanceTranslator:
    """
    Translates Japanese manga text via a local Ollama instance.
    """

    def __init__(self, model_name: str = "translategemma:12b"):
        self.model_name = model_name
        ollama.pull(model_name)  # Ensure the model is available locally (no-op if already pulled)   

    # ------------------------------------------------------------------
    # Prompt builder (shared between sync and async paths)
    # ------------------------------------------------------------------

    def _build_prompt(self, japanese_text: str, context: str = "Standard dialogue") -> str:
            # We use 'IMPORTANT' and 'ONLY' to override the model's instinct to think out loud.
            return f"""
            You are a professional Japanese (ja) to English (en) Translator specialising in manga. Your goal is to accurately convey the meaning and
            nuances of the original Japanese text while adhering to English grammar and natural phrasing. Produce only
            English translation, without any additional commentary or explanation.
            The translation should be concise and fit within the typical space of a manga speech bubble, while preserving the original meaning and tone.

            Return complete sentences where possible, unless the original Japanese is fragmented. In that case, maintain the fragmentation in English to preserve the character's voice and the scene's pacing.

            PROPER NOUN RULES (CRITICAL):
            1. Do NOT translate proper nouns (character names, place names, organizations).
            2. If a name is written in kanji/kana, preserve it OR convert to standard romaji.
            3. NEVER translate names into their literal meanings (e.g. "Black Sword" instead of a name).
            4. If unsure whether a term is a proper noun, assume that it IS and preserve it.

            Japanese Text: {japanese_text}
    
            JSON Format:
            {{
                "translation": "..."
            }}
            """

    def _parse_response(self, text: str) -> dict:
            try:
                # Look for ALL JSON blocks (model may have a "thinking" preamble)
                all_json_blocks = re.findall(r'(\{.*?\})', text, re.DOTALL)
                if all_json_blocks:
                    # Take the last complete block — skip any that are missing the translation key
                    for block in reversed(all_json_blocks):
                        try:
                            parsed = json.loads(block)
                            if "translation" in parsed and parsed["translation"].strip():
                                return parsed
                        except json.JSONDecodeError:
                            continue
                # Fallback: try to parse the whole response
                return json.loads(text.strip())
            except Exception as e:
                # Last resort: attempt to extract a partial translation value
                # Handles truncated output like: {"translation": "The ninja of
                match = re.search(r'"translation"\s*:\s*"([^"]+)', text)
                if match:
                    partial = match.group(1).strip()
                    if partial:
                        print(f"[Translator] WARNING: Recovered partial translation: '{partial[:60]}...'")
                        return {"translation": partial}

                print(f"[Translator] Failed to parse JSON. Raw: {text[:200]}")

                return self._error_result("JSON extraction failed")



    def _error_result(self, message: str) -> dict:
        return {"translation": message}

    # ------------------------------------------------------------------
    # Synchronous interface (unchanged — used by __main__ test)
    # ------------------------------------------------------------------

    def translate(self, japanese_text: str) -> dict:
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=self._build_prompt(japanese_text),
                format="json",
                options={"num_ctx": 3072, "num_predict": 256}
            )
            
            return self._parse_response(response["response"])
        except json.JSONDecodeError:
            print("Translator JSON Error")
            print(response)
        except Exception as e:
            print(f"Translator General Error: {e}")
            return self._error_result("Error: Connection to Ollama failed")

    # ------------------------------------------------------------------
    # Async interface (used by processor.py via asyncio.gather)
    #
    # Why asyncio and not threading?
    # --------------------------------
    # Ollama calls are I/O-bound (we're waiting on a network socket to the
    # local server, not doing CPU work). asyncio lets Python interleave the
    # waiting periods of many calls without the overhead of real threads.
    # asyncio.gather fires all coroutines and collects results as they land.
    # ------------------------------------------------------------------

    async def translate_async(self, japanese_text: str) -> dict:
        """
        Async version of translate(). Called concurrently by processor.py
        for all bubbles on a page via asyncio.gather().
        """
        loop = asyncio.get_event_loop()
        try:
            # ollama.generate is synchronous, so we run it in a thread pool
            # executor to avoid blocking the event loop while waiting for
            # the LLM response. This is the standard pattern for wrapping
            # blocking I/O inside async code.
            response = await loop.run_in_executor(
                None,  # uses the default ThreadPoolExecutor
                lambda: ollama.generate(
                    model=self.model_name,
                    prompt=self._build_prompt(japanese_text),
                    format="json",
                    options={"num_ctx": 3072, "num_predict": 256}
                ),
            )
            return self._parse_response(response["response"])
        except json.JSONDecodeError:
            print(f"Translator JSON Error: Could not parse LLM response.")
            return self._error_result("Error: Invalid JSON from LLM")
        except Exception as e:
            print(f"Translator General Error: {e}")
            return self._error_result("Error: Connection to Ollama failed")