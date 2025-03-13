from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "https://forfaitmoinscher.com", "https://www.forfaitmoinscher.com"],
                             "supports_credentials": True,
                             "allow_headers": ["Content-Type", "Authorization"],
                             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

@app.after_request
def apply_cors(response):
    origin = request.headers.get("Origin")
    allowed_origins = ["http://localhost:5173", "https://forfaitmoinscher.com", "https://www.forfaitmoinscher.com"]

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Cache-Control"] = "no-store"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

def get_forfaits():
    try:
        conn = sqlite3.connect('forfaits.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM forfaits")

        forfaits_list = []
        for forfait in cursor.fetchall():
            print("📡 Données brutes de la base :", forfait)  # 🔍 Vérification des données SQL
            
            operateur = forfait[2] if forfait[2] else "Inconnu"
            reseau = forfait[3] if forfait[3] else "Inconnu"
            engagement = forfait[9] if forfait[9] else "Sans engagement"
            techno = forfait[14] if forfait[14] else ""

            forfaits_list.append({
                "id": forfait[0],
                "nom": forfait[1],
                "operateur": operateur,
                "reseau": reseau,
                "prix": float(forfait[4]) if forfait[4] else 0.0,
                "data": forfait[5] if forfait[5] else "0 Mo",  # ✅ Récupération brute
                "data_etranger": forfait[6] if forfait[6] else "0 Mo",
                "appels": forfait[7],
                "sms": forfait[8],
                "engagement": engagement,
                "techno": techno
            })

        conn.close()
        print(f"📡 {len(forfaits_list)} forfaits récupérés avant filtrage :", forfaits_list)  # ✅ Vérifie si des forfaits existent
        return forfaits_list

    except Exception as e:
        print(f"❌ ERREUR dans get_forfaits : {str(e)}")
        return []

@app.route('/comparateur', methods=['GET', 'OPTIONS'])
def comparer_forfaits():
    try:
        budget_max = float(request.args.get('budget_max', 999))
        data_min = float(request.args.get('data_min', 0))
        engagement = request.args.get('engagement', "Sans engagement")
        reseau_pref = request.args.getlist('reseau_pref')
        only_5g = request.args.get('only_5g', 'false').lower() == 'true'

        forfaits = get_forfaits()

        resultats = [f for f in forfaits if
                     f["prix"] <= budget_max and
                     float(re.sub(r'[^\d.]', '', f["data"])) >= data_min and  # ✅ Correction
                     (engagement == "Sans engagement" or f['engagement'] == engagement) and
                     (not reseau_pref or f['reseau'] in reseau_pref) and
                     (not only_5g or f['techno'] == "5G")]

        resultats = sorted(resultats, key=lambda x: x['prix'])

        print(f"✅ {len(resultats)} forfaits trouvés après filtrage.")
        return jsonify(resultats)

    except Exception as e:
        print(f"❌ ERREUR dans comparer_forfaits : {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)