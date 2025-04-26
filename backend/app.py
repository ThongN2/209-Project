from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vulnerability-scanner-server")

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.py', '.js', '.php', '.java', '.cs', '.go', '.c', '.cpp', '.rb', '.ts'}

# Load OpenAI API Key
def load_api_key():
    config_path = os.path.join(os.path.dirname(__file__), "openai_config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            api_key = config.get("api_key")
            if not api_key:
                logger.warning("API key is missing in openai_config.json.")
                return None
            return api_key
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        return None
    except Exception as e:
        logger.error(f"Failed to load OpenAI API key: {str(e)}")
        return None

# Try to load API key but don't stop server if missing
OPENAI_API_KEY = load_api_key()
if OPENAI_API_KEY:
    logger.info("API key loaded successfully")
else:
    logger.warning("No API key loaded. Scanner will not work correctly.")

# Helper to validate file type
def allowed_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.route("/test", methods=["GET"])
def test():
    """Simple test endpoint to verify server is working"""
    return jsonify({"status": "ok", "message": "Backend server is running"})

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload and scanning"""
    try:
        logger.info("Upload request received")
        
        # Check if API key is available
        if not OPENAI_API_KEY:
            logger.error("API key missing when trying to process upload")
            return jsonify({
                "error": "Server misconfigured. API key missing.",
                "details": "Create an openai_config.json file with your API key"
            }), 500

        # Check if file is in the request
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            return jsonify({"error": "No file part in the request."}), 400

        file = request.files['file']
        logger.info(f"File received: {file.filename}")

        # Check if filename is empty
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({"error": "No file selected."}), 400

        # Check if file type is allowed
        if not allowed_file(file.filename):
            logger.warning(f"Unsupported file type: {file.filename}")
            return jsonify({
                "error": "Unsupported file type.",
                "message": f"Supported file types are: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        try:
            file.save(file_path)
            logger.info(f"File saved: {file_path}")
            
            # Create scanner and scan the file
            from scanner import VulnerabilityScanner
            scanner = VulnerabilityScanner(api_key=OPENAI_API_KEY)
            logger.info(f"Starting scan for file: {file.filename}")
            scan_result = scanner.scan_file(file_path)
            logger.info(f"Scan completed for file: {file.filename}")

            # Clean up the uploaded file after scanning
            os.remove(file_path)
            logger.info(f"File removed after scan: {file_path}")

            return jsonify(scan_result)

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File removed after error: {file_path}")
            
            logger.error(f"Server error during upload/scan: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Internal server error", 
                "message": str(e),
                "traceback": traceback.format_exc()
            }), 500

    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "Unhandled server error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    status = "✅ Vulnerability Scanner Backend is Running"
    api_status = "✅ API Key Loaded" if OPENAI_API_KEY else "❌ API Key Missing"
    
    return jsonify({
        "status": status,
        "api_status": api_status,
        "version": "1.1.0",
        "supported_extensions": list(ALLOWED_EXTENSIONS)
    })

@app.route("/status", methods=["GET"])
def detailed_status():
    """Detailed status endpoint for monitoring"""
    return jsonify({
        "server": "running",
        "api_key_loaded": OPENAI_API_KEY is not None,
        "upload_folder": os.path.abspath(UPLOAD_FOLDER),
        "supported_file_types": list(ALLOWED_EXTENSIONS),
        "version": "1.1.0"
    })

if __name__ == "__main__":
    logger.info("Starting vulnerability scanner server")
    app.run(host="0.0.0.0", port=5000, debug=True)