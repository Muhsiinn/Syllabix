from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, List, Optional
import ollama
from pydantic import BaseModel
import asyncio
from dataclasses import dataclass
import re
import json
router = APIRouter()


class QuestionPattern(BaseModel):
    pattern_type: str  
    regex_pattern: str
    example_matches: List[str]
    confidence: float
    metadata: Dict 

class PatternLearner:

    def __init__(self,model = 'mistral:7b-instruct') :
        self.model = model 

    def learn_patterns(self,query:str):

        prompt = f"""
You are a pattern recognition expert for exam papers. Analyze this sample text and identify the structural patterns used for questions.

SAMPLE TEXT:
{query}

TASK:
1. Identify how questions are numbered/formatted (e.g., "Q1.", "1)", "Question 1:", etc.)
2. Identify how marks are indicated (e.g., "[5 marks]", "(10)", "Marks: 5")
3. Identify question type markers (MCQ options like a), b), c) or multi-part questions like a., b., c.)
4. Return regex patterns that can extract these reliably

IMPORTANT: The regex must work for ALL questions in this format, not just the samples you see.

Return ONLY valid JSON in this exact format:
{{
  "patterns": [
    {{
      "pattern_type": "main_question",
      "regex_pattern": "Q\\d+\\.\\s+(.+?)(?=Q\\d+\\.|$)",
      "description": "Matches Q1. Q2. format",
      "example_matches": ["Q1. What is AI?", "Q2. Explain ML"],
      "confidence": 0.95
    }},
    {{
      "pattern_type": "marks",
      "regex_pattern": "\\[(\\d+)\\s*marks?\\]",
      "description": "Matches [5 marks] or [5 mark]",
      "example_matches": ["[5 marks]", "[10 marks]"],
      "confidence": 0.90
    }},
    {{
      "pattern_type": "sub_question",
      "regex_pattern": "[a-z]\\)\\s+(.+?)(?=[a-z]\\)|$)",
      "description": "Matches a) b) c) format for sub-questions",
      "example_matches": ["a) Define supervised learning", "b) Explain the concept"],
      "confidence": 0.85
    }}
  ],
  "document_structure": {{
    "has_subsections": true,
    "section_markers": ["Section A", "Section B"],
    "total_questions_estimate": 10,
    "question_numbering_system": "numeric"
  }}
}}

Do not include any explanatory text, ONLY the JSON.
"""

        response = ollama.generate(
            model=self.model,
            prompt=prompt,
            stream= False,
            options={
                "temperature": 0.1,  # Low temp for consistent patterns
                "num_predict": 3000
            }
        )
        return response


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
agent = PatternLearner()
result = agent.learn_patterns(sample_exam_text[100:200])
output = result['response']
print (output)


