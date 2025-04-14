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
        return f"""
Given the PostgreSQL schema:
CREATE TABLE students (student_id SERIAL PRIMARY KEY, name TEXT NOT NULL, gender TEXT CHECK (gender IN ('MALE', 'FEMALE')), branch TEXT CHECK (branch IN ('CSE', 'ECE', 'IT', 'ME')), cgpa NUMERIC(3,2) CHECK (cgpa BETWEEN 6.00 AND 10.00), passing_year INTEGER CHECK (passing_year BETWEEN 2000 AND 2050));
CREATE TABLE offers (offer_id SERIAL PRIMARY KEY, student_id INTEGER REFERENCES students(student_id), company_id INTEGER REFERENCES companies(company_id), package_lpa INTEGER, offer_day INTEGER CHECK (offer_day BETWEEN 1 AND 31), offer_month INTEGER CHECK (offer_month BETWEEN 1 AND 12), offer_year INTEGER CHECK (offer_year BETWEEN 2000 AND 2050));
CREATE TABLE skills (skill_id SERIAL PRIMARY KEY, name TEXT CHECK (name IN ('Python', 'Java', 'Machine Learning', 'Data Structures', 'SQL', 'Web Development', 'C++', 'Deep Learning')));
CREATE TABLE studentskills (student_id INTEGER, skill_id INTEGER, PRIMARY KEY (student_id, skill_id), FOREIGN KEY (student_id) REFERENCES students(student_id), FOREIGN KEY (skill_id) REFERENCES skills(skill_id));
CREATE TYPE industry_enum AS ENUM ('ML', 'Software', 'Consulting', 'IT Services');
CREATE TYPE offer_type_enum AS ENUM ('Full_time', 'Internship');
CREATE TABLE companies (company_id SERIAL PRIMARY KEY, name TEXT, industry industry_enum, visit_day INTEGER CHECK (visit_day BETWEEN 1 AND 31), visit_month INTEGER CHECK (visit_month BETWEEN 1 AND 12), visit_year INTEGER CHECK (visit_year BETWEEN 2000 AND 2050), offer_type offer_type_enum);
Convert this question to a valid SQL query:
Question: {question}
Return only the SQL query or if the questin is not relavent to the dataset or even not a perfect question then give  NOT RELEVENT QUESTION.
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