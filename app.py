import json
import os
from flask import Flask, render_template_string, request, redirect, url_for
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- PERSISTANCE ---
DB_FILE = 'database.json'

def init_db():
    if not os.path.exists(DB_FILE):
        # On initialise avec une liste vide au lieu de l'étudiant par défaut
        initial_data = [] 
        with open(DB_FILE, 'w') as f:
            json.dump(initial_data, f)

def get_students():
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_students(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

# --- MÉTRIQUES ---
STUDENT_COUNT = Gauge('inptic_student_current_total', 'Total étudiants')
ACTIONS_TOTAL = Counter('inptic_actions_total', 'Interactions', ['type'])

init_db()
STUDENT_COUNT.set(len(get_students()))

# --- UI DESIGN (Mélange de ta capture + Dashboard Pro) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>INPTIC OS | Management</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --p: #1e293b; --s: #3b82f6; --acc: #10b981; --danger: #ef4444; --warn: #f59e0b; --bg: #f1f5f9; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 260px; background: var(--p); color: white; padding: 30px 20px; }
        .sidebar h2 { color: var(--s); margin-bottom: 40px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .nav-link { color: #94a3b8; text-decoration: none; padding: 12px; display: block; border-radius: 8px; margin-bottom: 5px; }
        .nav-link.active { background: #334155; color: white; }

        .main { flex: 1; padding: 30px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }

        /* Quick Action Cards (Comme sur ton image) */
        .quick-actions { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .action-card { background: white; padding: 25px; border-radius: 16px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: 0.3s; }
        .action-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .icon-box { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px; font-size: 1.2rem; }

        /* Form & Table */
        .glass-card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .input-group { display: flex; gap: 15px; margin-top: 15px; }
        input, select { padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; flex: 1; outline: none; }
        .btn { padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; color: white; display: flex; align-items: center; gap: 8px; }
        
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 15px; background: #f8fafc; color: #64748b; font-size: 0.8rem; text-transform: uppercase; }
        td { padding: 15px; border-bottom: 1px solid #f1f5f9; }
        .badge { background: #e0f2fe; color: var(--s); padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
        
        .status-bar { background: white; padding: 15px; border-radius: 12px; display: flex; align-items: center; gap: 10px; margin-bottom: 25px; border-left: 5px solid var(--acc); }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>INPTIC OS</h2>
        <a href="/" class="nav-link active"><i class="fas fa-home"></i> Dashboard</a>
        <a href="/metrics" target="_blank" class="nav-link"><i class="fas fa-chart-bar"></i> Métriques</a>
    </div>

    <div class="main">
        <div class="header">
            <h1>Gestion des Étudiants</h1>
            <div style="font-size: 0.9rem; color: #64748b;">Bienvenue, <strong>Minko Marc</strong></div>
        </div>

        <div class="quick-actions">
            <div class="action-card">
                <div class="icon-box" style="background: #ecfdf5; color: var(--acc);"><i class="fas fa-user-plus"></i></div>
                <p style="font-weight: 600;">{{ count }} Étudiants</p>
            </div>
            <div class="action-card">
                <div class="icon-box" style="background: #eff6ff; color: var(--s);"><i class="fas fa-search"></i></div>
                <p style="font-weight: 600;">Consulter</p>
            </div>
            <div class="action-card">
                <div class="icon-box" style="background: #fffbeb; color: var(--warn);"><i class="fas fa-sync"></i></div>
                <p style="font-weight: 600;">Mettre à jour</p>
            </div>
            <div class="action-card">
                <div class="icon-box" style="background: #fef2f2; color: var(--danger);"><i class="fas fa-trash"></i></div>
                <p style="font-weight: 600;">Supprimer</p>
            </div>
        </div>

        <div class="status-bar">
            <div style="width: 12px; height: 12px; background: var(--acc); border-radius: 50%;"></div>
            <span style="font-size: 0.9rem;">Système de Monitoring Prometheus Actif sur le port 9091</span>
        </div>

        <div class="glass-card">
            <h3><i class="fas fa-edit"></i> {{ 'Modification' if edit_student else 'Enregistrement' }}</h3>
            <form action="/save" method="post" class="input-group">
                <input type="hidden" name="id" value="{{ edit_student.id if edit_student else '' }}">
                <input type="text" name="nom" placeholder="NOM" value="{{ edit_student.nom if edit_student else '' }}" required>
                <input type="text" name="prenom" placeholder="Prénom" value="{{ edit_student.prenom if edit_student else '' }}" required>
                <select name="filiere">
                    <option value="Génie Info" {{ 'selected' if edit_student and edit_student.filiere == 'Génie Info' }}>Génie Informatique</option>
                    <option value="Cyber" {{ 'selected' if edit_student and edit_student.filiere == 'Cyber' }}>Cybersécurité</option>
                </select>
                <button type="submit" class="btn" style="background: {{ 'var(--warn)' if edit_student else 'var(--s)' }}">
                    <i class="fas fa-save"></i> {{ 'Valider' if edit_student else 'Ajouter' }}
                </button>
            </form>
        </div>

        <div class="glass-card">
            <input type="text" id="srch" onkeyup="filter()" placeholder="Rechercher un nom..." style="width:100%; margin-bottom:15px; padding:10px; border-radius:8px; border:1px solid #ddd;">
            <table id="tbl">
                <thead><tr><th>ID</th><th>Nom Complet</th><th>Filière</th><th style="text-align:right">Actions</th></tr></thead>
                <tbody>
                    {% for s in students %}
                    <tr>
                        <td>#{{ s.id }}</td>
                        <td><strong>{{ s.nom }}</strong> {{ s.prenom }}</td>
                        <td><span class="badge">{{ s.filiere }}</span></td>
                        <td style="text-align:right">
                            <a href="/edit/{{ s.id }}" style="color:var(--warn); margin-right:15px;"><i class="fas fa-pen"></i></a>
                            <form action="/delete/{{ s.id }}" method="post" style="display:inline;">
                                <button style="border:none; background:none; color:var(--danger); cursor:pointer;"><i class="fas fa-trash"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function filter() {
            let val = document.getElementById("srch").value.toUpperCase();
            let rows = document.getElementById("tbl").getElementsByTagName("tr");
            for (let i = 1; i < rows.length; i++) {
                rows[i].style.display = rows[i].innerText.toUpperCase().includes(val) ? "" : "none";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    db = get_students()
    return render_template_string(HTML_TEMPLATE, students=db, count=len(db), edit_student=None)

@app.route('/edit/<int:uid>')
def edit(uid):
    db = get_students()
    target = next((s for s in db if s['id'] == uid), None)
    return render_template_string(HTML_TEMPLATE, students=db, count=len(db), edit_student=target)

@app.route('/save', methods=['POST'])
def save():
    db = get_students()
    uid = request.form.get('id')
    nom, prenom, fil = request.form.get('nom').upper(), request.form.get('prenom'), request.form.get('filiere')
    if uid:
        for s in db:
            if s['id'] == int(uid): s.update({"nom": nom, "prenom": prenom, "filiere": fil})
        ACTIONS_TOTAL.labels(type='modification').inc()
    else:
        new_id = max([s['id'] for s in db]) + 1 if db else 1
        db.append({"id": new_id, "nom": nom, "prenom": prenom, "filiere": fil})
        ACTIONS_TOTAL.labels(type='inscription').inc()
    save_students(db)
    STUDENT_COUNT.set(len(db))
    return redirect(url_for('home'))

@app.route('/delete/<int:uid>', methods=['POST'])
def delete(uid):
    db = get_students()
    db = [s for s in db if s['id'] != uid]
    save_students(db)
    STUDENT_COUNT.set(len(db))
    ACTIONS_TOTAL.labels(type='suppression').inc()
    return redirect(url_for('home'))

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
# Cache-bust: lun. 27 avril 2026 07:17:40 CEST
