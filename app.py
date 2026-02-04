from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secret123')

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBbUN60L9CtxvGEDAtQxc0nDUa80nJkyoM",
    "authDomain": "sscorpion-874a7.firebaseapp.com",
    "projectId": "sscorpion-874a7",
    "storageBucket": "sscorpion-874a7.firebasestorage.app",
    "messagingSenderId": "574381566374",
    "appId": "1:574381566374:web:2874daf133972ecfd00767",
    "measurementId": "G-8ZZ71L7D0W"
}

# Simple admin credentials
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')

@app.route('/')
def index():
    return render_template('index.html', 
                         firebase_config=FIREBASE_CONFIG,
                         title='Ana Sayfa')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/admin/login')
    return render_template('admin.html',
                         firebase_config=FIREBASE_CONFIG,
                         title='Admin Panel')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect('/admin')
        return render_template('admin_login.html', error='Hatalı giriş!')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-bot-hosting',
        'timestamp': datetime.datetime.now().isoformat(),
        'firebase': 'ready'
    })

@app.route('/api/firebase-test')
def firebase_test():
    return jsonify({
        'success': True,
        'message': 'Firebase client SDK için hazır',
        'config': {
            'apiKey': FIREBASE_CONFIG['apiKey'],
            'projectId': FIREBASE_CONFIG['projectId']
        }
    })

# ERROR HANDLER
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return "Internal Server Error - Şablon hatası. Lütfen app.py'yi kontrol edin.", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
