from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

USERS_FILE = 'users.csv'
CANDIDATES_FILE = 'candidates.csv'

# Load users data
def load_users():
    return pd.read_csv(USERS_FILE)

# Load candidates data
def load_candidates():
    return pd.read_csv(CANDIDATES_FILE)

# Save users data
def save_users(df):
    df.to_csv(USERS_FILE, index=False)

# Save candidates data
def save_candidates(df):
    df.to_csv(CANDIDATES_FILE, index=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users['username'].values:
            return render_template('error.html', message='Username already exists.')
        hashed_password = generate_password_hash(password)
        new_user = pd.DataFrame([{'username': username, 'password': hashed_password, 'voted': False}])
        users = pd.concat([users, new_user], ignore_index=True)
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = users[users['username'] == username]
        if not user.empty and check_password_hash(user.iloc[0]['password'], password):
            if username == 'admin':
                return redirect(url_for('admin'))
            if user.iloc[0]['voted']:
                return render_template('error.html', message='You have already voted!')
            return redirect(url_for('vote', username=username))
        return render_template('error.html', message='Invalid credentials.')
    return render_template('login.html')

@app.route('/vote/<username>', methods=['GET', 'POST'])
def vote(username):
    candidates = load_candidates()
    if request.method == 'POST':
        selected = request.form['candidate']
        candidates.loc[candidates['name'] == selected, 'votes'] += 1
        save_candidates(candidates)
        users = load_users()
        users.loc[users['username'] == username, 'voted'] = True
        save_users(users)
        return render_template('thank_you.html')
    return render_template('vote.html', candidates=candidates['name'].tolist())

@app.route('/results')
def results():
    candidates = load_candidates()
    return render_template('result.html', candidates=candidates.to_dict(orient='records'))

@app.route('/admin')
def admin():
    users = load_users()
    candidates = load_candidates()
    total_users = len(users) - 1  # Exclude admin from total
    voted_users = users[users['voted'] == True].shape[0] - 1  # Exclude admin from voted
    not_voted_users = total_users - voted_users
    return render_template('admin.html', total=total_users, voted=voted_users, not_voted=not_voted_users, candidates=candidates.to_dict(orient='records'))

@app.route('/admin-login')
def admin_login():
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found."), 404

if __name__ == '__main__':
    app.run(debug=True)
