from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Bot Hosting</title>
        <style>body { font-family: Arial; padding: 40px; text-align: center; } h1 { color: #333; } .success { color: green; }</style>
    </head>
    <body>
        <h1>🚀 Telegram Bot Hosting</h1>
        <p class="success">✅ Python Flask ÇALIŞIYOR!</p>
        <p><a href="/health">Health Check</a> | <a href="/admin">Admin</a></p>
        <script src="https://www.gstatic.com/firebasejs/9.6.10/firebase-app.js"></script>
        <script>
            firebase.initializeApp({
                apiKey: "AIzaSyBbUN60L9CtxvGEDAtQxc0nDUa80nJkyoM",
                authDomain: "sscorpion-874a7.firebaseapp.com",
                projectId: "sscorpion-874a7",
                storageBucket: "sscorpion-874a7.firebasestorage.app"
            });
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'app': 'telegram-bot'})

@app.route('/admin')
def admin():
    return '''
    <h1>Admin</h1>
    <form action="/admin/login" method="post">
        <input type="text" name="username" placeholder="Kullanıcı"><br>
        <input type="password" name="password" placeholder="Şifre"><br>
        <button>Giriş</button>
    </form>
    <p><small>Test: admin / admin123</small></p>
    '''

@app.route('/admin/login', methods=['POST'])
def admin_login():
    if request.form.get('username') == 'admin' and request.form.get('password') == 'admin123':
        return '✅ Giriş başarılı!'
    return '❌ Hatalı giriş!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
@app.route('/api/firebase-test')
def firebase_test():
    return jsonify({
        'success': True,
        'message': 'Firebase client-side için hazır',
        'config': {
            'apiKey': FIREBASE_CONFIG['apiKey'][:10] + '...',  # Güvenlik için kısalt
            'projectId': FIREBASE_CONFIG['projectId'],
            'status': 'ready'
        }
    })
