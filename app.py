from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import subprocess
import threading
import time
import json
import datetime
import logging
from pathlib import Path

# Firebase
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_ENABLED = True
except:
    FIREBASE_ENABLED = False

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'python-hosting-secret-123')

# Config
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LOG_FOLDER'] = 'logs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'py', 'txt', 'json', 'env'}

# Klasörleri oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

# Firebase config
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBbUN60L9CtxvGEDAtQxc0nDUa80nJkyoM",
    "authDomain": "sscorpion-874a7.firebaseapp.com",
    "projectId": "sscorpion-874a7",
    "storageBucket": "sscorpion-874a7.firebasestorage.app",
    "messagingSenderId": "574381566374",
    "appId": "1:574381566374:web:2874daf133972ecfd00767",
    "measurementId": "G-8ZZ71L7D0W"
}

# Process yönetimi
running_processes = {}

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_python_script(filepath, script_id):
    """Python dosyasını çalıştır"""
    log_file = os.path.join(app.config['LOG_FOLDER'], f"{script_id}.log")
    
    with open(log_file, 'a') as f:
        f.write(f"=== Script başlatıldı: {datetime.datetime.now()} ===\n")
    
    def run():
        try:
            process = subprocess.Popen(
                ['python', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            running_processes[script_id] = process
            
            with open(log_file, 'a') as log_f:
                for line in iter(process.stdout.readline, ''):
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_line = f"[{timestamp}] {line}"
                    log_f.write(log_line)
                    log_f.flush()
                    
                    # Firebase'e log kaydet (opsiyonel)
                    if FIREBASE_ENABLED:
                        try:
                            db = firestore.client()
                            db.collection('script_logs').add({
                                'script_id': script_id,
                                'timestamp': timestamp,
                                'message': line.strip(),
                                'type': 'output'
                            })
                        except:
                            pass
            
            process.wait()
            
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f"HATA: {str(e)}\n")
        finally:
            if script_id in running_processes:
                del running_processes[script_id]
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

# Routes
@app.route('/')
def index():
    return render_template('index.html', 
                         firebase_config=FIREBASE_CONFIG,
                         title='Python Hosting Platform')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
            file.save(filepath)
            
            # Script bilgilerini kaydet
            script_info = {
                'id': file_id,
                'filename': filename,
                'original_name': file.filename,
                'uploaded_at': datetime.datetime.now().isoformat(),
                'status': 'stopped',
                'path': filepath,
                'log_file': os.path.join(app.config['LOG_FOLDER'], f"{file_id}.log")
            }
            
            # Firebase'e kaydet
            if FIREBASE_ENABLED:
                try:
                    db = firestore.client()
                    db.collection('scripts').document(file_id).set(script_info)
                except:
                    pass
            
            return jsonify({
                'success': True,
                'message': 'Dosya yüklendi!',
                'file_id': file_id,
                'filename': filename
            })
    
    return render_template('upload.html')

@app.route('/api/scripts')
def list_scripts():
    scripts = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.endswith('.py'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            stats = os.stat(filepath)
            scripts.append({
                'id': filename,
                'name': filename,
                'size': stats.st_size,
                'uploaded': datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'status': 'running' if filename in running_processes else 'stopped'
            })
    return jsonify({'scripts': scripts})

@app.route('/api/script/<script_id>/start', methods=['POST'])
def start_script(script_id):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], script_id)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Script bulunamadı'}), 404
    
    if script_id in running_processes:
        return jsonify({'error': 'Script zaten çalışıyor'}), 400
    
    # Script'i başlat
    thread = run_python_script(filepath, script_id)
    
    return jsonify({
        'success': True,
        'message': 'Script başlatıldı',
        'script_id': script_id
    })

@app.route('/api/script/<script_id>/stop', methods=['POST'])
def stop_script(script_id):
    if script_id not in running_processes:
        return jsonify({'error': 'Script çalışmıyor'}), 400
    
    process = running_processes[script_id]
    process.terminate()
    
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    del running_processes[script_id]
    
    return jsonify({
        'success': True,
        'message': 'Script durduruldu'
    })

