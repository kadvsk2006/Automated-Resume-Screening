"""
Text preprocessing utilities for cleaning noisy resume and JD text
before skill extraction and other NLP steps.
"""

import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    @staticmethod
    def preprocess(text: Optional[str]) -> str:
        """
        Aggressively clean up raw text by normalizing Unicode artifacts,
        removing problematic characters, and standardizing whitespace.

        This is especially useful for PDF-extracted text that may contain
        characters like Â, \\xa0, and irregular spacing, which can break
        regex-based skill extraction.
        """
        if not text:
            return ""

        # 1. Normalize Unicode to NFKD (decomposes characters)
        text = unicodedata.normalize("NFKD", text)

        # 2. Encode to ASCII and decode back (strips hidden non-ascii chars)
        text = text.encode("ascii", "ignore").decode("utf-8")

        # 3. Replace non-breaking spaces and tabs with space
        text = text.replace("\xa0", " ").replace("\t", " ")

        # 4. Remove all non-alphanumeric characters EXCEPT common punctuation
        #    (keep . + # - so that tokens like "C++", "C#", and "Tally." remain usable)
        text = re.sub(r"[^a-zA-Z0-9\s\.\+\#\-]", " ", text)

        # 5. Collapse multiple spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text.lower()


