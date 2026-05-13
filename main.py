import os
import requests
import re
import datetime
import time
import sys

# Configurações do GitHub Secrets
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')
BASE_URL = "https://api.pcloud.com"

def obter_auth_token():
    """Realiza o login e retorna um token de sessão (auth)"""
    url = f"{BASE_URL}/login"
    params = {'getauth': 1, 'username': EMAIL, 'password': PASSWORD}
    try:
        r = requests.get(url, params=params).json()
        if r.get('result') == 0:
            return r.get('auth')
        else:
            print(f"❌ Falha no login: {r.get('error')}")
            # Se o erro for 'Please provide code', o pCloud enviou um código para seu e-mail
            return None
    except Exception as e:
        print(f"Erro na conexão de login: {e}")
        return None

def obter_ou_criar_pasta(auth_token, nome_pasta, parent_id=0):
    url_list = f"{BASE_URL}/listfolder"
    params = {'auth': auth_token, 'folderid': parent_id}
    try:
        r = requests.get(url_list, params=params).json()
        if r.get('result') == 0:
            for item in r.get('metadata', {}).get('contents', []):
                if item['name'] == nome_pasta and item['isfolder']:
                    return item['folderid']
        
        url_create = f"{BASE_URL}/createfolder"
        params_create = {'auth': auth_token, 'name': nome_pasta, 'folderid': parent_id}
        r_create = requests.get(url_create, params=params_create).json()
        return r_create.get('metadata', {}).get('folderid')
    except:
        return parent_id

def enviar_pcloud(auth_token, caminho_arquivo, folder_id):
    url = f"{BASE_URL}/uploadfile"
    params = {'auth': auth_token, 'folderid': folder_id, 'nopartial': 1}
    try:
        with open(caminho_arquivo, 'rb') as f:
            files = {'file': (os.path.basename(caminho_arquivo), f)}
            r = requests.post(url, params=params, files=files)
            return r.json().get('result') == 0
    except:
        return False

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt):
        print(f"❌ Arquivo {arquivo_txt} não encontrado.")
        return

    auth_token = obter_auth_token()
    if not auth_token:
        print("⚠️ Verifique se recebeu um código de segurança no seu e-mail do pCloud.")
        return

    id_raiz = obter_ou_criar_pasta(auth_token, "PROGRAMAS_GRAVADOS")
    nome_pasta_dia = f"{datetime.datetime.now().strftime('%A %d-%m')}" # Simplificado
    id_pasta_dia = obter_ou_criar_pasta(auth_token, nome_pasta_dia, id_raiz)

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            arquivo_nome = match.group(2).replace("_", " ") if match else f"audio_{int(time.time())}.mp3"
            prog_nome = match.group(1).replace("_", " ") if match else "GERAL"

            id_pasta_prog = obter_ou_criar_pasta(auth_token, prog_nome, id_pasta_dia)

            print(f"⬇️ Baixando: {arquivo_nome}")
            r = requests.get(url, timeout=300)
            with open(arquivo_nome, 'wb') as f:
                f.write(r.content)

            if enviar_pcloud(auth_token, arquivo_nome, id_pasta_prog):
                print(f"✅ Enviado: {arquivo_nome}")
            
            if os.path.exists(arquivo_nome): os.remove(arquivo_nome)
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else 'links.txt'
    processar(target_file)