@app.route('/api/script/<script_id>/logs')
def get_logs(script_id):
    log_file = os.path.join(app.config['LOG_FOLDER'], f"{script_id}.log")
    
    if not os.path.exists(log_file):
        return jsonify({'logs': [], 'error': 'Log bulunamadı'})
    
    try:
        with open(log_file, 'r') as f:
            logs = f.readlines()[-100:]  # Son 100 satır
        return jsonify({'logs': logs})
    except:
        return jsonify({'logs': [], 'error': 'Log okunamadı'})

@app.route('/api/script/<script_id>/delete', methods=['DELETE'])
def delete_script(script_id):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], script_id)
    log_file = os.path.join(app.config['LOG_FOLDER'], f"{script_id}.log")
    
    # Eğer çalışıyorsa durdur
    if script_id in running_processes:
        stop_script(script_id)
    
    # Dosyaları sil
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(log_file):
            os.remove(log_file)
    except:
        pass
    
    return jsonify({'success': True, 'message': 'Script silindi'})

# Telegram Bot Hosting
@app.route('/telegram-bot')
def telegram_bot():
    return render_template('bot.html')

@app.route('/api/telegram-bot/create', methods=['POST'])
def create_telegram_bot():
    data = request.get_json()
    bot_token = data.get('token', '')
    script_code = data.get('code', '')
    
    if not bot_token:
        return jsonify({'error': 'Bot token gerekli'}), 400
    
    # Telegram bot script'i oluştur
    bot_script = f'''
import telebot
import logging
import time

# Bot token'ı
TOKEN = '{bot_token}'

# Bot oluştur
bot = telebot.TeleBot(TOKEN)

# Log ayarları
logging.basicConfig(level=logging.INFO)

# Kullanıcı tarafından eklenen kod
{script_code}

# Varsayılan komutlar
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Merhaba! Ben Python Hosting'de çalışan bir botum! 🚀")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = '''
🤖 Python Hosting Telegram Bot
/start - Botu başlat
/help - Yardım
/status - Bot durumu
    '''
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ Bot çalışıyor! Python Hosting platformunda barındırılıyorum.")

# Mesajları dinle
if __name__ == '__main__':
    print("🤖 Telegram bot başlatılıyor...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)
'''
    
    # Script'i kaydet
    bot_id = f"telegram_bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    bot_path = os.path.join(app.config['UPLOAD_FOLDER'], bot_id)
    
    with open(bot_path, 'w', encoding='utf-8') as f:
        f.write(bot_script)
    
    # Bot'u başlat
    thread = run_python_script(bot_path, bot_id)
    
    return jsonify({
        'success': True,
        'message': 'Telegram bot oluşturuldu ve başlatıldı!',
        'bot_id': bot_id
    })

# Admin paneli
@app.route('/admin')
def admin_panel():
    # Basit auth kontrolü
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    # İstatistikler
    total_scripts = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.py')])
    running_scripts = len(running_processes)
    total_logs = len([f for f in os.listdir(app.config['LOG_FOLDER']) if f.endswith('.log')])
    
    stats = {
        'total_scripts': total_scripts,
        'running_scripts': running_scripts,
        'total_logs': total_logs,
        'server_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return render_template('admin.html', stats=stats)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_pass = os.environ.get('ADMIN_PASS', 'admin123')
        
        if username == admin_user and password == admin_pass:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        
        return render_template('admin_login.html', error='Hatalı giriş!')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# Health check
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'python-hosting',
        'timestamp': datetime.datetime.now().isoformat(),
        'stats': {
            'running_processes': len(running_processes),
            'total_uploads': len(os.listdir(app.config['UPLOAD_FOLDER'])),
            'firebase': FIREBASE_ENABLED
        }
    })

# Static files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logs/<filename>')
def log_file(filename):
    return send_from_directory(app.config['LOG_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
