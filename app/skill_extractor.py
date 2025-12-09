"""
THE EYES. This file scans resumes to find skills like 'Python', 'Tally', or 'Leadership'.
"""

import re
from typing import List, Set

import spacy


class SkillExtractor:
    def __init__(self):
        """Initialize spaCy and compile regex patterns for known skills."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback: run without spaCy if the model is missing
            print("Warning: spaCy model not found. Using Regex only.")
            self.nlp = None

        # Comprehensive list of technical skills
        self.skill_patterns: Set[str] = {
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C++",
            "C#",
            "Go",
            "Rust",
            "HTML",
            "CSS",
            "React",
            "Angular",
            "Vue.js",
            "Next.js",
            "Node.js",
            "Django",
            "Flask",
            "FastAPI",
            "Spring",
            "ASP.NET",
            "SQL",
            "MySQL",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "Oracle",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "Kubernetes",
            "Jenkins",
            "Git",
            "Machine Learning",
            "Deep Learning",
            "TensorFlow",
            "PyTorch",
            "Pandas",
            "NumPy",
            "Linux",
            "Agile",
            "Scrum",
            "DevOps",
            "CI/CD",
            "REST API",
            "GraphQL",
        }

        # Pre-compile a single regex for fast matching
        self.skill_regex = re.compile(
            r"\b(?:"
            + "|".join(re.escape(skill) for skill in self.skill_patterns)
            + r")\b",
            re.IGNORECASE,
        )

    def extract(self, text: str) -> List[str]:
        """Extract a sorted list of unique skills from arbitrary text."""
        if not text or not text.strip():
            return []

        found_skills: Set[str] = set()

        # 1. Regex Match (fast, deterministic)
        matches = self.skill_regex.findall(text)
        for match in matches:
            found_skills.add(self._normalize_skill(match))

        # 2. spaCy NER (contextual, best-effort)
        if self.nlp:
            try:
                doc = self.nlp(text)
                tech_keywords = ["experience", "proficient", "using", "developer"]
                for ent in doc.ents:
                    if ent.label_ in ["ORG", "PRODUCT"]:
                        window_start = max(0, ent.start_char - 30)
                        window_end = min(len(text), ent.end_char + 30)
                        context = text[window_start:window_end].lower()
                        if any(k in context for k in tech_keywords):
                            norm = self._normalize_skill(ent.text)
                            if norm in self.skill_patterns:
                                found_skills.add(norm)
            except Exception:
                # NER is best-effort only; ignore errors
                pass

        return sorted(found_skills)

    def _normalize_skill(self, skill: str) -> str:
        """Normalize variations like 'react.js' -> 'React'."""
        skill = skill.strip().replace(".js", "").replace(".JS", "")
        for pattern in self.skill_patterns:
            if pattern.lower() == skill.lower():
                return pattern
        return skill.title()


# Convenience global instance used by the rest of the app
skill_extractor = SkillExtractor()


