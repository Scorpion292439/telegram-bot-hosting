import firebase_admin
from firebase_admin import credentials, firestore, auth

# Firebase yapılandırması
firebase_config = {
    "apiKey": "AIzaSyBbUN60L9CtxvGEDAtQxc0nDUa80nJkyoM",
    "authDomain": "sscorpion-874a7.firebaseapp.com",
    "projectId": "sscorpion-874a7",
    "storageBucket": "sscorpion-874a7.firebasestorage.app",
    "messagingSenderId": "574381566374",
    "appId": "1:574381566374:web:2874daf133972ecfd00767",
    "measurementId": "G-8ZZ71L7D0W"
}

# Firebase Admin SDK başlatma
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    print("Firebase başlatıldı")
except:
    # Eğer serviceAccountKey.json yoksa, başlatma işlemini erteler
    print("Firebase Admin SDK için serviceAccountKey.json gerekli")
    
db = firestore.client()