import subprocess
import sys
import os
import time
import random
import re
import datetime
import zipfile

# 1. Garante que as bibliotecas existam no GitHub
def instalar_dependencias():
    try:
        import mediafire
        import requests
    except ImportError:
        print("🔧 Instalando bibliotecas...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mediafire", "requests"])

instalar_dependencias()

from mediafire import MediaFireApi, MediaFireUploader
import requests

# 2. Configurações (Pegas dos Secrets do GitHub)
EMAIL = os.getenv('MF_EMAIL')
PASSWORD = os.getenv('MF_PASSWORD')

def get_data_formatada():
    agora = datetime.datetime.now()
    return agora.strftime("%d-%m")

def compactar_arquivo(conteudo_audio, nome_programa, nome_bloco):
    data = get_data_formatada()
    nome_zip = f"{nome_programa} {data}.zip"
    caminho_temp_audio = f"temp_{nome_bloco}"
    
    with open(caminho_temp_audio, 'wb') as f:
        f.write(conteudo_audio)
    
    with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(caminho_temp_audio, arcname=nome_bloco)
    
    os.remove(caminho_temp_audio)
    return nome_zip

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt): 
        print(f"⚠️ Arquivo {arquivo_txt} não encontrado.")
        return

    api = MediaFireApi()
    uploader = MediaFireUploader(api)
    
    try:
        session = api.user_get_session_token(email=EMAIL, password=PASSWORD, application_id='25145')
        api.session = session
        print(f"🔓 Login ok para processar {arquivo_txt}")
    except Exception as e:
        print(f"❌ Erro de login no MediaFire: {e}")
        return

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        # Pausa para evitar bloqueio
        time.sleep(random.randint(7, 15))

        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog = match.group(1).replace("_", " ").strip()
                bloco = match.group(2).replace("_", " ").strip()
            else:
                prog = "PROGRAMA"
                bloco = url.split('/')[-1]

            print(f"⬇️ Baixando: {bloco}")
            r = requests.get(url, timeout=180)
            r.raise_for_status()

            print(f"📦 Compactando: {prog}...")
            nome_zip = compactar_arquivo(r.content, prog, bloco)

            print(f"☁️ Enviando {nome_zip}...")
            with open(nome_zip, 'rb') as f:
                uploader.upload(f, nome_zip)
            
            print(f"✅ Sucesso: {nome_zip}")
            if os.path.exists(nome_zip):
                os.remove(nome_zip)

        except Exception as e:
            print(f"❌ Erro no link {url}: {e}")
            time.sleep(10)

# 3. Execução Principal
if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Faltam os Secrets MF_EMAIL ou MF_PASSWORD.")
    else:
        # Processa a primeira lista
        processar('links.txt')
        
        # Pausa entre as listas
        time.sleep(10)
        
        # Processa a segunda lista
        processar('links_fds.txt')
