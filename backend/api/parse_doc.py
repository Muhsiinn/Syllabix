"""
Document parsing module for extracting structured questions from exam documents.

This module provides classes and utilities to:
- Learn regex patterns from exam text using LLMs
- Parse exam documents into structured questions
- Extract question metadata (marks, sub-parts, etc.)
"""

from fastapi import APIRouter
from typing import List, Optional
import ollama
from pydantic import BaseModel, field_validator, ConfigDict
import re
import json

router = APIRouter()


class PatternLearner:
    """
    Uses an LLM to analyze exam text and learn regex patterns for parsing.

    Attributes:
        model: The Ollama model to use for pattern learning
    """

    def __init__(self, model: str = 'mistral:7b-instruct'):
        """
        Initialize the PatternLearner.

        Args:
            model: The Ollama model name to use (default: 'mistral:7b-instruct')
        """
        self.model = model

    def learn_patterns(self, query: str) -> dict:
        """
        Analyze exam text and generate regex patterns for parsing.

        Args:
            query: The exam text to analyze

        Returns:
            Dictionary containing the LLM response with learned patterns
        """
        prompt = f"""Analyze this exam and create regex patterns.

EXAM TEXT:
{query}

STEP 1: Look at the text and find examples.

STEP 2: Create regex patterns.

CRITICAL: You are outputting JSON as text. In JSON strings, backslashes must be escaped.
- For regex \\d, write: \\\\d (two backslashes)
- For regex \\., write: \\\\. (two backslashes)
- For regex \\s, write: \\\\s (two backslashes)

Examples:
- To match "Q1." write: "Q\\\\d+\\\\."
- To match "[8 Punkte]" write: "\\\\[\\\\d+ Punkte\\\\]"
- To match "   a)" write: "\\\\s+[a-z]\\\\)"

Output this JSON:
{{
  "observations": {{
    "question_format": "Questions use Q1., Q2., Q3.",
    "marks_format": "Marks shown as [8 Punkte]",
    "subparts_format": "Sub-parts are a), b), c)"
  }},
  "regex_patterns": {{
    "main_question": "Q\\\\d+\\\\.",
    "marks": "\\\\[\\\\d+ Punkte\\\\]",
    "sub_question": "\\\\s+[a-z]\\\\)"
  }},
  "test_examples": {{
    "what_matches": ["Q1.", "Q2."],
    "edge_cases": []
  }}
}}

Return ONLY valid JSON.
"""

        response = ollama.generate(
            model=self.model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.1,
                "num_predict": 3000
            }
        )
        return response


class SubPart(BaseModel):
    """Represents a sub-part of a question (e.g., a), b), c))."""
    letter: str
    text: str

class ExtractedQuestion(BaseModel):
    """Represents a parsed exam question with all its components."""
    question_number: str
    question_text: str
    marks: Optional[int] = None
    sub_parts: List[SubPart] = []
    raw_block: Optional[str] = None


class RegexPatterns(BaseModel):
    """Regex patterns learned for parsing exam questions."""
    model_config = ConfigDict(extra="allow")
    main_question: str
    marks: str
    sub_question: str


class Observations(BaseModel):
    """Observations about the exam format."""
    model_config = ConfigDict(extra="allow")
    question_format: str
    marks_format: str
    subparts_format: str


class TestExamples(BaseModel):
    """Test examples for validating regex patterns."""
    model_config = ConfigDict(extra="allow")
    what_matches: List[str] = []
    edge_cases: List[str] = []


class PatternLearning(BaseModel):
    """Complete pattern learning result with observations, patterns, and examples."""
    model_config = ConfigDict(extra="allow")
    observations: Observations
    regex_patterns: RegexPatterns
    test_examples: TestExamples

    @field_validator('regex_patterns', mode='before')
    @classmethod
    def validate_regex(cls, v):
        """Validate that regex patterns are valid."""
        if isinstance(v, dict):
            for key, pattern in v.items():
                try:
                    re.compile(pattern)
                except re.error as e:
                    pass
        return v


def parse_pattern_response(response_text: str) -> PatternLearning:
    """
    Parse LLM response into PatternLearning object.

    Args:
        response_text: Raw text response from the LLM

    Returns:
        PatternLearning object

    Raises:
        json.JSONDecodeError: If response is not valid JSON
        ValueError: If response doesn't match expected schema
    """
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)

    data = json.loads(response_text)
    return PatternLearning(**data)

