# ==========================================
# FOREX BOT MERKEZİ YAPILANDIRMA (CONFIG)
# ==========================================

# 1. Takip Edilecek Parite Listesi
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]

# 2. Zaman Dilimleri (D1, H4, H1, M15, M5, M1)
TREND_TIMEFRAME = "H4"      # Ana trend belirleme grafiği
TRIGGER_TIMEFRAME = "M15"    # Giriş formasyonu arama grafiği

# 3. Risk ve Kasa Limitleri
RISK_PER_TRADE = 1.0        # İşlem başı bakiyeden riske edilecek % tutar
RR_RATIO = 3.0              # Risk / Ödül oranı (1:3)
MAX_OPEN_TRADES = 3         # Aynı anda açık olabilecek maksimum işlem sayısı
MAX_SPREAD_PIPS = 2.5       # İşlem açmak için izin verilen maksimum spread (pip)

# 4. Telegram Bildirim Ayarları
TELEGRAM_ENABLED = True
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# ==========================================
# ERKEN GİRİŞ (EARLY ENTRY / MOMENTUM) AYARLARI
# ==========================================
ALLOW_EARLY_ENTRY = True           # Erken giriş mekanizması aktif mi?
EARLY_ENTRY_BODY_RATIO = 1.5       # Canlı mumun gövdesi, önceki mumun en az 1.5 katı büyüklükte olmalı (Aşırı Güç)

# ==========================================
# LOT VE MARJİN GÜVENLİK AYARLARI
# ==========================================
MIN_LOT = 0.01      # En küçük açılabilir lot
MAX_LOT = 0.50      # Güvenlik için izin verilen maksimum lot (İsteğe göre 1.0 veya 2.0 yapılabilir)