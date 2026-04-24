from flask import Flask, render_template_string, request, redirect, url_for
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- MÉTRIQUES ---
STUDENT_COUNT = Gauge('inptic_student_current_total', 'Nombre total d\'étudiants')
ACTIONS_TOTAL = Counter('inptic_actions_total', 'Interactions', ['type'])

# --- DATA ---
students_db = [{"id": 1, "nom": "MINKO", "prenom": "Marc", "filiere": "Génie Info"}]
next_id = 2
STUDENT_COUNT.set(len(students_db))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>INPTIC | Management System v3</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --p: #0f172a; --s: #3b82f6; --acc: #10b981; --danger: #ef4444; }
        body { font-family: 'Inter', sans-serif; background: #f8fafc; margin: 0; display: flex; height: 100vh; color: #1e293b; }
        .sidebar { width: 280px; background: var(--p); color: white; padding: 30px 20px; }
        .main { flex: 1; padding: 40px; overflow-y: auto; }
        .glass-card { background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #e2e8f0; margin-bottom: 30px; }
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        input, select { padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; flex: 1; min-width: 150px; }
        .btn { padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; color: white; transition: 0.2s; display: inline-flex; align-items: center; gap: 8px; }
        .btn-add { background: var(--s); }
        .btn-update { background: #f59e0b; }
        .btn-del { background: var(--danger); }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }
        th { background: #f1f5f9; padding: 15px; text-align: left; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
        td { padding: 15px; border-bottom: 1px solid #f1f5f9; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-box { background: var(--s); color: white; padding: 15px 25px; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="color: var(--s)">INPTIC <span style="color:white">DEV</span></h2>
        <p style="opacity: 0.6; font-size: 0.8rem; margin-bottom: 40px;">Infrastructure Monitoring & CI/CD</p>
        <div class="stat-box">
            <small>Effectif Étudiant</small>
            <h1 style="margin:0">{{ count }}</h1>
        </div>
    </div>
    <div class="main">
        <h1>Dashboard Administration</h1>
        
        <div class="glass-card">
            <h3><i class="fas fa-user-edit"></i> Enregistrement / Modification</h3>
            <form action="/save" method="post" class="input-group">
                <input type="hidden" name="id" value="{{ edit_student.id if edit_student else '' }}">
                <input type="text" name="nom" placeholder="Nom" value="{{ edit_student.nom if edit_student else '' }}" required>
                <input type="text" name="prenom" placeholder="Prénom" value="{{ edit_student.prenom if edit_student else '' }}" required>
                <select name="filiere">
                    <option value="Génie Info" {{ 'selected' if edit_student and edit_student.filiere == 'Génie Info' }}>Génie Info</option>
                    <option value="Cyber" {{ 'selected' if edit_student and edit_student.filiere == 'Cyber' }}>Cyber</option>
                </select>
                <button type="submit" class="btn {{ 'btn-update' if edit_student else 'btn-add' }}">
                    <i class="fas {{ 'fa-sync' if edit_student else 'fa-plus' }}"></i>
                    {{ 'Mettre à jour' if edit_student else 'Ajouter' }}
                </button>
                {% if edit_student %}<a href="/" style="padding:12px; color: grey;">Annuler</a>{% endif %}
            </form>
        </div>

        <div class="glass-card">
            <table>
                <thead><tr><th>ID</th><th>Étudiant</th><th>Filière</th><th>Actions</th></tr></thead>
                <tbody>
                    {% for s in students %}
                    <tr>
                        <td>#{{ s.id }}</td>
                        <td><strong>{{ s.nom }}</strong> {{ s.prenom }}</td>
                        <td>{{ s.filiere }}</td>
                        <td>
                            <a href="/edit/{{ s.id }}" class="btn" style="background:#f1f5f9; color:#475569; padding:8px;"><i class="fas fa-pen"></i></a>
                            <form action="/delete/{{ s.id }}" method="post" style="display:inline;">
                                <button class="btn btn-del" style="padding:8px;"><i class="fas fa-trash"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, students=students_db, count=len(students_db), edit_student=None)

@app.route('/edit/<int:uid>')
def edit(uid):
    target = next((s for s in students_db if s['id'] == uid), None)
    return render_template_string(HTML_TEMPLATE, students=students_db, count=len(students_db), edit_student=target)

@app.route('/save', methods=['POST'])
def save():
    global next_id
    uid = request.form.get('id')
    nom, prenom, fil = request.form.get('nom').upper(), request.form.get('prenom'), request.form.get('filiere')
    
    if uid: # Modification
        for s in students_db:
            if s['id'] == int(uid):
                s.update({"nom": nom, "prenom": prenom, "filiere": fil})
        ACTIONS_TOTAL.labels(type='modification').inc()
    else: # Création
        students_db.append({"id": next_id, "nom": nom, "prenom": prenom, "filiere": fil})
        next_id += 1
        STUDENT_COUNT.set(len(students_db))
        ACTIONS_TOTAL.labels(type='inscription').inc()
    return redirect(url_for('home'))

@app.route('/delete/<int:uid>', methods=['POST'])
def delete(uid):
    global students_db
    students_db = [s for s in students_db if s['id'] != uid]
    STUDENT_COUNT.set(len(students_db))
    ACTIONS_TOTAL.labels(type='suppression').inc()
    return redirect(url_for('home'))

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
