import re
import os
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

class ParserService:
    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, str]:
        """
        Extract raw text from PDF or DOCX file.
        Returns: (extracted_text, file_type)
        """
        path = Path(file_path)
        ext = path.suffix.lower().replace(".", "")

        if ext == "pdf":
            text = ParserService._extract_from_pdf(file_path)
            return ParserService.clean_text(text), "pdf"
        elif ext in ["docx", "doc"]:
            text = ParserService._extract_from_docx(file_path)
            return ParserService.clean_text(text), "docx"
        elif ext in ["txt", "md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            return ParserService.clean_text(text), ext
        else:
            raise ValueError(f"Unsupported file format: {ext}. Only PDF, DOCX, and TXT are supported.")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        text_parts = []
        # Try pypdf first
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception:
            text_parts = []

        # If pypdf extracted very little or failed, try pdfplumber
        if len("".join(text_parts).strip()) < 50:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            except Exception:
                pass

        return "\n".join(text_parts)

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        text_parts.append(" | ".join(row_text))
            return "\n".join(text_parts)
        except Exception as e:
            raise RuntimeError(f"Failed to read DOCX file: {str(e)}")

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalize whitespace, strip non-printable characters, preserve bullet structures.
        """
        if not text:
            return ""
        # Remove null bytes
        text = text.replace("\x00", " ")
        # Replace multiple horizontal spaces with single space
        text = re.sub(r"[ \t]+", " ", text)
        # Replace multiple newlines with at most two newlines
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    @staticmethod
    def extract_heuristic_metadata(text: str) -> Dict[str, Any]:
        """
        Quick regex-based extraction of email, phone, and links for fallback / verification.
        """
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        github_pattern = r'(?:https?:\/\/)?(?:www\.)?github\.com\/[A-Za-z0-9_.-]+'
        linkedin_pattern = r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/(?:in|pub)\/[A-Za-z0-9_.-]+'

        email_match = re.search(email_pattern, text)
        phone_match = re.search(phone_pattern, text)
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)

        return {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "github": github_match.group(0) if github_match else "",
            "linkedin": linkedin_match.group(0) if linkedin_match else ""
        }

