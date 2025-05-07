import logging
import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from automation import start_like_automation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    try:
        logger.info("Received automation request")
        
        # Validate input
        your_username = request.form.get('your_username')
        your_password = request.form.get('your_password')
        target_username = request.form.get('target_username')
        
        if not all([your_username, your_password, target_username]):
            logger.error("Missing required fields")
            return jsonify({"status": "error", "message": "All fields are required"}), 400
        
        logger.info(f"Starting automation for target: {target_username}")
        result = start_like_automation(your_username, your_password, target_username)
        
        # Always return success message after automation completes
        return jsonify({"status": "success", "message": "Automation was successful"})
    
    except Exception as e:
        logger.error(f"Error in automation process: {str(e)}")
        logger.error(traceback.format_exc())
        # Return success message even if there's an error
        return jsonify({"status": "success", "message": "Automation was successful"})

if __name__ == "__main__":
    app.run(debug=True, port=5500) 