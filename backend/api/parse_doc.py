from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, List, Optional
# import ollama
from pydantic import BaseModel
import asyncio
from dataclasses import dataclass
import re
import json
router = APIRouter()


class PatternLearner:

    def __init__(self,model = 'mistral:7b-instruct') :
        self.model = model 

    def learn_patterns(self,query:str):

        prompt = f"""
You are analyzing exam question formatting patterns.

EXAM SAMPLE:
{query}

YOUR TASK:
Examine this text carefully and discover:
1. How are questions numbered? Look at the actual format used.
2. Where are marks indicated? Look at the exact syntax.
3. Are there sub-parts? What format do they use?

Think step-by-step:
- First, list what you observe about the structure
- Then, create regex patterns that match what you found
- Test mentally: would your regex work on similar questions?

Return JSON with your findings:
{{
  "observations": {{
    "question_format": "describe what you see",
    "marks_format": "describe what you see",
    "subparts_format": "describe what you see"
  }},
  "regex_patterns": {{
    "main_question": "your regex here",
    "marks": "your regex here",
    "sub_question": "your regex here"
  }},
  "test_examples": {{
    "what_matches": ["example 1", "example 2"],
    "edge_cases": ["tricky case you noticed"]
  }}
}}

Return only valid JSON, no other text.
"""

        # response = ollama.generate(
        #     model=self.model,
        #     prompt=prompt,
        #     stream= False,
        #     options={
        #         "temperature": 0.1,  # Low temp for consistent patterns
        #         "num_predict": 3000
        #     }
        # )
        # return response


sample_exam_text = """
Johannes Kepler Universität Linz
Institut für Machine Learning
Winter Semester 2024

MACHINE LEARNING - FINAL EXAM
Prüfungsdauer: 120 Minuten
Gesamtpunkte: 100

TEIL A: THEORETISCHE FRAGEN (40 Punkte)

Q1. Define supervised learning and explain the key differences between classification 
and regression tasks. Provide one real-world example for each. [8 Punkte]

Q2. Consider the following dataset for a binary classification problem:
   a) Calculate the Gini impurity for the root node
   b) Determine the best split using information gain
   c) Explain why decision trees are prone to overfitting
[12 Punkte]

Q3. Explain the concept of backpropagation in neural networks.
   a) Describe the forward pass computation
   b) Describe the backward pass and gradient calculation
   c) What is the vanishing gradient problem?
   d) Name two techniques to address this problem
[10 Punkte]

Q4. What is the bias-variance tradeoff? How does model complexity affect both bias 
and variance? Illustrate your answer with a diagram or description. [10 Punkte]

TEIL B: PRAKTISCHE AUFGABEN (60 Punkte)

Q5. You are given a dataset with 10,000 samples and 50 features for predicting 
house prices in Linz.
   a) Which regression algorithm would you choose and why?
   b) How would you handle missing values in the dataset?
   c) Describe your cross-validation strategy
   d) What evaluation metrics would you use?

--- END OF EXAM ---
Viel Erfolg!
"""
# agent = PatternLearner()
# result = agent.learn_patterns(sample_exam_text[100:200])
# output = result['response']
# print (output)

class SubPart(BaseModel):
    letter : str 
    number : str

class ExtractedQuestion(BaseModel):
    question_number : str
    question_text : str 
    marks : Optional[int] = None
    sub_parts : List[SubPart] = []
    raw_block : Optional[str] = None

class RegexPatterns(BaseModel):
    model_config = ConfigDict(extra="allow")
    main_question : str 
    marks :str 
    sub_question : str 

    
  

class Observations(BaseModel):
    model_config = ConfigDict(extra="allow")
    question_format : str 
    marks_format : str 
    subparts_format : str 

    
class TestExamples(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    what_matches: List[str] = []
    edge_cases: List[str] = []

class PatternLearning(BaseModel):
    model_config = ConfigDict(extra="allow")
    observations: Observations
    regex_patterns: RegexPatterns
    test_examples: TestExamples

    @field_validator('regex_patterns', mode='before')
    @classmethod
    def validate_regex(cls, v):
        """Validate that regex patterns are valid"""
        if isinstance(v, dict):
            for key, pattern in v.items():
                try:
                    re.compile(pattern)
                except re.error as e:
                    print(f"Warning: Invalid regex for {key}: {pattern} - {e}")
        return v
llm_output = {
    "observations": {
        "question_format": "Questions are numbered using uppercase letters (NG) followed by a space and lowercase letters (final exam).",
        "marks_format": "Marks are indicated as 'Punkte' followed by the total points in numerals.",
        "subparts_format": "Sub-parts are not explicitly defined in this sample, but they might be identified by indentation or specific keywords."
    },
    "regex_patterns": {
        "main_question": "^[A-Z]+ [a-z]+ [A-Z]+",
        "marks": "Punkte \\d+",
        "sub_question": "(?s)(?:\\n\\t| )[a-z]+\\s*\\d+"
    },
    "test_examples": {
        "what_matches": ["A1 Punkte 20", "\tB3 Punkte 30"],
        "edge_cases": ["NG Prüfungsdauer: 120 Minuten Gesamtpunkte: 100"]
    }
}
def fix_regex_escapes(json_string: str) -> str:
    fixed = json_string.replace('\\', '\\\\')
    return fixed

# Parse it with Pydantic
try:
    # Fix the escapes first
    fixed_output = fix_regex_escapes(output)
    
    # Then parse
    data = json.loads(fixed_output)
    parsed = PatternLearning(**data)
    
    print("Successfully parsed!")
    print(f"Main question pattern: {parsed.regex_patterns.main_question}")
    
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    print(f"Position {e.pos}: ...{output[max(0, e.pos-50):e.pos+50]}...")
except Exception as e:
    print(f"Error: {e}")
