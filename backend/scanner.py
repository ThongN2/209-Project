from openai import OpenAI
import os
import json
import re
import logging
from typing import List, Dict, Any
from rag_loader import retrieve_extra_explanation

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vulnerability-scanner")

class VulnerabilityScanner:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        try:
            self.client = OpenAI(api_key=api_key)
            self.model = model
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

        self.vulnerability_patterns = {
            "sql_injection": [
                r"execute\(\s*[\'\"](SELECT|INSERT|UPDATE|DELETE).*?\+.*?[\'\"]",
                r"cursor\.execute\(([^,\)]*?\+[^,\)]*?)\)",
            ],
            "xss": [
                r"innerHTML\s*=\s*([^\n;]*?)",
                r"document\.write\([^\n;]*?\)",
            ],
            "command_injection": [
                r"exec\(\s*[\'\"]*.*?\+.*?[\'\"]",
                r"os\.system\([^\n;]*?\+[^\n;]*?\)",
            ],
            "buffer_overflow": [
                r"\bgets\s*\([^\n;]*?\)",
                r"\bstrcpy\s*\([^\n;]*?\)",
                r"\bstrcat\s*\([^\n;]*?\)",
                r"\bsprintf\s*\([^\n;]*?\)",
                r"\bscanf\s*\(\s\"%s\"[^\n;]*?\)",
            ],
            "path_traversal": [
                r"open\(\s*['\"](?:[^'\"]*?\\/)*[^'\"]*?\"\s*\+\s*[^\n;]*?\)",
                r"os\.path\.join\([^\n;]*?user_input[^\n;]*?\)",
            ],
            "insecure_deserialization": [
                r"pickle\.loads\([^\n;]*?\)",
                r"yaml\.load\([^\n;]*?\)",
                r"eval\([^\n;]*?\)",
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
            with open(file_path, 'r', encoding='latin-1') as f:
                code = f.read()

        pattern_results = self._detect_patterns(code)
        llm_results = self._analyze_with_llm(code, pattern_results)
        vulnerabilities = llm_results.get("vulnerabilities", [])

        return {
            "file_path": file_path,
            "pattern_results": pattern_results,
            "llm_results": llm_results,
            "recommendations": self._generate_recommendations(llm_results),
            "brief_summary": self._generate_brief_summary(file_path, vulnerabilities)
        }

    def _detect_patterns(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        results: Dict[str, List[Dict[str, Any]]] = {}
        for vuln_type, patterns in self.vulnerability_patterns.items():
            matches: List[Dict[str, Any]] = []
            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    line_number = code[:match.start()].count('\n') + 1
                    line_start = code.rfind('\n', 0, match.start()) + 1
                    line_end = code.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(code)
                    context_start = max(0, code.rfind('\n', 0, line_start - 100) + 1)
                    context_end = code.find('\n', line_end + 1, line_end + 200)
                    if context_end == -1:
                        context_end = len(code)

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
                    pattern_info += f"  - Match {i+1} (line {match['line']}): {match['match']}\n"
                if len(matches) > 3:
                    pattern_info += f"  - ... and {len(matches) - 3} more\n"

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
vulnerabilities: [{{"type": "vulnerability_type", "description": "description", "location": "line_number or function_name", "severity": "high/medium/low"}}],
risk_score: 0-100,
analysis_confidence: 0-100,
summary: "brief overview of findings".
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            content = response.choices[0].message.content
            logger.info(f"Raw LLM response:\n{content}")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                content = content.strip()
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        return json.loads(content[json_start:json_end])
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON content: {content[json_start:json_end]}")
                return {"vulnerabilities": [], "risk_score": 0, "analysis_confidence": 0, "summary": "Failed to parse LLM response as JSON."}
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return {"error": f"LLM analysis failed: {e}"}

    def _generate_recommendations(self, llm_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "error" in llm_results or "vulnerabilities" not in llm_results:
            return []

        recommendations: List[Dict[str, Any]] = []
        for vuln in llm_results.get("vulnerabilities", []):
            raw_type = vuln.get("type", "").lower()
            if "sql injection" in raw_type:
                key = "sql_injection"
            elif "xss" in raw_type:
                key = "xss"
            elif "command injection" in raw_type:
                key = "command_injection"
            elif "path traversal" in raw_type:
                key = "path_traversal"
            elif "deserialization" in raw_type:
                key = "insecure_deserialization"
            elif "buffer overflow" in raw_type:
                key = "buffer_overflow"
            else:
                key = raw_type.replace(" ", "_")

            rec = {
                "vulnerability_type": vuln.get("type", key),
                "recommendation": "",
                "code_example": "",
                "resources": [],
                "severity": vuln.get("severity", "medium"),
                "extra_explanation": retrieve_extra_explanation(key)
            }

            if key == "sql_injection":
                rec.update({
                    "recommendation": "Use parameterized queries.",
                    "code_example": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                    "resources": [
                        "https://owasp.org/www-community/attacks/SQL_Injection",
                        "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
                    ]
                })
            elif key == "xss":
                rec.update({
                    "recommendation": "Use output encoding or templating with automatic escaping.",
                    "code_example": "element.textContent = userProvidedData;",
                    "resources": [
                        "https://owasp.org/www-community/attacks/xss/",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
                    ]
                })
            elif key == "command_injection":
                rec.update({
                    "recommendation": "Use subprocess with shell=False.",
                    "code_example": "subprocess.run(['ls', '-l'], shell=False)",
                    "resources": [
                        "https://owasp.org/www-community/attacks/Command_Injection",
                        "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
                    ]
                })
            elif key == "path_traversal":
                rec.update({
                    "recommendation": "Validate paths and use os.path.normpath and os.path.abspath.",
                    "code_example": "# sanitize and validate file path...",
                    "resources": [
                        "https://owasp.org/www-community/attacks/Path_Traversal",
                        "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html"
                    ]
                })
            elif key == "insecure_deserialization":
                rec.update({
                    "recommendation": "Avoid pickle for untrusted data; use JSON instead.",
                    "code_example": "import json\nobj = json.loads(data)",
                    "resources": [
                        "https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html"
                    ]
                })
            elif key == "buffer_overflow":
                rec.update({
                    "recommendation": "Use safe functions with bounds checking.",
                    "code_example": "strncpy(dest, src, sizeof(dest)-1); dest[sizeof(dest)-1]='\\0';",
                    "resources": [
                        "https://owasp.org/www-community/vulnerabilities/Buffer_Overflow",
                        "https://cwe.mitre.org/data/definitions/120.html"
                    ]
                })

            recommendations.append(rec)

        return recommendations
    

    def _generate_brief_summary(self, file_path: str, vulnerabilities: List[Dict[str, Any]]) -> str:
        if not vulnerabilities:
            return f"The file `{os.path.basename(file_path)}` appears clean with no major vulnerabilities detected."
        
        summary_parts = []
        for vuln in vulnerabilities:
            vuln_type = vuln.get("type", "Unknown Vulnerability")
            location = vuln.get("location", "Unknown Location")
            severity = vuln.get("severity", "medium").capitalize()
            description = vuln.get("description", "No detailed description available.")
            
            summary = (
                f"The file `{os.path.basename(file_path)}` contains a **{severity} severity {vuln_type}** "
                f"located at {location}. {description}"
            )
            summary_parts.append(summary)
        
        return " ".join(summary_parts)
    
    def _deeper_llm_analysis(self, code: str) -> Dict[str, Any]:
        """
        Perform a deeper, second-level LLM analysis on the uploaded code.
        This returns a professional security report in Markdown.
        """
        prompt = f"""
You are a cybersecurity expert. Perform a deep security audit of the following code.

Analyze and explain:
- Rare and advanced security vulnerabilities
- Insecure design patterns
- Hardcoded secrets or sensitive information
- Unsafe programming practices
- Real-world attack scenarios and exploitation risks
- Best practice improvements and recommendations

Generate a professional and detailed security report in **Markdown** format.

Code:
{code}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            content = response.choices[0].message.content
            return {"deep_analysis": content}
        except Exception as e:
            logger.error(f"Deep LLM analysis failed: {e}")
            return {"error": str(e)}
