import json
import os
from flask import Flask, render_template_string, request, redirect, url_for
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- CONFIGURATION & PERSISTANCE ---
DB_FILE = 'database.json'

def init_db():
    if not os.path.exists(DB_FILE):
        initial_data = [{"id": 1, "nom": "MINKO", "prenom": "Marc", "filiere": "Génie Info", "date": "2026-04-24"}]
        with open(DB_FILE, 'w') as f:
            json.dump(initial_data, f)

def get_students():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_students(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

# --- MÉTRIQUES PROMETHEUS ---
STUDENT_COUNT = Gauge('inptic_student_current_total', 'Nombre total d\'étudiants')
ACTIONS_TOTAL = Counter('inptic_actions_total', 'Interactions utilisateur', ['type'])

# Initialisation des métriques au démarrage
init_db()
STUDENT_COUNT.set(len(get_students()))

# --- DESIGN PREMIUM ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>INPTIC | Système de Gestion Intégré</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --p: #1e293b; --s: #3b82f6; --acc: #10b981; --danger: #ef4444; --warn: #f59e0b; --bg: #f8fafc; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { background: var(--bg); display: flex; height: 100vh; color: var(--p); }
        
        /* Navigation */
        .sidebar { width: 280px; background: var(--p); color: white; padding: 30px 20px; display: flex; flex-direction: column; }
        .sidebar h2 { color: var(--s); margin-bottom: 40px; font-size: 1.5rem; display: flex; align-items: center; gap: 10px; }
        .nav-link { color: #94a3b8; text-decoration: none; padding: 12px; border-radius: 8px; display: flex; align-items: center; gap: 12px; transition: 0.3s; }
        .nav-link:hover, .nav-link.active { background: #334155; color: white; }
        
        /* Main Content */
        .main { flex: 1; padding: 40px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        
        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .stat-card { display: flex; align-items: center; gap: 20px; border-bottom: 4px solid var(--s); }
        .stat-val { font-size: 1.8rem; font-weight: bold; }
        
        /* Form & Table */
        .form-section { display: flex; gap: 15px; margin-bottom: 25px; background: white; padding: 20px; border-radius: 12px; align-items: flex-end; }
        .form-group { flex: 1; display: flex; flex-direction: column; gap: 5px; }
        input, select { padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; outline: none; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: 0.2s; display: flex; align-items: center; gap: 8px; color: white; text-decoration: none; }
        .btn-add { background: var(--s); }
        .btn-update { background: var(--warn); }
        .btn-del { background: var(--danger); padding: 8px; }
        
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }
        th { background: #f1f5f9; padding: 15px; text-align: left; font-size: 0.8rem; color: #64748b; text-transform: uppercase; }
        td { padding: 15px; border-bottom: 1px solid #f1f5f9; }
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; background: #e0f2fe; color: var(--s); }
        
        /* Search Bar */
        .search-box { position: relative; margin-bottom: 20px; }
        .search-box i { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
        .search-box input { width: 100%; padding-left: 45px; background: white; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2><i class="fas fa-microchip"></i> INPTIC v4</h2>
        <nav style="display: flex; flex-direction: column; gap: 10px;">
            <a href="/" class="nav-link active"><i class="fas fa-th-large"></i> Dashboard</a>
            <a href="/metrics" target="_blank" class="nav-link"><i class="fas fa-chart-line"></i> Métriques Live</a>
        </nav>
        <div style="margin-top: auto; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;">
            <p style="font-size: 0.8rem; color: #94a3b8;">Status Monitoring</p>
            <div style="display: flex; align-items: center; gap: 8px; margin-top: 5px;">
                <div style="width: 10px; height: 10px; background: var(--acc); border-radius: 50%;"></div>
                <span style="font-size: 0.9rem;">Prometheus Ready</span>
            </div>
        </div>
    </div>

    <div class="main">
        <div class="header">
            <h1>Administration Étudiants</h1>
            <div style="color: #64748b;">Connecté en tant que <strong>Marc Minko</strong></div>
        </div>

        <div class="stats-grid">
            <div class="card stat-card">
                <i class="fas fa-users" style="font-size: 2.5rem; color: var(--s);"></i>
                <div><h3>Effectif Total</h3><p class="stat-val">{{ count }}</p></div>
            </div>
            <div class="card stat-card" style="border-color: var(--acc);">
                <i class="fas fa-graduation-cap" style="font-size: 2.5rem; color: var(--acc);"></i>
                <div><h3>Réussite (Sim)</h3><p class="stat-val">94%</p></div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 30px;">
            <h3 style="margin-bottom: 20px;"><i class="fas {{ 'fa-user-edit' if edit_student else 'fa-user-plus' }}"></i> 
                {{ 'Modifier les informations' if edit_student else 'Ajouter un nouvel inscrit' }}</h3>
            <form action="/save" method="post" class="form-section">
                <input type="hidden" name="id" value="{{ edit_student.id if edit_student else '' }}">
                <div class="form-group">
                    <label>Nom</label>
                    <input type="text" name="nom" value="{{ edit_student.nom if edit_student else '' }}" required placeholder="Ex: NDONG">
                </div>
                <div class="form-group">
                    <label>Prénom</label>
                    <input type="text" name="prenom" value="{{ edit_student.prenom if edit_student else '' }}" required placeholder="Ex: Jean">
                </div>
                <div class="form-group">
                    <label>Filière</label>
                    <select name="filiere">
                        <option value="Génie Info" {{ 'selected' if edit_student and edit_student.filiere == 'Génie Info' }}>Génie Informatique</option>
                        <option value="Cyber" {{ 'selected' if edit_student and edit_student.filiere == 'Cyber' }}>Cybersécurité</option>
                        <option value="Réseaux" {{ 'selected' if edit_student and edit_student.filiere == 'Réseaux' }}>Réseaux & Télécoms</option>
                    </select>
                </div>
                <button type="submit" class="btn {{ 'btn-update' if edit_student else 'btn-add' }}">
                    <i class="fas {{ 'fa-sync' if edit_student else 'fa-save' }}"></i>
                    {{ 'Mettre à jour' if edit_student else 'Enregistrer' }}
                </button>
            </form>
        </div>

        <div class="search-box">
            <i class="fas fa-search"></i>
            <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Rechercher un étudiant par nom...">
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Nom & Prénom</th><th>Filière</th><th style="text-align: right;">Actions</th>
                </tr>
            </thead>
            <tbody id="studentTable">
                {% for s in students %}
                <tr>
                    <td><span style="color: #94a3b8;">#{{ s.id }}</span></td>
                    <td><strong>{{ s.nom }}</strong> {{ s.prenom }}</td>
                    <td><span class="badge">{{ s.filiere }}</span></td>
                    <td style="text-align: right; display: flex; justify-content: flex-end; gap: 10px;">
                        <a href="/edit/{{ s.id }}" class="btn" style="background: #f1f5f9; color: #475569; padding: 8px;"><i class="fas fa-pen"></i></a>
                        <form action="/delete/{{ s.id }}" method="post" style="display:inline;">
                            <button class="btn btn-del"><i class="fas fa-trash"></i></button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
    function filterTable() {
        let input = document.getElementById("searchInput");
        let filter = input.value.toUpperCase();
        let tr = document.getElementById("studentTable").getElementsByTagName("tr");
        for (let i = 0; i < tr.length; i++) {
            let td = tr[i].getElementsByTagName("td")[1];
            if (td) {
                let textValue = td.textContent || td.innerText;
                tr[i].style.display = textValue.toUpperCase().indexOf(filter) > -1 ? "" : "none";
            }
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
    nom = request.form.get('nom').upper()
    prenom = request.form.get('prenom').capitalize()
    fil = request.form.get('filiere')

    if uid: # UPDATE
        for s in db:
            if s['id'] == int(uid):
                s.update({"nom": nom, "prenom": prenom, "filiere": fil})
        ACTIONS_TOTAL.labels(type='modification').inc()
    else: # CREATE
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