class QuestionParser:
    """
    Parses exam text into structured questions using learned regex patterns.

    Attributes:
        patterns: The regex patterns to use for parsing
        observations: Observations about the exam format
    """

    def __init__(self, pattern_result: PatternLearning):
        """
        Initialize the QuestionParser.

        Args:
            pattern_result: PatternLearning object containing regex patterns
        """
        self.patterns = pattern_result.regex_patterns
        self.observations = pattern_result.observations

    def parse_questions(self, exam_text: str, verbose: bool = False) -> List[ExtractedQuestion]:
        """
        Parse exam text into structured questions.

        Args:
            exam_text: The full exam text to parse
            verbose: Whether to print debug information

        Returns:
            List of ExtractedQuestion objects
        """
        questions = []

        main_q_pattern = self.patterns.main_question
        marks_pattern = self.patterns.marks
        sub_q_pattern = self.patterns.sub_question

        if verbose:
            print(f'Using main pattern: {main_q_pattern}')
            print(f'Using marks pattern: {marks_pattern}')
            print(f'Using sub-question pattern: {sub_q_pattern}')

        main_matches = list(re.finditer(main_q_pattern, exam_text, re.MULTILINE))

        if not main_matches:
            if verbose:
                print("No main questions found")
            return questions

        if verbose:
            print(f"Found {len(main_matches)} questions")

        for i, q_match in enumerate(main_matches):
            q_start = q_match.start()
            q_end = main_matches[i + 1].start() if i + 1 < len(main_matches) else len(exam_text)
            question_block = exam_text[q_start:q_end]
            q_number = q_match.group(0).strip()

            if verbose:
                print(f"Parsing {q_number} (block length: {len(question_block)} chars)")

            marks = self._extract_marks(question_block, marks_pattern, verbose)
            sub_parts = self._extract_subparts(question_block, sub_q_pattern, verbose)
            main_text = self._extract_main_text(
                question_block,
                q_match.group(0),
                marks_pattern,
                sub_parts
            )

            question = ExtractedQuestion(
                question_number=q_number,
                question_text=main_text,
                marks=marks,
                sub_parts=sub_parts,
                raw_block=question_block
            )

            questions.append(question)

        return questions

    def _extract_marks(self, text: str, marks_pattern: str, verbose: bool = False) -> Optional[int]:
        """
        Extract marks/points from question text.

        Args:
            text: The question text
            marks_pattern: Regex pattern for marks
            verbose: Whether to print debug information

        Returns:
            The number of marks, or None if not found
        """
        if not marks_pattern or marks_pattern == ".*":
            return None

        try:
            marks_match = re.search(marks_pattern, text)
            if marks_match:
                numbers = re.findall(r'\d+', marks_match.group(0))
                if numbers:
                    marks_value = int(numbers[0])
                    if verbose:
                        print(f"  Marks: {marks_value}")
                    return marks_value
        except Exception:
            pass

        return None

    def _extract_subparts(self, text: str, sub_pattern: str, verbose: bool = False) -> List[SubPart]:
        """
        Extract sub-parts (a, b, c, etc.) from question text.

        Args:
            text: The question text
            sub_pattern: Regex pattern for sub-parts
            verbose: Whether to print debug information

        Returns:
            List of SubPart objects
        """
        if not sub_pattern or sub_pattern == ".*":
            return []

        sub_parts = []

        try:
            sub_matches = list(re.finditer(sub_pattern, text, re.MULTILINE))

            for j, sub_match in enumerate(sub_matches):
                sub_identifier = sub_match.group(0).strip()
                sub_start = sub_match.end()
                sub_end = sub_matches[j + 1].start() if j + 1 < len(sub_matches) else len(text)

                sub_text = text[sub_start:sub_end].strip()
                sub_text = ' '.join(sub_text.split())

                sub_parts.append(SubPart(
                    letter=sub_identifier,
                    text=sub_text
                ))

            if verbose and sub_parts:
                print(f"  Sub-parts: {len(sub_parts)}")

        except Exception:
            pass

        return sub_parts

    def _extract_main_text(
        self,
        block: str,
        q_marker: str,
        marks_pattern: str,
        sub_parts: List[SubPart]
    ) -> str:
        """
        Extract the main question text, excluding marks and sub-parts.

        Args:
            block: The full question block
            q_marker: The question number marker (e.g., "Q1.")
            marks_pattern: Regex pattern for marks
            sub_parts: List of sub-parts already extracted

        Returns:
            The cleaned main question text
        """
        text = block[len(q_marker):].strip()

        if sub_parts:
            first_sub = sub_parts[0].letter
            sub_pos = block.find(first_sub)
            if sub_pos != -1:
                text = block[len(q_marker):sub_pos].strip()

        if marks_pattern and marks_pattern != ".*":
            text = re.sub(marks_pattern, '', text)

        text = ' '.join(text.split())

        return text


SAMPLE_EXAM_TEXT = """
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


def main():
    """Example usage of the parsing functionality."""
    print("Learning patterns from sample exam...")
    agent = PatternLearner()
    result = agent.learn_patterns(SAMPLE_EXAM_TEXT[:2000])
    output = result['response']

    print("_" * 80)
    print(output)
    print("_" * 80)

    try:
        parsed = parse_pattern_response(output)
        print("\nSuccessfully parsed patterns!")
        print(f"Main question pattern: {parsed.regex_patterns.main_question}")
        print(f"Sub question pattern: {parsed.regex_patterns.sub_question}")

        print("\nParsing questions...")
        parser = QuestionParser(parsed)
        questions = parser.parse_questions(SAMPLE_EXAM_TEXT, verbose=True)

        print(f"\nExtracted {len(questions)} questions")
        print(questions)
        for q in questions:
            print(f"\n{q.question_number}: {q.question_text}...")
            if q.marks:
                print(f"  Marks: {q.marks}")
            if q.sub_parts:
                print(f"  Sub-parts: {q.sub_parts}")

    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        print(f"Position {e.pos}: ...{output[max(0, e.pos-50):e.pos+50]}...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
