import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template_string, request, redirect, url_for
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- CONFIGURATION NOTIFICATIONS EMAIL ---
GMAIL_USER = "jeuxm0703@gmail.com"
GMAIL_PASS = "wnnahwqvwlzpxjdw"
DESTINATAIRE = "jeuxm0703@gmail.com"

def envoyer_alerte(sujet, action_titre, message_details, couleur_hex):
    msg = MIMEMultipart()
    msg['From'] = f"INPTIC Monitoring <{GMAIL_USER}>"
    msg['To'] = DESTINATAIRE
    msg['Subject'] = sujet

    # Design HTML Pro pour ta boîte Gmail
    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7f6; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 8px solid {couleur_hex};">
            <div style="padding: 25px; background-color: #ffffff; text-align: center;">
                <h1 style="margin: 0; color: {couleur_hex}; font-size: 24px;">{action_titre}</h1>
            </div>
            <div style="padding: 30px; color: #334155; line-height: 1.6;">
                <p style="font-size: 16px;">Bonjour Marc,</p>
                <p style="font-size: 15px;">Une nouvelle opération a été enregistrée sur <b>INPTIC OS</b> :</p>
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 5px solid {couleur_hex}; margin: 20px 0;">
                    <span style="font-size: 14px; text-transform: uppercase; color: #64748b; font-weight: bold;">Détails de l'événement</span><br>
                    <p style="margin: 10px 0 0; font-size: 16px; color: #1e293b;">{message_details}</p>
                </div>
                <p style="font-size: 13px; color: #94a3b8; margin-top: 30px; text-align: center;">
                    Notification automatisée via Pipeline Jenkins & Docker
                </p>
            </div>
            <div style="padding: 15px; background: #1e293b; text-align: center; font-size: 11px; color: #94a3b8;">
                © 2026 Projet Fin d'Étude INPTIC | Système de Monitoring Temps Réel
            </div>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, DESTINATAIRE, msg.as_string())
            print(f"[*] Email '{action_titre}' envoyé avec succès.")
    except Exception as e:
        print(f"[!] Erreur d'envoi : {e}")

# --- PERSISTANCE ---
DB_FILE = 'database.json'

def init_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        with open(DB_FILE, 'w') as f:
            json.dump([], f) # Initialisation à vide

