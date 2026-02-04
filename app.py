import os
import sys
import time
import json
import uuid
import threading
import subprocess
import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging

# Flask uygulaması
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'python-hosting-secret-key-2026')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
CORS(app)

# Yapılandırma
UPLOAD_FOLDER = 'uploads'
LOG_FOLDER = 'logs'
ALLOWED_EXTENSIONS = {'py', 'txt', 'json'}
DATABASE_FILE = 'database.json'

# Klasörleri oluştur
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(LOG_FOLDER).mkdir(exist_ok=True)

# Firebase konfigürasyonu
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBbUN60L9CtxvGEDAtQxc0nDUa80nJkyoM",
    "authDomain": "sscorpion-874a7.firebaseapp.com",
    "projectId": "sscorpion-874a7",
    "storageBucket": "sscorpion-874a7.firebasestorage.app",
    "messagingSenderId": "574381566374",
    "appId": "1:574381566374:web:2874daf133972ecfd00767",
    "measurementId": "G-8ZZ71L7D0W"
}

# Çalışan process'leri takip
running_processes = {}
scripts_database = []

# Yardımcı fonksiyonlar
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_script_info(script_id):
    """Script bilgilerini getir"""
    for script in scripts_database:
        if script['id'] == script_id:
            return script
    return None

def save_script_info(script_info):
    """Script bilgilerini kaydet"""
    global scripts_database
    # Eski kaydı bul ve güncelle
    for i, script in enumerate(scripts_database):
        if script['id'] == script_info['id']:
            scripts_database[i] = script_info
            break
    else:
        # Yeni kayıt ekle
        scripts_database.append(script_info)
    
    # Database'i kaydet
    save_database()

def load_database():
    """Database'i yükle"""
    global scripts_database
    try:
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                scripts_database = json.load(f)
    except:
        scripts_database = []

def save_database():
    """Database'i kaydet"""
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(scripts_database, f, indent=2, ensure_ascii=False, default=str)
    except:
        pass

