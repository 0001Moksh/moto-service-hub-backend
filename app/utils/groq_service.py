import base64
import json
import logging
from groq import Groq
from app.core.config import settings
from typing import Dict, Any
import re

logger = logging.getLogger(__name__)

# Initialize Groq client
try:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info("✅ Groq client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq: {e}")
    groq_client = None


def get_image_as_base64(image_path: str) -> str:
    """Convert image file to base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.standard_b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None


def extract_aadhaar_data(image_path: str) -> Dict[str, Any]:
    """Extract Aadhaar card data using Groq LLM"""
    try:
        if groq_client is None:
            return {"error": "Groq client not initialized"}
        
        image_base64 = get_image_as_base64(image_path)
        if not image_base64:
            return {"error": "Failed to process image"}
        
        prompt = """Analyze this Aadhaar card image and extract the following information:
        1. Name (as shown on card)
        2. Gender
        3. Date of Birth (in DD/MM/YYYY format)
        4. Aadhaar Number (12 digit number)
        5. Any other important information visible
        
        Return the data as JSON format only, nothing else. If any field is not clearly visible, mark it as "Not visible".
        Example JSON format:
        {
            "name": "John Doe",
            "gender": "Male",
            "dob": "01/01/1990",
            "aadhaar_number": "123456789012",
            "additional_info": ""
        }
        """
        
        completion = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )
        
        response_text = completion.choices[0].message.content
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group())
                logger.info(f"✅ Aadhaar data extracted successfully")
                return {"success": True, "data": extracted_data}
            else:
                logger.warning(f"No JSON found in response: {response_text}")
                return {"error": "Could not parse response", "raw_response": response_text}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"error": "Invalid JSON in response", "raw_response": response_text}
        
    except Exception as e:
        logger.error(f"Error extracting Aadhaar data: {e}")
        return {"error": str(e)}


def extract_rc_data(image_path: str) -> Dict[str, Any]:
    """Extract RC (Registration Certificate) data using Groq LLM"""
    try:
        if groq_client is None:
            return {"error": "Groq client not initialized"}
        
        image_base64 = get_image_as_base64(image_path)
        if not image_base64:
            return {"error": "Failed to process image"}
        
        prompt = """
Analyze this vehicle RC (Registration Certificate) image and extract the following information:

1. Vehicle Registration Number
2. Owner Name
3. Vehicle Class
4. Fuel Type (Petrol / Diesel / CNG / LPG / Electric)
5. Manufacturer
6. Model Number / Model Name
7. Chassis Number
8. Engine Number
9. Registration Date
10. Vehicle Color
11. Body Type (Bike / Scooter / Sedan / SUV / Hatchback / Truck etc.)
12. Manufacturing Date (if available)
13. Registration Validity / RC Validity (if available)

Return the extracted information in **JSON format only**. Do not include explanations.

If any value is not visible or cannot be identified, return "Not visible".

The JSON must follow this exact schema:

{
    "reg_number": "MH01AB1234", 
    "owner_name": "John Doe", 
    "vehicle_class": "Light Motor Vehicle", 
    "fuel_type": "Petrol", 
    "manufacturer": "Bajaj", 
    "model": "Pulsar 150", 
    "chassis_number": "XXXX", 
    "engine_number": "YYYY", 
    "registration_date": "01/01/2020", 
    "color": "Black", 
    "body_type": "Bike",
    "manufacture_date": "",
    "refid_validity": ""
}
"""
        
        completion = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.3,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )
        
        response_text = completion.choices[0].message.content
        
        # Extract JSON from response
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted_data = json.loads(json_match.group())
                logger.info(f"RC data extracted successfully")
                return {"success": True, "data": extracted_data}
            else:
                logger.warning(f"No JSON found in response: {response_text}")
                return {"error": "Could not parse response", "raw_response": response_text}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"error": "Invalid JSON in response", "raw_response": response_text}
        
    except Exception as e:
        logger.error(f"Error extracting RC data: {e}")
        return {"error": str(e)}