def get_students():
    init_db()
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_students(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

# --- MÉTRIQUES PROMETHEUS ---
STUDENT_COUNT = Gauge('inptic_student_current_total', 'Total étudiants en base')
ACTIONS_TOTAL = Counter('inptic_actions_total', 'Compteur total des actions', ['type'])

# --- UI TEMPLATE (Ton design Dashboard) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>INPTIC OS | Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --p: #1e293b; --s: #3b82f6; --acc: #10b981; --danger: #ef4444; --warn: #f59e0b; --bg: #f1f5f9; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background: var(--p); color: white; padding: 30px 20px; }
        .sidebar h2 { color: var(--s); margin-bottom: 40px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .nav-link { color: #94a3b8; text-decoration: none; padding: 12px; display: block; border-radius: 8px; margin-bottom: 5px; transition: 0.3s; }
        .nav-link:hover, .nav-link.active { background: #334155; color: white; }
        .main { flex: 1; padding: 30px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .quick-actions { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .action-card { background: white; padding: 20px; border-radius: 16px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .icon-box { width: 45px; height: 45px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; font-size: 1.1rem; }
        .glass-card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .input-group { display: flex; gap: 15px; margin-top: 15px; }
        input, select { padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; flex: 1; outline: none; }
        .btn { padding: 12px 25px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; color: white; display: flex; align-items: center; gap: 8px; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 15px; background: #f8fafc; color: #64748b; font-size: 0.75rem; text-transform: uppercase; }
        td { padding: 15px; border-bottom: 1px solid #f1f5f9; }
        .badge { background: #e0f2fe; color: var(--s); padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
        .status-bar { background: white; padding: 15px; border-radius: 12px; display: flex; align-items: center; gap: 10px; margin-bottom: 25px; border-left: 5px solid var(--acc); font-size: 0.85rem; }
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
            <h1>Système de Gestion</h1>
            <div style="font-size: 0.9rem; color: #64748b;">Administrateur : <strong>Marc Essone</strong></div>
        </div>
        <div class="quick-actions">
            <div class="action-card"><div class="icon-box" style="background: #ecfdf5; color: var(--acc);"><i class="fas fa-users"></i></div><p style="font-weight: 600;">{{ count }} Étudiants</p></div>
            <div class="action-card"><div class="icon-box" style="background: #eff6ff; color: var(--s);"><i class="fas fa-plus"></i></div><p style="font-weight: 600;">Inscription</p></div>
            <div class="action-card"><div class="icon-box" style="background: #fffbeb; color: var(--warn);"><i class="fas fa-edit"></i></div><p style="font-weight: 600;">Mise à jour</p></div>
            <div class="action-card"><div class="icon-box" style="background: #fef2f2; color: var(--danger);"><i class="fas fa-shield-alt"></i></div><p style="font-weight: 600;">Sécurité</p></div>
        </div>
        <div class="status-bar">
            <div style="width: 10px; height: 10px; background: var(--acc); border-radius: 50%;"></div>
            Monitoring Temps Réel & Alertes Emails activés.
        </div>
        <div class="glass-card">
            <h3><i class="fas fa-user-edit"></i> {{ 'Modifier les infos' if edit_student else 'Nouvel Étudiant' }}</h3>
            <form action="/save" method="post" class="input-group">
                <input type="hidden" name="id" value="{{ edit_student.id if edit_student else '' }}">
                <input type="text" name="nom" placeholder="NOM" value="{{ edit_student.nom if edit_student else '' }}" required>
                <input type="text" name="prenom" placeholder="Prénom" value="{{ edit_student.prenom if edit_student else '' }}" required>
                <select name="filiere">
                    <option value="Génie Info" {{ 'selected' if edit_student and edit_student.filiere == 'Génie Info' }}>Génie Informatique</option>
                    <option value="Cybersécurité" {{ 'selected' if edit_student and edit_student.filiere == 'Cybersécurité' }}>Cybersécurité</option>
                </select>
                <button type="submit" class="btn" style="background: {{ 'var(--warn)' if edit_student else 'var(--s)' }}">
                    <i class="fas fa-check-circle"></i> {{ 'Enregistrer' if edit_student else 'Ajouter' }}
                </button>
            </form>
        </div>
        <div class="glass-card">
            <table>
                <thead><tr><th>ID</th><th>Nom Complet</th><th>Filière</th><th style="text-align:right">Action</th></tr></thead>
                <tbody>
                    {% for s in students %}
                    <tr>
                        <td>#{{ s.id }}</td>
                        <td><strong>{{ s.nom }}</strong> {{ s.prenom }}</td>
                        <td><span class="badge">{{ s.filiere }}</span></td>
                        <td style="text-align:right">
                            <a href="/edit/{{ s.id }}" style="color:var(--warn); margin-right:15px;"><i class="fas fa-edit"></i></a>
                            <form action="/delete/{{ s.id }}" method="post" style="display:inline;">
                                <button style="border:none; background:none; color:var(--danger); cursor:pointer;"><i class="fas fa-user-times"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:30px;">Aucun étudiant enregistré pour le moment.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    db = get_students()
    STUDENT_COUNT.set(len(db))
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

    if uid: # MODIFICATION
        for s in db:
            if s['id'] == int(uid):
                s.update({"nom": nom, "prenom": prenom, "filiere": fil})
        ACTIONS_TOTAL.labels(type='modification').inc()
        envoyer_alerte("✏️ Modification INPTIC OS", "MISE À JOUR ÉTUDIANT", 
                       f"Les informations de l'étudiant <b>{nom} {prenom}</b> (#ID {uid}) ont été modifiées.", "#3b82f6")
    else: # AJOUT
        new_id = max([s['id'] for s in db]) + 1 if db else 1
        db.append({"id": new_id, "nom": nom, "prenom": prenom, "filiere": fil})
        ACTIONS_TOTAL.labels(type='inscription').inc()
        envoyer_alerte("✅ Succès Inscription", "NOUVEL ÉTUDIANT AJOUTÉ", 
                       f"<b>{nom} {prenom}</b> vient d'être inscrit en filière <b>{fil}</b>.", "#10b981")

    save_students(db)
    STUDENT_COUNT.set(len(db))
    return redirect(url_for('home'))

@app.route('/delete/<int:uid>', methods=['POST'])
def delete(uid):
    db = get_students()
    target = next((s for s in db if s['id'] == uid), None)
    nom_supprime = f"{target['nom']} {target['prenom']}" if target else "Inconnu"

    db = [s for s in db if s['id'] != uid]
    save_students(db)
    
    STUDENT_COUNT.set(len(db))
    ACTIONS_TOTAL.labels(type='suppression').inc()

    envoyer_alerte("⚠️ Alerte Suppression", "SUPPRESSION EFFECTUÉE", 
                   f"L'étudiant <b>{nom_supprime}</b> (ID #{uid}) a été retiré de la base de données.", "#ef4444")
    return redirect(url_for('home'))

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
