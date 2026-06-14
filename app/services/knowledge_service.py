import os
import logging

logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self, base_path: str = "app/knowledge_base"):
        self.base_path = base_path

    def search(self, query: str) -> str:
        query_words = query.lower().split()
        results = []
        if not os.path.exists(self.base_path):
            logger.error(f"Knowledge base directory not found: {self.base_path}")
            return ""
        for filename in os.listdir(self.base_path):
            filepath = os.path.join(self.base_path, filename)
            if not os.path.isfile(filepath) or not filename.endswith(".txt"):
                continue
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if any(word in content.lower() for word in query_words):
                    results.append(content.strip())
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
        return "\n".join(results) if results else ""

knowledge_service = KnowledgeService()