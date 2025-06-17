import requests
import yaml
from collections import defaultdict
from datetime import date
import json

def load_config(path="config.yml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_json(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()



def send_report(backend_url, data):
    resp = requests.post(backend_url, json=data)
    print(f"Enviado a {data['destinatario']['telefono']}: {resp.status_code} {resp.text}")

def build_report(level, grades, sections_by_grade, summary):
    reporte = {}
    for grade in grades:
        grade_name = grade["name"]
        reporte[grade_name] = {}
        for section in sections_by_grade[grade["id"]]:
            section_name = section["name"]
            section_id = section["id"]
            presentes = sum(1 for a in summary[level["id"]][grade["id"]][section_id] if a["state"] == "Presente")
            total = len(summary[level["id"]][grade["id"]][section_id])
            reporte[grade_name][section_name] = {"asistencia": presentes, "total": total}
    return reporte

def main():
    config = load_config()
    base_url = config["base_url"]
    today = config.get("date") or str(date.today())

    for school in config["schools"]:
        school_slug = school["slug"]
        print(f"\n=== Colegio: {school['name']} ({school_slug}) ===")

        # 1. Obtener niveles
        levels = get_json(f"{base_url}/{school_slug}/levels/")
        grades_by_level = {}
        for level in levels:
            grades = get_json(f"{base_url}/{school_slug}/level/{level['id']}/grades/")
            grades_by_level[level["id"]] = grades

        sections_by_grade = {}
        for level_id, grades in grades_by_level.items():
            for grade in grades:
                sections = get_json(f"{base_url}/{school_slug}/level/{level_id}/grade/{grade['id']}/sections/")
                sections_by_grade[grade["id"]] = sections

        assistances = get_json(f"{base_url}/{school_slug}/general-assistances/details/{today}/")

        # Agrupar por nivel, grado y sección
        summary = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for a in assistances:
            student = a["student"]
            level_id = student["level"]
            grade_id = student["grade"]
            section_id = student["section"]
            summary[level_id][grade_id][section_id].append(a)

        # Para cada nivel (ej: Primaria, Secundaria)
        for level in levels:
            nivel_key = "primaria" if "primaria" in school["recipients"] and level["name"].lower().startswith("prim") else "secundaria"
            grades = grades_by_level[level["id"]]
            reporte = build_report(level, grades, sections_by_grade, summary)

            # Para cada rol y persona
            for rol in ["profesores", "auxiliares"]:
                for persona in school["recipients"].get(nivel_key, {}).get(rol, []):
                    if nivel_key in persona.get("recibe", []):
                        data = {
                            "colegio": school["name"],
                            "nivel": nivel_key,
                            "reporte": reporte,
                            "destinatario": {
                                "nombre": persona["nombre"],
                                "telefono": persona["telefono"],
                                "email": persona["email"],
                                "rol": rol[:-1],
                                "recibe": persona.get("recibe", [])
                            }
                        }
                        #print(json.dumps(data, ensure_ascii=False, indent=2))
                        send_report(config["backend_url"], data)
                        
            # Directores
            for director in school["recipients"].get("directores", []):
                if nivel_key in director.get("recibe", []):
                    data = {
                        "colegio": school["name"],
                        "nivel": nivel_key,
                        "reporte": reporte,
                        "destinatario": {
                            "nombre": director["nombre"],
                            "telefono": director["telefono"],
                            "email": director["email"],
                            "rol": "director",
                            "recibe": director.get("recibe", [])
                        }
                    }
                    #print(json.dumps(data, ensure_ascii=False, indent=2))
                    send_report(config["backend_url"], data)

if __name__ == "__main__":
    main()
