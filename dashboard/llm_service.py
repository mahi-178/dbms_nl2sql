import requests
import json
import os
from django.conf import settings

class LLMService:
    def __init__(self, service_type=None):
        self.service_type = service_type or settings.LLM_SERVICE_TYPE
        
        if self.service_type == "huggingface":
            self.api_key = settings.HUGGINGFACE_API_KEY
            self.endpoint = f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}"
        else:
            raise ValueError(f"Unsupported LLM service type: {self.service_type}")
            
    def generate_sql(self, natural_language, schema_info):
        """
        Generate SQL from natural language using the selected LLM service
        """
        prompt = self._create_prompt(natural_language, schema_info)
        
        if self.service_type == "huggingface":
            return self._query_huggingface(prompt)
    
    def _create_prompt(self, question, schema_info):
        """
        Create a prompt for the LLM with the question and schema information
        """
        return f"""
Given the following PostgreSQL database schema:
{schema_info}

Convert this natural language question to a valid SQL query:
Question: {question}

Return only the SQL query without any explanation or additional text.
"""
    
    def _query_huggingface(self, prompt):
        """
        Query HuggingFace's Inference API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.1,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        response = requests.post(self.endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the generated text from the response
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                # Attempt to extract just the SQL query
                if "SELECT" in generated_text:
                    # Try to get just the SQL part
                    import re
                    sql_match = re.search(r"(SELECT.*?)(;|\Z)", generated_text, re.DOTALL | re.IGNORECASE)
                    if sql_match:
                        return sql_match.group(1).strip()
                return generated_text.strip()
            else:
                raise Exception(f"Unexpected response format from API: {result}")
        else:
            raise Exception(f"Error from HuggingFace API: {response.text}")