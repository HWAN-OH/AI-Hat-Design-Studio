import httpx
import asyncio
import json

async def parse_command_with_llm(command, api_key, persona, available_parts):
    """
    Uses the Gemini API to parse the user's natural language command based on a given persona.
    주어진 페르소나를 기반으로, Gemini API를 사용하여 사용자의 자연어 명령을 해석합니다.
    """
    if not api_key:
        # In a real app, you might raise an exception or handle this differently.
        # 실제 앱에서는 예외를 발생시키거나 다르게 처리할 수 있습니다.
        return {"error": "API Key is missing."}

    # The LLM prompt is now built here, inside the engine.
    # LLM 프롬프트는 이제 엔진 내부에서 만들어집니다.
    persona_prompt = f"""
    You are {persona.get('role', 'an AI assistant')}.
    Your personality is: {persona.get('personality', 'helpful')}.
    Your goal is to translate the user's command into a structured JSON action based on your capabilities and knowledge.
    
    Your capabilities are: {json.dumps(persona.get('capabilities'))}
    Your knowledge base for styles is: {json.dumps(persona.get('knowledge_base'))}
    You have these parts available to you (this is the entire BOM): {json.dumps(available_parts)}

    Based on the user's command, decide which action to take. Your response MUST be a single, valid JSON object.

    EXAMPLES:
    - User: "make the logo 2x bigger" -> {{"action": "change_property", "target": "logo", "property": "scale", "value": 2.0}}
    - User: "I want a cowboy hat" -> {{"action": "apply_style", "style_name": "cowboy hat", "part_changes": [{{"part_type": "Crown", "name_contains": "Fedora"}}, {{"part_type": "Brim", "name_contains": "Wide"}}]}}

    Now, parse this command:
    User command: "{command}"
    
    JSON Action:
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": persona_prompt}]}]}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            clean_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except httpx.HTTPStatusError as e:
        return {"error": f"API Request Failed: {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        return {"error": f"Error processing LLM response: {e}"}

