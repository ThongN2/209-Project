

### Set Up a Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---


### Example `openai_config.json`:
```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

You can get your API key from [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)


##  Usage

### Scan a Single File
```bash
python scanner.py --path testing/test_sql_injection.py
```

### Scan an Entire Folder
```bash
python scanner.py --path ./testing
```

---




