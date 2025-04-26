from openai import OpenAI
import os
import json
import re
import logging
from typing import List, Dict, Any

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vulnerability-scanner")

class VulnerabilityScanner:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        
        # CRITICAL FIX: Initialize OpenAI client with ONLY the API key
        try:
            self.client = OpenAI(api_key=api_key)  # No other parameters!
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise

        self.vulnerability_patterns = {
            "sql_injection": [
                r"execute\(\s*[\'\"]SELECT.*\+.*[\'\"]",
                r"cursor\.execute\([^,]*\+[^,]*\)",
            ],
            "xss": [
                r"innerHTML\s*=",
                r"document\.write\(.*\)",
            ],
            "command_injection": [
                r"exec\(\s*[\'\"]*.*\+.*[\'\"]",
                r"os\.system\([^,]*\+[^,]*\)",
            ],
            "buffer_overflow": [
                r"\bgets\s*\(",
                r"\bstrcpy\s*\(",
                r"\bstrcat\s*\(",
                r"\bsprintf\s*\(",
                r"\bscanf\s*\(\s*\"%s\""
            ],
        }

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        logger.info(f"Scanning file: {file_path}")

        if not os.path.isfile(file_path):
            return {"error": f"File does not exist: {file_path}"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    code = f.read()
            except Exception as e:
                return {"error": f"Error reading file: {str(e)}"}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}

        pattern_results = self._detect_patterns(code)
        llm_results = self._analyze_with_llm(code, pattern_results)

        return {
            "file_path": file_path,
            "pattern_results": pattern_results,
            "llm_results": llm_results,
            "recommendations": self._generate_recommendations(llm_results)
        }

    def _detect_patterns(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        for vuln_type, patterns in self.vulnerability_patterns.items():
            matches = []
            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    line_number = code[:match.start()].count('\n') + 1
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(code), match.end() + 50)
                    matches.append({
                        "pattern": pattern,
                        "match": match.group(0),
                        "line": line_number,
                        "context": code[context_start:context_end]
                    })
            if matches:
                results[vuln_type] = matches
        return results

    def _analyze_with_llm(self, code: str, pattern_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        code_excerpt = code[:10000] + "... [truncated]" if len(code) > 10000 else code

        pattern_info = ""
        if pattern_results:
            pattern_info = "Initial pattern matching found these potential issues:\n"
            for vuln_type, matches in pattern_results.items():
                pattern_info += f"- {vuln_type}: {len(matches)} matches\n"
                for i, match in enumerate(matches[:3]):
                    pattern_info += f"  - Match {i+1} on line {match['line']}: {match['match']}\n"
                if len(matches) > 3:
                    pattern_info += f"  - ... and {len(matches) - 3} more matches\n"

        prompt = f"""
        Analyze this code for security vulnerabilities:

        
{code_excerpt}


        {pattern_info}

        Identify potential vulnerabilities including:
        - SQL Injection
        - Buffer Overflow
        - Cross-site scripting (XSS)
        - Command Injection
        - Path Traversal
        - Insecure Deserialization
        - Weak Cryptography
        - Hardcoded Credentials
        - Race Conditions

        Output ONLY raw JSON with fields:
        vulnerabilities, risk_score, analysis_confidence, summary.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            logger.info(f"Raw LLM response:\n{content}")
            
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                content = content.strip()
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        json_content = content[json_start:json_end]
                        result = json.loads(json_content)
                        return result
                    except:
                        pass
                        
                # If JSON extraction fails, return a fallback
                return {
                    "vulnerabilities": [],
                    "risk_score": 0,
                    "analysis_confidence": 0,
                    "summary": "Failed to parse LLM response as JSON. Raw response: " + content[:100] + "..."
                }

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return {"error": f"LLM analysis failed: {str(e)}"}

    def _generate_recommendations(self, llm_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "error" in llm_results or "vulnerabilities" not in llm_results:
            return []

        recommendations = []
        for vuln in llm_results["vulnerabilities"]:
            vuln_type = vuln.get("type", "unknown")

            if vuln_type == "sql_injection":
                recommendations.append({
                    "vulnerability_type": vuln_type,
                    "recommendation": "Use parameterized queries or prepared statements.",
                    "code_example": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                    "resources": [
                        "https://owasp.org/www-community/attacks/SQL_Injection",
                        "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
                    ]
                })
            elif vuln_type == "xss":
                recommendations.append({
                    "vulnerability_type": vuln_type,
                    "recommendation": "Use output encoding or a templating engine with automatic escaping.",
                    "code_example": "element.textContent = userProvidedData;",
                    "resources": [
                        "https://owasp.org/www-community/attacks/xss/",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
                    ]
                })
            elif vuln_type == "command_injection":
                recommendations.append({
                    "vulnerability_type": vuln_type,
                    "recommendation": "Use subprocess with shell=False instead of os.system.",
                    "code_example": "subprocess.run(['ls', '-l'], shell=False)",
                    "resources": [
                        "https://owasp.org/www-community/attacks/Command_Injection",
                        "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
                    ]
                })
            # More recommendations as needed...

        return recommendations