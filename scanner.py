import os
import json
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI

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
        self.client = OpenAI(api_key=self.api_key)
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
            logger.error(f"File does not exist: {file_path}")
            return {"error": f"File does not exist: {file_path}"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {"error": f"Error reading file: {str(e)}"}

        pattern_results = self._detect_patterns(code)
        llm_results = self._analyze_with_llm(code, pattern_results)

        return {
            "file_path": file_path,
            "pattern_results": pattern_results,
            "llm_results": llm_results,
            "recommendations": self._generate_recommendations(llm_results)
        }

    def scan_directory(self, directory_path: str, file_extensions: List[str] = None) -> List[Dict[str, Any]]:
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.php', '.java', '.cs', '.go', '.c', '.cpp']

        results = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)
                    results.append(self.scan_file(file_path))
        return results

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

        ```
        {code_excerpt}
        ```

        {pattern_info}

        Identify potential security vulnerabilities including but not limited to:
        - SQL injection
        - Buffer Overflow
        - Cross-site scripting (XSS)
        - Command injection
        - Insecure deserialization
        - Weak cryptography
        - Hardcoded credentials
        - Race conditions
        - Path traversal

        Format your response ONLY as raw JSON, without explanation or formatting. Do NOT include Markdown or code blocks.

        JSON fields:
        - vulnerabilities: [Array of identified vulnerabilities with type, severity, line_numbers, and description]
        - risk_score: Overall risk score from 1-10
        - analysis_confidence: Confidence in analysis from 1-10
        - summary: Brief textual summary of findings
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
            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from LLM response: {str(e)}")
            return {
                "error": "Failed to parse LLM response",
                "raw_response": content
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

        return recommendations


def main():
    parser = argparse.ArgumentParser(description="Automated Vulnerability Scanning Tool")
    parser.add_argument("--path", required=True, help="Path to file or directory to scan")
    parser.add_argument("--api-key", help="OpenAI API key (or leave blank to use openai_config.json)")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--output", default="scan_results.json", help="Output file for results")
    parser.add_argument("--extensions", default=".py,.js,.php,.java,.cs,.go,.c,.cpp", help="Comma-separated list of file extensions to scan")  # ✅ Added .c and .cpp
    args = parser.parse_args()

    api_key = args.api_key
    if not api_key:
        try:
            with open("openai_config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("api_key")
        except Exception as e:
            logger.error(f"No API key provided and failed to load openai_config.json: {e}")
            return

    scanner = VulnerabilityScanner(api_key, args.model)
    path = Path(args.path)

    if path.is_file():
        results = [scanner.scan_file(str(path))]
    elif path.is_dir():
        extensions = args.extensions.split(",")
        results = scanner.scan_directory(str(path), extensions)
    else:
        logger.error(f"Path does not exist: {args.path}")
        return

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Scan complete. Results written to {args.output}")

    total_vulnerabilities = sum(
        len(r.get("llm_results", {}).get("vulnerabilities", []))
        for r in results if "error" not in r
    )

    print(f"\nScan Summary:")
    print(f"Files scanned: {len(results)}")
    print(f"Vulnerabilities found: {total_vulnerabilities}")
    print(f"Full results saved to: {args.output}")


if __name__ == "__main__":
    main()
