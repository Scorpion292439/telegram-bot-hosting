from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_session import Session
import os
import uuid
import json
import threading
import subprocess
import time
from datetime import datetime
import firebase_admin
from firebase_admin import auth, firestore, credentials
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'bots'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session yapılandırması
Session(app)

# Firebase başlatma
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
except:
    print("Firebase Admin SDK için serviceAccountKey.json gerekli")

db = firestore.client()

# Kullanıcı rollerini tanımla
USER_ROLES = {
    'free': {
        'max_bots': 1,
        'name': 'Ücretsiz'
    },
    'vip': {
        'max_bots': 12,
        'name': 'VIP'
    },
    'admin': {
        'max_bots': 999,
        'name': 'Yönetici'
    }
}

# Çalışan botları takip etmek için
running_bots = {}

def check_auth():
    """Kullanıcının oturum açıp açmadığını kontrol et"""
    if 'user' not in session:
        return None
    
    user_data = session.get('user')
    email = user_data.get('email')
    
    # Firebase'den güncel kullanıcı bilgilerini al
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        results = query.stream()
        
        for doc in results:
            user_info = doc.to_dict()
            user_info['id'] = doc.id
            return user_info
    
    except Exception as e:
        print(f"Auth hatası: {e}")
    
    return None

def get_user_bots(user_id):
    """Kullanıcının botlarını getir"""
    try:
        bots_ref = db.collection('bots').where('user_id', '==', user_id)
        bots = []
        for doc in bots_ref.stream():
            bot_data = doc.to_dict()
            bot_data['id'] = doc.id
            bot_data['status'] = 'running' if bot_data['id'] in running_bots else 'stopped'
            bots.append(bot_data)
        return bots
    except:
        return []

