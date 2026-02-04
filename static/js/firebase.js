// Firebase yardımcı fonksiyonları

class FirebaseHelper {
    constructor() {
        this.db = null;
        this.auth = null;
        this.initialized = false;
    }
    
    initialize() {
        try {
            if (window.firebaseApp) {
                this.db = firebase.firestore();
                this.auth = firebase.auth();
                this.initialized = true;
                console.log('✅ Firebase Helper başlatıldı');
                return true;
            }
            return false;
        } catch (error) {
            console.error('Firebase Helper başlatılamadı:', error);
            return false;
        }
    }
    
    // Kullanıcı kaydı
    async signUp(email, password, additionalData = {}) {
        if (!this.initialized) return { success: false, error: 'Firebase başlatılmadı' };
        
        try {
            const userCredential = await this.auth.createUserWithEmailAndPassword(email, password);
            const user = userCredential.user;
            
            // Ekstra kullanıcı bilgilerini kaydet
            await this.db.collection('users').doc(user.uid).set({
                email: user.email,
                createdAt: new Date().toISOString(),
                ...additionalData
            });
            
            return { success: true, user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Kullanıcı girişi
    async signIn(email, password) {
        if (!this.initialized) return { success: false, error: 'Firebase başlatılmadı' };
        
        try {
            const userCredential = await this.auth.signInWithEmailAndPassword(email, password);
            return { success: true, user: userCredential.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Veri kaydetme
    async saveData(collection, data) {
        if (!this.initialized) return { success: false, error: 'Firebase başlatılmadı' };
        
        try {
            const docRef = await this.db.collection(collection).add({
                ...data,
                timestamp: new Date().toISOString(),
                createdAt: firebase.firestore.FieldValue.serverTimestamp()
            });
            return { success: true, id: docRef.id };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Veri okuma
    async getData(collection, limit = 10) {
        if (!this.initialized) return { success: false, error: 'Firebase başlatılmadı' };
        
        try {
            const snapshot = await this.db.collection(collection)
                .orderBy('createdAt', 'desc')
                .limit(limit)
                .get();
            
            const data = [];
            snapshot.forEach(doc => {
                data.push({ id: doc.id, ...doc.data() });
            });
            
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    // Gerçek zamanlı abonelik
    subscribeToCollection(collection, callback, limit = 10) {
        if (!this.initialized) return null;
        
        return this.db.collection(collection)
            .orderBy('createdAt', 'desc')
            .limit(limit)
            .onSnapshot(snapshot => {
                const data = [];
                snapshot.forEach(doc => {
                    data.push({ id: doc.id, ...doc.data() });
                });
                callback(data);
            });
    }
    
    // Çevrimdışı desteği etkinleştir
    enableOfflineSupport() {
        if (!this.initialized) return;
        
        firebase.firestore().enablePersistence()
            .then(() => {
                console.log('✅ Çevrimdışı destek etkin');
            })
            .catch(err => {
                console.warn('Çevrimdışı destek hatası:', err);
            });
    }
}

// Global firebase helper instance'ı
window.firebaseHelper = new FirebaseHelper();

// Sayfa yüklendiğinde başlat
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        window.firebaseHelper.initialize();
        window.firebaseHelper.enableOfflineSupport();
    }, 1000);
});