import os
import unittest
from app.services.parser_service import ParserService

class TestParserService(unittest.TestCase):
    def test_clean_text(self):
        dirty = "  Hello \x00 world! \t \n\n\n\n Test  "
        cleaned = ParserService.clean_text(dirty)
        self.assertEqual(cleaned, "Hello world! \n\n Test")

    def test_extract_heuristic_metadata(self):
        text = "Contact: john.doe@techcorp.io or phone +1-555-123-4567. GitHub: https://github.com/johndoe"
        meta = ParserService.extract_heuristic_metadata(text)
        self.assertEqual(meta["email"], "john.doe@techcorp.io")
        self.assertIn("555", meta["phone"])
        self.assertIn("github.com/johndoe", meta["github"])

    def test_parse_docx(self):
        sample_path = "sample_data/resumes/alex_senior_ai.docx"
        if os.path.exists(sample_path):
            text, ftype = ParserService.extract_text(sample_path)
            self.assertEqual(ftype, "docx")
            self.assertIn("Alex Mercer", text)

    def test_parse_pdf(self):
        sample_path = "sample_data/resumes/sam_fullstack.pdf"
        if os.path.exists(sample_path):
            text, ftype = ParserService.extract_text(sample_path)
            self.assertEqual(ftype, "pdf")
            self.assertIn("Samantha Hayes", text)

if __name__ == "__main__":
    unittest.main()