def run_bot(bot_id, file_path, token):
    """Botu çalıştır"""
    try:
        # Botu çalıştır
        process = subprocess.Popen(['python', file_path], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        
        running_bots[bot_id] = {
            'process': process,
            'start_time': datetime.now(),
            'file_path': file_path
        }
        
        # Bot çalışma durumunu güncelle
        bot_ref = db.collection('bots').document(bot_id)
        bot_ref.update({
            'status': 'running',
            'last_started': datetime.now().isoformat()
        })
        
        print(f"Bot {bot_id} başlatıldı")
        
    except Exception as e:
        print(f"Bot çalıştırma hatası: {e}")

@app.route('/')
def index():
    """Ana sayfa"""
    user = check_auth()
    if user:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Giriş sayfası"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Firebase Authentication ile giriş yap
            # Not: Firebase Admin SDK doğrudan giriş yapmaz, 
            # bu nedenle özel bir token doğrulama sistemi kurulmalı
            # Bu örnekte basit bir sistem kullanıyoruz
            
            users_ref = db.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            results = query.stream()
            
            for doc in results:
                user_data = doc.to_dict()
                # Basit şifre kontrolü (gerçek uygulamada hash kullan)
                if user_data.get('password') == hashlib.sha256(password.encode()).hexdigest():
                    session['user'] = {
                        'id': doc.id,
                        'email': email,
                        'role': user_data.get('role', 'free'),
                        'name': user_data.get('name', 'Kullanıcı')
                    }
                    return redirect(url_for('dashboard'))
            
            return render_template('login.html', error='Geçersiz email veya şifre')
            
        except Exception as e:
            return render_template('login.html', error=str(e))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Kayıt sayfası"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        try:
            # Kullanıcıyı veritabanına kaydet
            users_ref = db.collection('users')
            
            # Email kontrolü
            query = users_ref.where('email', '==', email).limit(1)
            if len(list(query.stream())) > 0:
                return render_template('register.html', error='Bu email zaten kullanılıyor')
            
            # Yeni kullanıcı oluştur
            user_data = {
                'email': email,
                'password': hashlib.sha256(password.encode()).hexdigest(),  # Gerçek uygulamada daha güvenli hash
                'name': name,
                'role': 'free',
                'created_at': datetime.now().isoformat(),
                'vip_expiry': None,
                'max_bots': 1
            }
            
            # Firestore'a kaydet
            doc_ref = users_ref.add(user_data)
            
            # Oturum aç
            session['user'] = {
                'id': doc_ref[1].id,
                'email': email,
                'role': 'free',
                'name': name
            }
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """Kullanıcı paneli"""
    user = check_auth()
    if not user:
        return redirect(url_for('login'))
    
    # Kullanıcının botlarını getir
    user_bots = get_user_bots(user['id'])
    
    return render_template('dashboard.html', 
                         user=user, 
                         bots=user_bots,
                         user_roles=USER_ROLES)

@app.route('/upload_bot', methods=['POST'])
def upload_bot():
    """Bot yükleme"""
    user = check_auth()
    if not user:
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401
    
    # Kullanıcının bot sayısını kontrol et
    user_bots = get_user_bots(user['id'])
    max_bots = USER_ROLES[user['role']]['max_bots']
    
    if len(user_bots) >= max_bots:
        return jsonify({'error': f'Maksimum {max_bots} bot yükleyebilirsiniz'}), 400
    
    if 'bot_file' not in request.files:
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    file = request.files['bot_file']
    bot_name = request.form.get('bot_name', 'Yeni Bot')
    bot_token = request.form.get('bot_token', '')
    
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400
    
    if not file.filename.endswith('.py'):
        return jsonify({'error': 'Sadece .py dosyaları yükleyebilirsiniz'}), 400
    
    # Dosyayı kaydet
    bot_id = str(uuid.uuid4())
    filename = f"{bot_id}.py"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Bots klasörünü oluştur
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    file.save(file_path)
    
    # Firestore'a bot bilgilerini kaydet
    bot_data = {
        'user_id': user['id'],
        'name': bot_name,
        'filename': filename,
        'token': bot_token,
        'status': 'stopped',
        'created_at': datetime.now().isoformat(),
        'last_started': None
    }
    
    bot_ref = db.collection('bots').document(bot_id)
    bot_ref.set(bot_data)
    
    return jsonify({
        'success': True,
        'bot_id': bot_id,
        'message': 'Bot başarıyla yüklendi'
    })

@app.route('/start_bot/<bot_id>')
def start_bot(bot_id):
    """Botu başlat"""
    user = check_auth()
    if not user:
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401
    
    # Bot bilgilerini getir
    bot_ref = db.collection('bots').document(bot_id)
    bot_doc = bot_ref.get()
    
    if not bot_doc.exists:
        return jsonify({'error': 'Bot bulunamadı'}), 404
    
    bot_data = bot_doc.to_dict()
    
    # Kullanıcı yetkisi kontrolü
    if bot_data['user_id'] != user['id'] and user['role'] != 'admin':
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
    
    # Bot zaten çalışıyor mu?
    if bot_id in running_bots:
        return jsonify({'error': 'Bot zaten çalışıyor'}), 400
    
    # Bot dosyasını bul
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], bot_data['filename'])
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Bot dosyası bulunamadı'}), 404
    
    # Yeni thread'de botu başlat
    thread = threading.Thread(target=run_bot, args=(bot_id, file_path, bot_data.get('token', '')))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Bot başlatılıyor...'})

@app.route('/stop_bot/<bot_id>')
def stop_bot(bot_id):
    """Botu durdur"""
    user = check_auth()
    if not user:
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401
    
    # Bot çalışıyor mu?
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot çalışmıyor'}), 400
    
    # Bot bilgilerini getir
    bot_ref = db.collection('bots').document(bot_id)
    bot_doc = bot_ref.get()
    
    if not bot_doc.exists:
        return jsonify({'error': 'Bot bulunamadı'}), 404
    
    bot_data = bot_doc.to_dict()
    
    # Kullanıcı yetkisi kontrolü
    if bot_data['user_id'] != user['id'] and user['role'] != 'admin':
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
    
    # Botu durdur
    process = running_bots[bot_id]['process']
    process.terminate()
    process.wait()
    
    # Çalışan botlar listesinden çıkar
    del running_bots[bot_id]
    
    # Durumu güncelle
    bot_ref.update({
        'status': 'stopped',
        'last_stopped': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'message': 'Bot durduruldu'})

