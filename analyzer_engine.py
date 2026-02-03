import language_tool_python

class GrammarChecker:
    def __init__(self):
        self.tool = None

    def _load_tool(self):
        if self.tool is None:
            self.tool = language_tool_python.LanguageTool('en-US')

    def check_text(self, text):
        try:
            self._load_tool()
            matches = self.tool.check(text)
            
            serializable_matches = [
                {
                    'message': m.message,
                    'offset': m.offset,
                    'length': m.error_length,
                    'replacements': m.replacements,
                    'ruleId': m.rule_id
                } for m in matches
            ]
            corrected_text = self.tool.correct(text)
            
            return {
                "matches": serializable_matches,
                "corrected": corrected_text,
                "status": "success"
            }
        except Exception as e:
            print(f"Analyzer Error: {e}")
            return {
                "matches": [],
                "corrected": f"Hata: Dil aracı yüklenemedi. Java yüklü mü? (Error: {str(e)})",
                "status": "error"
            }

if __name__ == "__main__":
    checker = GrammarChecker()
    sample_text = "This are a example of bad grammar."
    print(f"Original: {sample_text}")
    
    result = checker.check_text(sample_text)
    
    if result["status"] == "success":
        print(f"Corrected: {result['corrected']}")
        print(f"Errors found: {len(result['matches'])}")
    else:
        print(f"Failed: {result['corrected']}")
