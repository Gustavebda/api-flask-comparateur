from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://forfaitmoinscher.com", "https://www.forfaitmoinscher.com"], supports_credentials=True)

@app.after_request
def add_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin") if request.headers.get("Origin") in ["http://localhost:5173", "https://forfaitmoinscher.com", "https://www.forfaitmoinscher.com"] else "http://localhost:5173"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

def get_forfaits():
    conn = sqlite3.connect('forfaits.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM forfaits")
    forfaits = cursor.fetchall()
    conn.close()

    forfaits_list = []
    for forfait in forfaits:
        print("📡 Données brutes de la base :", forfait)  # Debug SQL
        
        forfaits_list.append({
            "id": forfait[0],
            "operateur": forfait[1],
            "nom": forfait[2],
            "prix": float(forfait[3]) if forfait[3] else 0.0,
            "data": forfait[4],  # ✅ Garder la valeur brute
            "data_etranger": forfait[5],
            "appels": forfait[6],
            "sms": forfait[7],
            "engagement": forfait[8],
            "reseau": forfait[9] if forfait[9] else "",
            "options": forfait[10].split(",") if forfait[10] else [],
            "cible": forfait[11],
            "url": forfait[12],
            "suisse": forfait[13] if forfait[13] else "",
            "techno": forfait[14] if forfait[14] else ""
        })

    print(f"📡 {len(forfaits_list)} forfaits récupérés avant filtrage.")  # ✅ Vérifier combien de forfaits sont disponibles
    return forfaits_list

@app.route('/comparateur', methods=['GET', 'OPTIONS'])
def comparer_forfaits():
    if request.method == 'OPTIONS':
        return '', 204  # ✅ Réponse rapide pour les requêtes préliminaires

    try:
        budget_max = int(request.args.get('budget_max', 100))
        data_min = int(request.args.get('data_min', 0))
        engagement = request.args.get('engagement', "Sans engagement")
        reseau_pref = request.args.getlist('reseau_pref')
        cible = request.args.get('cible', None)
        only_5g = request.args.get('only_5g', 'false').lower() == 'true'
        only_suisse = request.args.get('only_suisse', 'false').lower() == 'true'

        print(f"🔍 Requête reçue avec : budget_max={budget_max}, data_min={data_min}, engagement={engagement}, reseau_pref={reseau_pref}, cible={cible}, only_5g={only_5g}, only_suisse={only_suisse}")

        forfaits = get_forfaits()
        print(f"📊 {len(forfaits)} forfaits avant filtrage")

        resultats = []
        for f in forfaits:
            # ✅ Extraction correcte du nombre de Go/Mo
            try:
                data_value = float(f['data'].replace("Go", "").replace("Mo", "").strip())  # ✅ Extrait uniquement le nombre
            except ValueError:
                data_value = 0.0  # ✅ Sécuriser si une valeur est mal formatée

            print(f"🔍 Forfait : {f['nom']} | Data : {f['data']} (extrait : {data_value}) | Prix : {f['prix']} | Réseau : {f['reseau']}")

            # ✅ Appliquer les filtres progressivement
            if (
                f['prix'] <= budget_max and
                data_value >= data_min and
                (engagement == "Sans engagement" or f['engagement'] == engagement) and
                (not reseau_pref or f['reseau'] in reseau_pref) and
                (not only_5g or (f['techno'].strip().lower() == "5g")) and
                (not only_suisse or (f['suisse'].strip().lower() == "oui"))
            ):
                resultats.append(f)

        print(f"✅ {len(resultats)} forfaits trouvés après filtrage.")

        return jsonify(sorted(resultats, key=lambda x: x['prix']))

    except Exception as e:
        print(f"❌ ERREUR : {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
