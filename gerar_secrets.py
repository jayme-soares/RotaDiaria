import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(SCRIPT_DIR, "credenciais.json")

with open(CREDS_FILE, "r") as f:
    creds_json = json.load(f)

creds_raw = json.dumps(creds_json, indent=2)

print('password = "wwcQ5Zt4"')
print('gsheet_id = "1E4dZIrznKyKbd-zFDjpKtbCnyDaNXGFGyCU_YQx-dfU"')
print('gsheet_credentials = """')
print(creds_raw)
print('"""')
