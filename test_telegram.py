import requests

# Doğrudan tanımlanan bilgiler
TOKEN = "9252844033:AAHS_8c5gEZaX0D9c8O7i_jIWo5QJto7Nwc"
CHAT_ID = "5198452228"

def run_direct_test():
    print("\n==========================================")
    print("   TELEGRAM DOĞRUDAN API TESTİ")
    print("==========================================")
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "<b>🚨 FOREX BOT TEST BİLDİRİMİ</b>\n\nTelegram bildirim sisteminiz başarıyla bağlandı!",
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        res_data = response.json()

        print(f"[*] HTTP Durum Kodu: {response.status_code}")
        print(f"[*] API Yanıtı    : {res_data}")

        if response.status_code == 200 and res_data.get("ok"):
            print("\n[+] BAŞARILI! Telegram bildirimi telefonunuza ulaştı.")
        else:
            print(f"\n[-] BAŞARISIZ! Telegram Hata Mesajı: {res_data.get('description')}")

    except Exception as e:
        print(f"[-] İstek / İnternet Hatası: {e}")

if __name__ == "__main__":
    run_direct_test()