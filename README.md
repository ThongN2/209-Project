# Automated Vulnerability Scanner Web App


---

## Prerequisites

- **Backend**: Python 3.8+ and `pip`
- **Frontend**: Node.js 14+ and `npm` or `yarn`

---

## Backend Setup

1. **Enter the backend folder**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate    # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your OpenAI key**
   - Copy the example config:
     ```bash
     cp openai_config.json.example openai_config.json
     ```
   - Edit `openai_config.json` and insert your OpenAI API key.

5. **Run the scanner**
   ```bash
   python app.py 
   ```


## Frontend Setup

1. **Enter the frontend folder**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install     # or `yarn install`
   ```

3. **Start in development**
   ```bash
   npm start       # opens http://localhost:3000
   ```



