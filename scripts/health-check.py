import json
from urllib.request import urlopen
from urllib.error import URLError

SERVICES = {
    "backend": "http://localhost:8000/health",
    "ai-service": "http://localhost:8001/health",
    "mock-sap": "http://localhost:8002/health",
}

for name, url in SERVICES.items():
    try:
        with urlopen(url, timeout=3) as response:
            payload = json.loads(response.read().decode())
            print(f"[OK] {name}: {payload}")
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