@app.route('/delete_bot/<bot_id>')
def delete_bot(bot_id):
    """Botu sil"""
    user = check_auth()
    if not user:
        return jsonify({'error': 'Oturum açmanız gerekiyor'}), 401
    
    # Bot bilgilerini getir
    bot_ref = db.collection('bots').document(bot_id)
    bot_doc = bot_ref.get()
    
    if not bot_doc.exists:
        return jsonify({'error': 'Bot bulunamadı'}), 404
    
    bot_data = bot_doc.to_dict()
    
    # Kullanıcı yetkisi kontrolü
    if bot_data['user_id'] != user['id'] and user['role'] != 'admin':
        return jsonify({'error': 'Bu işlem için yetkiniz yok'}), 403
    
    # Bot çalışıyorsa durdur
    if bot_id in running_bots:
        process = running_bots[bot_id]['process']
        process.terminate()
        del running_bots[bot_id]
    
    # Dosyayı sil
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], bot_data['filename'])
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Veritabanından sil
    bot_ref.delete()
    
    return jsonify({'success': True, 'message': 'Bot silindi'})

@app.route('/admin')
def admin_panel():
    """Yönetici paneli"""
    user = check_auth()
    if not user or user['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    # Tüm kullanıcıları getir
    users_ref = db.collection('users')
    all_users = []
    for doc in users_ref.stream():
        user_data = doc.to_dict()
        user_data['id'] = doc.id
        all_users.append(user_data)
    
    # Tüm botları getir
    bots_ref = db.collection('bots')
    all_bots = []
    for doc in bots_ref.stream():
        bot_data = doc.to_dict()
        bot_data['id'] = doc.id
        all_bots.append(bot_data)
    
    return render_template('admin.html', 
                         user=user, 
                         users=all_users,
                         bots=all_bots,
                         running_bots=running_bots)

@app.route('/admin/create_vip_key', methods=['POST'])
def create_vip_key():
    """VIP anahtarı oluştur"""
    user = check_auth()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Yetkiniz yok'}), 403
    
    # VIP anahtarı oluştur
    vip_key = str(uuid.uuid4())
    expiry_days = int(request.form.get('expiry_days', 30))
    
    # Firestore'a kaydet
    vip_data = {
        'key': vip_key,
        'created_by': user['id'],
        'created_at': datetime.now().isoformat(),
        'expiry_days': expiry_days,
        'used': False,
        'used_by': None,
        'used_at': None
    }
    
    db.collection('vip_keys').document(vip_key).set(vip_data)
    
    return jsonify({
        'success': True,
        'vip_key': vip_key,
        'message': f'VIP anahtarı oluşturuldu. {expiry_days} gün geçerli.'
    })

@app.route('/admin/update_user_role', methods=['POST'])
def update_user_role():
    """Kullanıcı rolünü güncelle"""
    user = check_auth()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Yetkiniz yok'}), 403
    
    user_id = request.form.get('user_id')
    new_role = request.form.get('role')
    
    if new_role not in USER_ROLES:
        return jsonify({'error': 'Geçersiz rol'}), 400
    
    # Kullanıcıyı güncelle
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'role': new_role,
        'max_bots': USER_ROLES[new_role]['max_bots']
    })
    
    return jsonify({
        'success': True,
        'message': f'Kullanıcı rolü {USER_ROLES[new_role]["name"]} olarak güncellendi'
    })

@app.route('/logout')
def logout():
    """Çıkış yap"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Gerekli klasörleri oluştur
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Uygulamayı başlat
    app.run(debug=True, host='0.0.0.0', port=5000)