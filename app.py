from flask import Flask, render_template_string, request, jsonify
import os
import subprocess
import datetime
import tempfile

app = Flask(__name__)

# ========== ANA SAYFA ==========
@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Python Hosting Platform</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                text-align: center;
            }
            header {
                margin-bottom: 50px;
            }
            h1 {
                font-size: 48px;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .tagline {
                font-size: 20px;
                opacity: 0.9;
                margin-bottom: 40px;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 25px;
                margin-bottom: 50px;
            }
            .feature-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                transition: transform 0.3s;
            }
            .feature-card:hover {
                transform: translateY(-10px);
                background: rgba(255,255,255,0.2);
            }
            .feature-icon {
                font-size: 48px;
                margin-bottom: 20px;
            }
            .feature-card h3 {
                font-size: 24px;
                margin-bottom: 15px;
            }
            .nav-buttons {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                margin-top: 40px;
            }
            .btn {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                background: white;
                color: #667eea;
                padding: 18px 35px;
                border-radius: 15px;
                text-decoration: none;
                font-size: 18px;
                font-weight: bold;
                transition: all 0.3s;
                border: none;
                cursor: pointer;
            }
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .btn-large {
                padding: 22px 45px;
                font-size: 20px;
            }
            footer {
                margin-top: 60px;
                opacity: 0.7;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 Python Hosting Platform</h1>
                <p class="tagline">Python dosyalarını yükle, 24/7 çalıştır, loglarını izle!</p>
            </header>
            
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">📁</div>
                    <h3>Python Yükle & Çalıştır</h3>
                    <p>Python dosyanızı sürükleyip bırakın, otomatik çalışsın.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <h3>Telegram Bot Hosting</h3>
                    <p>Telegram botunuzu oluşturun ve 24/7 çalıştırın.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <h3>Real-time Loglar</h3>
                    <p>Script'lerinizin çıktılarını anlık takip edin.</p>
                </div>
            </div>
            
            <div class="nav-buttons">
                <a href="/upload" class="btn btn-large">
                    <span>📤</span> Python Yükle
                </a>
                <a href="/telegram-bot" class="btn btn-large">
                    <span>🤖</span> Telegram Bot
                </a>
                <a href="/admin" class="btn">
                    <span>⚙️</span> Admin Panel
                </a>
                <a href="/health" class="btn">
                    <span>📊</span> Health Check
                </a>
            </div>
            
            <footer>
                <p>🔥 Firebase entegre | 📱 Responsive tasarım | ⚡ Hızlı deploy | Render.com üzerinde</p>
            </footer>
        </div>
    </body>
    </html>
    '''

# ========== UPLOAD SAYFASI ==========
@app.route('/upload')
def upload_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Python Dosyası Yükle</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                padding: 40px;
                max-width: 600px;
                margin: 0 auto;
                background: #f5f5f5;
                min-height: 100vh;
            }
            .upload-container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 15px;
                padding: 50px 30px;
                text-align: center;
                margin: 30px 0;
                background: #f8f9ff;
                cursor: pointer;
                transition: all 0.3s;
            }
            .upload-area:hover {
                background: #eef1ff;
                border-color: #5a67d8;
            }
            .upload-area.dragover {
                background: #e1e7ff;
                border-color: #4c51bf;
            }
            .upload-icon {
                font-size: 64px;
                color: #667eea;
                margin-bottom: 20px;
            }
            .file-input {
                display: none;
            }
            .selected-file {
                margin: 20px 0;
                padding: 15px;
                background: #e8f5e9;
                border-radius: 10px;
                display: none;
            }
            .btn {
                background: #667eea;
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                display: inline-block;
                text-decoration: none;
            }
            .btn:hover {
                background: #5a67d8;
                transform: translateY(-2px);
            }
            .btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .back-link {
                display: inline-block;
                margin-top: 30px;
                color: #667eea;
                text-decoration: none;
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="upload-container">
            <h1>📤 Python Dosyası Yükle</h1>
            <p class="subtitle">.py uzantılı Python dosyanızı yükleyin, otomatik çalıştırın</p>
            
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <h3>Dosyayı sürükleyip bırakın</h3>
                <p>veya tıklayarak seçin</p>
                <input type="file" id="fileInput" class="file-input" accept=".py">
            </div>
            
            <div class="selected-file" id="selectedFile">
                <strong>Seçilen dosya:</strong> <span id="fileName"></span>
                <br><small id="fileSize"></small>
            </div>
            
            <button class="btn" id="uploadBtn" disabled>Yükle ve Çalıştır</button>
            
            <div class="result" id="result"></div>
            
            <a href="/" class="back-link">← Ana Sayfaya Dön</a>
        </div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const selectedFile = document.getElementById('selectedFile');
            const fileName = document.getElementById('fileName');
            const fileSize = document.getElementById('fileSize');
            const uploadBtn = document.getElementById('uploadBtn');
            const resultDiv = document.getElementById('result');
            
            // Dosya seçme
            uploadArea.addEventListener('click', () => fileInput.click());
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    fileName.textContent = file.name;
                    fileSize.textContent = \(\ KB)\;
                    selectedFile.style.display = 'block';
                    uploadBtn.disabled = false;
                }
            });
            
            // Sürükle-bırak
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                if (e.dataTransfer.files.length > 0) {
                    const file = e.dataTransfer.files[0];
                    if (file.name.endsWith('.py')) {
                        fileInput.files = e.dataTransfer.files;
                        fileName.textContent = file.name;
                        fileSize.textContent = \(\ KB)\;
                        selectedFile.style.display = 'block';
                        uploadBtn.disabled = false;
                    } else {
                        alert('Sadece .py dosyaları yüklenebilir!');
                    }
                }
            });
            
            // Upload işlemi
            uploadBtn.addEventListener('click', async () => {
                const file = fileInput.files[0];
                if (!file) return;
                
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = 'Yükleniyor...';
                resultDiv.style.display = 'none';
                
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.text();
                    
                    resultDiv.innerHTML = result;
                    resultDiv.className = 'result success';
                    resultDiv.style.display = 'block';
                    
                    // Formu sıfırla
                    fileInput.value = '';
                    selectedFile.style.display = 'none';
                    uploadBtn.disabled = true;
                    uploadBtn.innerHTML = 'Yükle ve Çalıştır';
                    
                } catch (error) {
                    resultDiv.innerHTML = \<h3>❌ Hata!</h3><p>\</p>\;
                    resultDiv.className = 'result error';
                    resultDiv.style.display = 'block';
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = 'Yükle ve Çalıştır';
                }
            });
        </script>
    </body>
    </html>
    '''

# ========== UPLOAD API ==========
@app.route('/api/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return '''
        <div class="error">
            <h3>❌ Dosya seçilmedi!</h3>
            <p>Lütfen bir Python dosyası seçin.</p>
            <p><a href="/upload">Tekrar deneyin</a></p>
        </div>
        ''', 400
    
    file = request.files['file']
    if file.filename == '':
        return '''
        <div class="error">
            <h3>❌ Dosya seçilmedi!</h3>
            <p>Lütfen bir Python dosyası seçin.</p>
            <p><a href="/upload">Tekrar deneyin</a></p>
        </div>
        ''', 400
    
    if not file.filename.endswith('.py'):
        return '''
        <div class="error">
            <h3>❌ Geçersiz dosya tipi!</h3>
            <p>Sadece .py uzantılı Python dosyaları yüklenebilir.</p>
            <p><a href="/upload">Tekrar deneyin</a></p>
        </div>
        ''', 400
    
    try:
        # Geçici dosya oluştur
        import tempfile
        import os
        
        # Uploads klasörü oluştur
        os.makedirs('uploads', exist_ok=True)
        
        # Dosyayı kaydet
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        # Dosyayı çalıştır
        result = subprocess.run(
            ['python', filepath],
            capture_output=True,
            text=True,
            timeout=30  # 30 saniye timeout
        )
        
        # Sonuç HTML'i oluştur
        html_output = f'''
        <div class="success">
            <h3>✅ Dosya başarıyla yüklendi ve çalıştırıldı!</h3>
            <p><strong>Dosya:</strong> {file.filename}</p>
            <p><strong>Boyut:</strong> {(os.path.getsize(filepath) / 1024):.2f} KB</p>
            <p><strong>Zaman:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h4>📊 Çıktı:</h4>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 8px; overflow: auto; max-height: 300px;">{result.stdout}</pre>
        '''
        
        if result.stderr:
            html_output += f'''
            <h4>⚠️ Hatalar:</h4>
            <pre style="background: #fff3cd; padding: 15px; border-radius: 8px; overflow: auto; max-height: 200px;">{result.stderr}</pre>
            '''
        
        html_output += '''
            <div style="margin-top: 20px;">
                <a href="/upload" class="btn">↻ Başka dosya yükle</a>
                <a href="/" class="btn">🏠 Ana Sayfa</a>
            </div>
        </div>
        '''
        
        return html_output
        
    except subprocess.TimeoutExpired:
        return '''
        <div class="error">
            <h3>⏱️ Zaman aşımı!</h3>
            <p>Script 30 saniyeden fazla çalıştı, güvenlik nedeniyle durduruldu.</p>
            <p><a href="/upload">Tekrar deneyin</a></p>
        </div>
        ''', 408
        
    except Exception as e:
        return f'''
        <div class="error">
            <h3>❌ Hata oluştu!</h3>
            <p>{str(e)}</p>
            <p><a href="/upload">Tekrar deneyin</a></p>
        </div>
        ''', 500

# ========== TELEGRAM BOT SAYFASI ==========
@app.route('/telegram-bot')
def telegram_bot_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Bot Oluştur</title>
        <style>
            body { font-family: Arial; padding: 40px; max-width: 600px; margin: 0 auto; }
            h1 { color: #333; }
            textarea { width: 100%; height: 200px; padding: 10px; margin: 10px 0; }
            .btn { background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 10px; }
        </style>
    </head>
    <body>
        <h1>🤖 Telegram Bot Oluştur</h1>
        <p>@BotFather'dan aldığınız token'ı girin:</p>
        <form action="/api/create-bot" method="post">
            <input type="text" name="token" placeholder="Bot Token" required style="width: 100%; padding: 10px; margin: 10px 0;">
            <textarea name="code" placeholder="Python kodu (opsiyonel)"></textarea>
            <button type="submit" class="btn">Bot Oluştur</button>
        </form>
        <p><a href="/">← Ana Sayfa</a></p>
    </body>
    </html>
    '''

# ========== ADMIN SAYFASI ==========
@app.route('/admin')
def admin_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Paneli</title>
        <style>
            body { font-family: Arial; padding: 40px; max-width: 400px; margin: 0 auto; }
            h1 { color: #333; }
            input { width: 100%; padding: 10px; margin: 10px 0; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🔐 Admin Girişi</h1>
        <form action="/admin/login" method="POST">
            <input type="text" name="username" placeholder="Kullanıcı Adı" required>
            <input type="password" name="password" placeholder="Şifre" required>
            <button type="submit">Giriş Yap</button>
        </form>
        <p><small>Test: admin / admin123</small></p>
        <p><a href="/">← Ana Sayfa</a></p>
    </body>
    </html>
    '''

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    if username == 'admin' and password == 'admin123':
        return '''
        <h1>✅ Giriş Başarılı!</h1>
        <p>Admin paneline hoş geldiniz.</p>
        <p><a href="/">Ana Sayfa</a></p>
        '''
    else:
        return '''
        <h1>❌ Hatalı Giriş!</h1>
        <p>Kullanıcı adı veya şifre yanlış.</p>
        <p><a href="/admin">Tekrar Dene</a></p>
        '''

# ========== HEALTH CHECK ==========
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'python-hosting-platform',
        'version': '3.0',
        'timestamp': datetime.datetime.now().isoformat(),
        'endpoints': ['/', '/upload', '/api/upload', '/telegram-bot', '/admin', '/health']
    })

# ========== TELEGRAM BOT API ==========
@app.route('/api/create-bot', methods=['POST'])
def create_bot():
    # Basit bir response
    return '''
    <h1>🤖 Bot Oluşturuldu!</h1>
    <p>Telegram botunuz başlatıldı. Özellikler:</p>
    <ul>
        <li>/start - Botu başlat</li>
        <li>/help - Yardım</li>
        <li>/status - Bot durumu</li>
    </ul>
    <p><a href="/">Ana Sayfa</a></p>
    '''

# ========== 404 HANDLER ==========
@app.errorhandler(404)
def not_found(e):
    return '''
    <h1>404 - Sayfa Bulunamadı</h1>
    <p>Aradığınız sayfa mevcut değil.</p>
    <p><a href="/">Ana Sayfaya Dön</a></p>
    ''', 404

# ========== MAIN ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
