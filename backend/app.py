from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import traceback
from scanner import VulnerabilityScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler()]
)
logger = logging.getLogger("vulnerability-scanner-server")

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'.py', '.js', '.php', '.java', '.cs', '.go', '.c', '.cpp', '.rb', '.ts'}

# Load OpenAI API Key
def load_api_key():
    config_path = os.path.join(os.path.dirname(__file__), "openai_config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            api_key = config.get("api_key")
            if not api_key:
                logger.warning("API key missing in openai_config.json.")
                return None
            return api_key
    except Exception as e:
        logger.error(f"Error loading API key: {str(e)}")
        return None

OPENAI_API_KEY = load_api_key()
if OPENAI_API_KEY:
    logger.info("API key loaded successfully")
else:
    logger.warning("No API key loaded. Scanner will not work correctly.")

def allowed_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"status": "ok", "message": "Backend server running"})

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if not OPENAI_API_KEY:
            return jsonify({"error": "Server misconfigured. API key missing."}), 500

        if 'file' not in request.files:
            return jsonify({"error": "No file part in request."}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected."}), 400

        if not allowed_file(file.filename):
            return jsonify({
                "error": "Unsupported file type.",
                "message": f"Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        logger.info(f"File uploaded: {file_path}")

        scanner = VulnerabilityScanner(api_key=OPENAI_API_KEY)
        result = scanner.scan_file(file_path)

        os.remove(file_path)  # Clean up
        return jsonify(result)

    except Exception as e:
        logger.error(f"Unhandled exception during upload: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/deep_analysis", methods=["POST"])
def deep_analysis():
    try:
        data = request.json
        code = data.get("code")
        if not code:
            return jsonify({"error": "No code provided."}), 400

        logger.info("Performing deeper LLM analysis...")
        scanner = VulnerabilityScanner(api_key=OPENAI_API_KEY)
        result = scanner._deeper_llm_analysis(code)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error during deep analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
