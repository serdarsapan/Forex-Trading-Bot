import requests
from datetime import datetime, timedelta

class NewsFilter:
    """
    Yüksek etkili makro ekonomik haberleri (NFP, CPI, FOMC vb.) takip eden
    ve kritik haber saatlerinde işlemi engelleyen güvenlik modülü.
    """
    def __init__(self, buffer_minutes: int = 30):
        self.buffer_minutes = buffer_minutes  # Haberden kaç dk önce/sonra işlem engellensin?
        # ForexFactory güncel JSON takvim adresi
        self.calendar_url = "https://npoint.io/docs/ff_calendar_this_week" # Alternatif açık veri kaynağı

    def is_news_time(self, symbol: str) -> tuple[bool, str]:
        """
        Anlık saat ile yüksek etkili haber saatlerini karşılaştırır.
        Haber yakınsa (True, "Haber Nedeni") döndürür.
        """
        # Paritedeki para birimlerini ayır (Örn: EURUSD -> EUR ve USD)
        base_curr = symbol[:3]
        quote_curr = symbol[3:]

        try:
            # ForexFactory haftalık takvimi çek
            response = requests.get("https://raw.githubusercontent.com/baselhack/forex-factory-calendar/main/calendar.json", timeout=5)
            if response.status_code != 200:
                return False, "Haber takvimine erişilemedi, filtre devre dışı."

            events = response.json()
            now = datetime.utcnow()

            for event in events:
                # Sadece ilgili para birimlerini ve YÜKSEK ETKİLİ (High Impact) haberleri incele
                if event.get('impact') == 'High' and event.get('country') in [base_curr, quote_curr]:
                    # Haber tarihini ayrıştır
                    event_time_str = event.get('date') # ISO Format
                    if event_time_str:
                        event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        
                        # Zaman aralığı kontrolü
                        start_window = event_time - timedelta(minutes=self.buffer_minutes)
                        end_window = event_time + timedelta(minutes=self.buffer_minutes)

                        if start_window <= now <= end_window:
                            title = event.get('title', 'Kritik Haber')
                            country = event.get('country')
                            return True, f"KRİTİK HABER RİSKİ: {country} - {title} ({event_time.strftime('%H:%M')} UTC)"

        except Exception as e:
            # İnternet veya API hatasında sistemi kilitlememek için uyarı verip devam eder
            return False, f"Haber kontrolü yapılırken hata oluştu: {str(e)}"

        return False, "Haber riski bulunmuyor."