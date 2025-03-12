from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://forfaitmoinscher.com"], 
     supports_credentials=True, allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

@app.after_request
def apply_cors(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Access-Control-Allow-Origin"] = "https://forfaitmoinscher.com"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response  # ✅ Ne pas jsonify(response), c'est déjà une réponse HTTP !

def get_forfaits():
    conn = sqlite3.connect('forfaits.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM forfaits")

    forfaits_list = []
    for forfait in cursor.fetchall():
        forfaits_list.append({
            "id": forfait[0],
            "nom": forfait[1],
            "reseau": forfait[2],
            "prix": float(forfait[3]) if forfait[3] else 0.0,
            "data": forfait[4],
            "data_etranger": forfait[5],
            "appels": forfait[6],
            "sms": forfait[7],
            "engagement": forfait[8],
            "data_etranger": forfait[5],
            "techno": forfait[14] if forfait[14] else ""
        })
    conn.close()
    return forfaits_list


@app.route('/comparateur', methods=['GET', 'OPTIONS'])
def comparer_forfaits():
    try:
        budget_max = float(request.args.get('budget_max', 999))
        data_min = float(request.args.get('data_min', 0))
        engagement = request.args.get('engagement', "Sans engagement")
        reseau_pref = request.args.getlist('reseau_pref')   
        cible = request.args.get('cible', None)
        only_5g = request.args.get('only_5g', 'false').lower() == 'true'

        forfaits = get_forfaits()

        resultats = [f for f in forfaits if
                     f["prix"] <= float(budget_max) and
                     float(f['data'].replace("Go", "").replace("Mo", "").strip()) >= float(data_min) and
                     (engagement == "Sans engagement" or f['engagement'] == engagement) and
                     (not reseau_pref or f['reseau'] in reseau_pref) and
                     (not only_5g or f['techno'] == "5G")]

        resultats = sorted(resultats, key=lambda x: x['prix'])

        return jsonify(resultats)

    except Exception as e:
        print(f"❌ ERREUR : {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
