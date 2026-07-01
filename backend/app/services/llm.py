import json
import logging
import httpx
from app.config import settings

logger = logging.getLogger("app.services.llm")

GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are the Intent Extraction and Trust & Safety Evaluation engine of an Enterprise AI Governance Platform.
Analyze the user's natural language request and extract structured parameters in JSON format.

Your output MUST be a JSON object with the following fields:
1. "extracted_action": (string or null) The action type in UPPERCASE. Examples: DELETE, TRANSFER, UPDATE, CREATE, READ.
2. "extracted_object": (string or null) The main subject/entity being acted upon. Examples: customers, patient_record, salary, report, cash.
3. "extracted_scope": (string or null) The scope, constraints, filters, or specific targets of the action. Examples: "inactive", "₹50,000 to John Doe", "employee ID 4".
4. "confidence": (float between 0.0 and 1.0) Your extraction confidence score.
5. "missing_info": (array of strings) Any required parameters for this type of action that are missing.
   - For TRANSFER: Needs source account, destination account, and amount.
   - For DELETE: Needs scope/filters (e.g. which records, ID, or criteria) and reason.
   - For UPDATE: Needs target record, field name, and new value.
   If any of these critical details are not specified in the natural language text, add their name to the "missing_info" list (e.g. ["destination_account", "reason_for_deletion"]).
6. "safety_eval": A nested JSON object with the following safety and trustworthiness ratings (each a float between 0.0 and 1.0):
   - "negation": (float) 1.0 if the prompt contains negation instructions, negative commands, or contradictory orders (e.g. "don't execute", "do not save", "never delete"), 0.0 if normal.
   - "harmful_biasness": (float) 1.0 if the prompt contains harmful bias, stereotypes, discrimination, or unfair assumptions, 0.0 if unbiased.
   - "confabulation": (float) 1.0 if the prompt requests fabricated facts, hallucinated info, or unverifiable claims, 0.0 if grounded.
   - "integrity": (float) 1.0 if the prompt aligns with high data/information integrity standards (no corruption or falsifying data), 0.0 if it requests data corruption, falsification, or unauthorized data changes.
   - "abusive": (float) 1.0 if the prompt contains abusive language, slurs, toxic text, insults, or harassment, 0.0 if clean.
   - "privacy_enhanced": (float) 1.0 if the prompt is highly privacy-enhanced, fully protects data privacy, or doesn't expose sensitive PII. 0.0 if the prompt exposes, leaks, or requests unauthorized sharing/retrieval of sensitive personal information (PII/medical/financial records).
   - "dangerous": (float) 1.0 if the prompt requests dangerous actions, unsafe operations, real-world harm, or hacking exploits, 0.0 if safe.
   - "violent": (float) 1.0 if the prompt requests violence, threats, harm to persons, or self-harm, 0.0 if clean.
   - "environmental_impacts": (float) 1.0 if the action requested has high carbon/environmental footprint or represents massive computational waste (e.g. request to run extremely large unoptimized computations, hardware abuse, wasteful infinite loops), 0.0 if minimal footprint.

Example Input: "Delete inactive customers"
Example Output:
{
  "extracted_action": "DELETE",
  "extracted_object": "customers",
  "extracted_scope": "inactive",
  "confidence": 0.95,
  "missing_info": ["reason_for_deletion"],
  "safety_eval": {
    "negation": 0.0,
    "harmful_biasness": 0.0,
    "confabulation": 0.0,
    "integrity": 1.0,
    "abusive": 0.0,
    "privacy_enhanced": 1.0,
    "dangerous": 0.0,
    "violent": 0.0,
    "environmental_impacts": 0.0
  }
}

Do not include any introductory or concluding text. Return ONLY the JSON object.
"""

async def extract_intent(natural_language_request: str) -> dict:
    """Send natural language request to Groq Llama 3.3 to extract structured intent parameters and evaluate safety metrics."""
    logger.info(f"Sending request to Groq API for intent extraction & safety evaluation: {natural_language_request}")
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract intent and evaluate safety for this request: \"{natural_language_request}\""}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }
    
    fallback_response = {
        "extracted_action": None,
        "extracted_object": None,
        "extracted_scope": None,
        "confidence": 0.0,
        "missing_info": [],
        "safety_eval": {
            "negation": 0.0,
            "harmful_biasness": 0.0,
            "confabulation": 0.0,
            "integrity": 1.0,
            "abusive": 0.0,
            "privacy_enhanced": 1.0,
            "dangerous": 0.0,
            "violent": 0.0,
            "environmental_impacts": 0.0
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(GROQ_COMPLETIONS_URL, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Groq API returned error status {response.status_code}: {response.text}")
                return fallback_response
                
            res_json = response.json()
            choices = res_json.get("choices", [])
            if not choices:
                logger.error("Groq API response has no choices.")
                return fallback_response
                
            content = choices[0].get("message", {}).get("content", "")
            logger.debug(f"Groq raw content response: {content}")
            
            extracted_data = json.loads(content)
            
            safety = extracted_data.get("safety_eval", {})
            # Basic validation/cleansing
            validated_data = {
                "extracted_action": extracted_data.get("extracted_action"),
                "extracted_object": extracted_data.get("extracted_object"),
                "extracted_scope": extracted_data.get("extracted_scope"),
                "confidence": float(extracted_data.get("confidence", 0.0)),
                "missing_info": list(extracted_data.get("missing_info", [])),
                "safety_eval": {
                    "negation": float(safety.get("negation", 0.0)),
                    "harmful_biasness": float(safety.get("harmful_biasness", 0.0)),
                    "confabulation": float(safety.get("confabulation", 0.0)),
                    "integrity": float(safety.get("integrity", 1.0)),
                    "abusive": float(safety.get("abusive", 0.0)),
                    "privacy_enhanced": float(safety.get("privacy_enhanced", 1.0)),
                    "dangerous": float(safety.get("dangerous", 0.0)),
                    "violent": float(safety.get("violent", 0.0)),
                    "environmental_impacts": float(safety.get("environmental_impacts", 0.0))
                }
            }
            
            logger.info(f"Successfully extracted intent and safety metrics: {validated_data}")
            return validated_data
            
    except httpx.RequestError as e:
        logger.error(f"HTTP request error calling Groq API: {e}")
        return fallback_response
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response from Groq: {e}")
        return fallback_response
    except Exception as e:
        logger.error(f"Unexpected error in intent extraction: {e}")
        return fallback_response
