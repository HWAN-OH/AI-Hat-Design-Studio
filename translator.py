import httpx
import asyncio
import json

async def get_design_plan_from_llm(command, api_key, persona, available_parts):
    """
    Uses the Gemini API to translate a natural language command into a structured design plan.
    자연어 명령을 구조화된 디자인 계획(JSON)으로 변환합니다.
    """
    if not api_key:
        return {"error": "API Key is missing."}

    persona_prompt = f"""
    You are {persona.get('role')}. Your personality is: {persona.get('personality')}.
    Your goal is to translate the user's command into a structured JSON action plan to build a 3D model in Blender.
    
    You have these parts available to you (this is the entire BOM): 
    {json.dumps(available_parts)}

    Based on the user's command, create a list of actions. The primary action is `load_and_place`.
    If the user asks for a style like "cowboy hat", use your knowledge base to determine which parts to load.
    
    Your response MUST be a valid JSON object containing a list of "actions".

    EXAMPLE:
    User command: "a navy baseball cap with a metal buckle"
    JSON Response:
    {{
      "actions": [
        {{
          "action": "load_and_place",
          "part_type": "Crown",
          "part_name": "6-Panel Classic"
        }},
        {{
          "action": "load_and_place",
          "part_type": "Brim",
          "part_name": "Curved Brim"
        }},
        {{
          "action": "load_and_place",
          "part_type": "Strap",
          "part_name": "Metal Buckle Strap"
        }}
      ]
    }}

    Now, parse this command:
    User command: "{command}"
    
    JSON Response:
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
    except Exception as e:
        return {"error": f"Error processing LLM response: {e}"}
