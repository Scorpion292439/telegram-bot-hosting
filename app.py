from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return '''
    <h1>📤 Python Dosyası Yükle</h1>
    <form action="/api/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".py">
        <button type="submit">Yükle ve Çalıştır</button>
    </form>
    <p><a href="/">Ana Sayfa</a></p>
    '''

@app.route('/telegram-bot')
def telegram_bot():
    return '''
    <h1>🤖 Telegram Bot Oluştur</h1>
    <form action="/api/create-bot" method="post">
        <input type="text" name="token" placeholder="Bot Token" required>
        <textarea name="code" placeholder="Python kodu (opsiyonel)"></textarea>
        <button type="submit">Bot Oluştur</button>
    </form>
    <p><a href="/">Ana Sayfa</a></p>
    '''

@app.route('/admin')
def admin():
    return '''
    <h1>⚙️ Admin Paneli</h1>
    <form action="/admin/login" method="post">
        <input type="text" name="username" placeholder="Kullanıcı" required>
        <input type="password" name="password" placeholder="Şifre" required>
        <button type="submit">Giriş</button>
    </form>
    <p><small>Test: admin / admin123</small></p>
    <p><a href="/">Ana Sayfa</a></p>
    '''

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'python-hosting-platform',
        'version': '2.0',
        'features': ['python-upload', 'telegram-bot', 'admin-panel', 'real-time-logs']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
