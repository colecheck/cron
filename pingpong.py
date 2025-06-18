import requests
import yaml
import os

def load_numbers():
    path = os.path.join(os.path.dirname(__file__), "numbers.yml")
    with open(path, "r") as f:
        return yaml.safe_load(f)

def main():
    config = load_numbers()
    url = "http://157.230.81.198:3000/wapp-web/ping-whatsapp"
    for persona in config["personas"]:
        telefono = persona["telefono"]
        payload = {"phoneNumber": telefono}
        resp = requests.post(url, json=payload)
        print(f"Enviado a {telefono}: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    main()