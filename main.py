import os
import requests
import re
import datetime
import zipfile
import time
import random
from mediafire import MediaFireApi, MediaFireUploader

# Credenciais pegas do GitHub Secrets
EMAIL = os.getenv('MF_EMAIL')
PASSWORD = os.getenv('MF_PASSWORD')

def get_data_formatada():
    agora = datetime.datetime.now()
    return agora.strftime("%d-%m")

def compactar_arquivo(conteudo_audio, nome_programa, nome_bloco):
    data = get_data_formatada()
    # Nome conforme solicitado: Nome do Programa + Dia e Mês
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
        print(f"⚠️ Arquivo {arquivo_txt} não encontrado. Pulando...")
        return

    api = MediaFireApi()
    uploader = MediaFireUploader(api)
    
    try:
        session = api.user_get_session_token(email=EMAIL, password=PASSWORD, application_id='25145')
        api.session = session
        print("🔓 Login no MediaFire ok.")
    except Exception as e:
        print(f"❌ Erro de login: {e}")
        return

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        # Pausa aleatória entre 5 e 12 segundos para evitar block
        time.sleep(random.randint(5, 12))

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

            print(f"☁️ Enviando {nome_zip} para o MediaFire...")
            with open(nome_zip, 'rb') as f:
                uploader.upload(f, nome_zip)
            
            print(f"✅ Sucesso: {nome_zip}")
            os.remove(nome_zip)

        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")
            time.sleep(15)

if __name__ == "__main__":
    processar('links.txt')
    time.sleep(10)
    processar('links_fds.txt')