def run_python_script(script_id, filepath):
    """Python script'ini çalıştır"""
    log_file = os.path.join(LOG_FOLDER, f"{script_id}.log")
    
    # Log dosyasını temizle
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== Script Başlatıldı: {datetime.datetime.now()} ===\n")
        f.write(f"=== Dosya: {os.path.basename(filepath)} ===\n")
        f.write("=" * 50 + "\n")
    
    def runner():
        try:
            # Process'i başlat
            process = subprocess.Popen(
                ['python', filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8'
            )
            
            # Process'i kaydet
            running_processes[script_id] = {
                'process': process,
                'start_time': datetime.datetime.now(),
                'status': 'running'
            }
            
            # Script durumunu güncelle
            script_info = get_script_info(script_id)
            if script_info:
                script_info['status'] = 'running'
                script_info['start_time'] = datetime.datetime.now().isoformat()
                save_script_info(script_info)
            
            # Çıktıları log'a yaz
            with open(log_file, 'a', encoding='utf-8') as log_f:
                for line in iter(process.stdout.readline, ''):
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_line = f"[{timestamp}] {line}"
                    log_f.write(log_line)
                    log_f.flush()
            
            # Process bitince
            process.wait()
            
            # Script durumunu güncelle
            script_info = get_script_info(script_id)
            if script_info:
                script_info['status'] = 'stopped'
                script_info['end_time'] = datetime.datetime.now().isoformat()
                save_script_info(script_info)
            
        except Exception as e:
            # Hata log'u
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[ERROR] {str(e)}\n")
        finally:
            # Process'i temizle
            if script_id in running_processes:
                del running_processes[script_id]
    
    # Thread'de çalıştır
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return thread

# Database'i yükle
load_database()

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Ana sayfa"""
    stats = {
        'total_scripts': len(scripts_database),
        'running_scripts': len([s for s in scripts_database if s.get('status') == 'running']),
        'total_size': sum(s.get('size', 0) for s in scripts_database),
        'server_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return render_template('index.html', 
                         firebase_config=FIREBASE_CONFIG,
                         stats=stats,
                         title='Python Hosting Platform')

@app.route('/upload', methods=['GET'])
def upload_page():
    """Upload sayfası"""
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Dosya yükleme API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Dosya seçilmedi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Dosya seçilmedi'}), 400
        
        # Dosya uzantısı kontrolü
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Sadece .py, .txt, .json dosyaları yüklenebilir'}), 400
        
        # Güvenli dosya adı
        original_name = file.filename
        filename = secure_filename(original_name)
        
        # Benzersiz ID oluştur
        script_id = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        file_id = f"{script_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        
        # Dosyayı kaydet
        file.save(filepath)
        
        # Script bilgileri
        script_info = {
            'id': script_id,
            'file_id': file_id,
            'original_name': original_name,
            'filename': filename,
            'path': filepath,
            'size': os.path.getsize(filepath),
            'upload_time': datetime.datetime.now().isoformat(),
            'status': 'stopped',
            'type': 'python' if filename.endswith('.py') else 'text'
        }
        
        # Database'e kaydet
        save_script_info(script_info)
        
        return jsonify({
            'success': True,
            'message': 'Dosya başarıyla yüklendi!',
            'script_id': script_id,
            'filename': original_name,
            'size': script_info['size']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scripts')
def get_scripts():
    """Tüm script'leri listele"""
    # Script'leri güncelle (çalışan durumlarını kontrol et)
    for script in scripts_database:
        script_id = script['id']
        if script_id in running_processes:
            script['status'] = 'running'
        else:
            if script.get('status') == 'running':
                script['status'] = 'stopped'
    
    return jsonify({
        'success': True,
        'scripts': scripts_database,
        'total': len(scripts_database),
        'running': len([s for s in scripts_database if s.get('status') == 'running'])
    })

@app.route('/api/script/<script_id>/start', methods=['POST'])
def start_script(script_id):
    """Script'i başlat"""
    script_info = get_script_info(script_id)
    if not script_info:
        return jsonify({'success': False, 'error': 'Script bulunamadı'}), 404
    
    if script_id in running_processes:
        return jsonify({'success': False, 'error': 'Script zaten çalışıyor'}), 400
    
    if not os.path.exists(script_info['path']):
        return jsonify({'success': False, 'error': 'Dosya bulunamadı'}), 404
    
    # Script'i başlat
    run_python_script(script_id, script_info['path'])
    
    return jsonify({
        'success': True,
        'message': 'Script başlatıldı!',
        'script_id': script_id
    })

@app.route('/api/script/<script_id>/stop', methods=['POST'])
def stop_script(script_id):
    """Script'i durdur"""
    if script_id not in running_processes:
        return jsonify({'success': False, 'error': 'Script çalışmıyor'}), 400
    
    process_info = running_processes[script_id]
    process = process_info['process']
    
    # Process'i durdur
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    # Script durumunu güncelle
    script_info = get_script_info(script_id)
    if script_info:
        script_info['status'] = 'stopped'
        script_info['end_time'] = datetime.datetime.now().isoformat()
        save_script_info(script_info)
    
    # Process'i temizle
    del running_processes[script_id]
    
    return jsonify({
        'success': True,
        'message': 'Script durduruldu!',
        'script_id': script_id
    })

@app.route('/api/script/<script_id>/logs')
def get_script_logs(script_id):
    """Script log'larını getir"""
    log_file = os.path.join(LOG_FOLDER, f"{script_id}.log")
    
    if not os.path.exists(log_file):
        return jsonify({'success': True, 'logs': [], 'message': 'Log bulunamadı'})
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()[-200:]  # Son 200 satır
        return jsonify({'success': True, 'logs': logs})
    except:
        return jsonify({'success': False, 'error': 'Log okunamadı'})

@app.route('/api/script/<script_id>/delete', methods=['DELETE'])
def delete_script(script_id):
    """Script'i sil"""
    script_info = get_script_info(script_id)
    if not script_info:
        return jsonify({'success': False, 'error': 'Script bulunamadı'}), 404
    
    # Çalışıyorsa durdur
    if script_id in running_processes:
        stop_script(script_id)
    
    # Dosyayı sil
    try:
        if os.path.exists(script_info['path']):
            os.remove(script_info['path'])
    except:
        pass
    
    # Log dosyasını sil
    log_file = os.path.join(LOG_FOLDER, f"{script_id}.log")
    try:
        if os.path.exists(log_file):
            os.remove(log_file)
    except:
        pass
    
    # Database'den sil
    global scripts_database
    scripts_database = [s for s in scripts_database if s['id'] != script_id]
    save_database()
    
    return jsonify({
        'success': True,
        'message': 'Script silindi!',
        'script_id': script_id
    })

@app.route('/admin')
def admin_panel():
    """Admin paneli"""
    # Basit auth kontrolü
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # İstatistikler
    stats = {
        'total_scripts': len(scripts_database),
        'running_scripts': len([s for s in scripts_database if s.get('status') == 'running']),
        'stopped_scripts': len([s for s in scripts_database if s.get('status') == 'stopped']),
        'total_size_mb': f"{sum(s.get('size', 0) for s in scripts_database) / (1024*1024):.2f} MB",
        'server_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'python_version': sys.version
    }
    
    return render_template('admin.html', 
                         stats=stats,
                         scripts=scripts_database,
                         running_processes=list(running_processes.keys()))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin girişi"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Basit auth (production'da daha güvenli olmalı)
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_pass = os.environ.get('ADMIN_PASS', 'admin123')
        
        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_panel'))
        
        return render_template('admin_login.html', error='Hatalı kullanıcı adı veya şifre!')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin çıkış"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/telegram-bot', methods=['GET', 'POST'])
def telegram_bot_page():
    """Telegram bot sayfası"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'Dosya seçilmedi'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'Dosya seçilmedi'}), 400
            
            if not file.filename.endswith('.py'):
                return jsonify({'success': False, 'error': 'Sadece .py dosyaları yüklenebilir'}), 400
            
            # Bot token kontrolü
            bot_token = request.form.get('bot_token', '').strip()
            if not bot_token:
                return jsonify({'success': False, 'error': 'Bot token gereklidir'}), 400
            
            # Güvenli dosya adı
            filename = secure_filename(file.filename)
            
            # Benzersiz ID oluştur
            bot_id = f"telegram_bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            file_id = f"{bot_id}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, file_id)
            
            # Dosyayı kaydet
            file.save(filepath)
            
            # Dosyayı oku ve token'ı ekle
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Token'ı dosyaya ekle (eğer yoksa)
            if 'TOKEN =' not in content:
                content = f"TOKEN = '{bot_token}'\n" + content
            
            # Güncellenmiş içeriği kaydet
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Bot bilgileri
            bot_info = {
                'id': bot_id,
                'file_id': file_id,
                'original_name': filename,
                'filename': filename,
                'path': filepath,
                'size': os.path.getsize(filepath),
                'upload_time': datetime.datetime.now().isoformat(),
                'status': 'stopped',
                'type': 'telegram_bot',
                'bot_token': bot_token[:10] + '...'  # Güvenlik için kısalt
            }
            
            # Database'e kaydet
            save_script_info(bot_info)
            
            # Bot'u başlat
            run_python_script(bot_id, filepath)
            
            return jsonify({
                'success': True,
                'message': 'Telegram bot yüklendi ve başlatıldı!',
                'bot_id': bot_id,
                'filename': filename
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('telegram_bot.html')

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'python-hosting-platform',
        'version': '4.0',
        'timestamp': datetime.datetime.now().isoformat(),
        'stats': {
            'total_scripts': len(scripts_database),
            'running_scripts': len(running_processes),
            'total_uploads': len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.py')]),
            'database_size': len(scripts_database)
        },
        'endpoints': [
            '/', '/upload', '/admin', '/telegram-bot', '/health',
            '/api/scripts', '/api/upload', '/api/script/*'
        ]
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Sayfa bulunamadı'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Sunucu hatası'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    print(f"🚀 Python Hosting Platform başlatılıyor...")
    print(f"📁 Upload Klasörü: {UPLOAD_FOLDER}")
    print(f"📊 Toplam Script: {len(scripts_database)}")
    print(f"🌐 Port: {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
