import os
import requests
import re
import datetime
import zipfile
from mediafire import MediaFireApi, MediaFireUploader

# Configure suas credenciais do MediaFire aqui ou no GitHub Secrets
EMAIL = os.getenv('MF_EMAIL')
PASSWORD = os.getenv('MF_PASSWORD')
APP_ID = os.getenv('MF_APP_ID')  # Opcional, dependendo da biblioteca
API_KEY = os.getenv('MF_API_KEY')

def get_data_formatada():
    # Retorna apenas o dia e mês para o nome do arquivo
    agora = datetime.datetime.now()
    return agora.strftime("%d-%m")

def compactar_arquivo(conteudo_audio, nome_programa, nome_bloco):
    data = get_data_formatada()
    nome_zip = f"{nome_programa} {data}.zip"
    caminho_temp_audio = f"temp_{nome_bloco}"
    
    # Salva temporariamente o áudio para zipar
    with open(caminho_temp_audio, 'wb') as f:
        f.write(conteudo_audio)
    
    # Cria o ZIP
    with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(caminho_temp_audio, arcname=nome_bloco)
    
    # Remove o temporário
    os.remove(caminho_temp_audio)
    return nome_zip

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt): 
        return

    # Inicializa API do MediaFire
    api = MediaFireApi()
    uploader = MediaFireUploader(api)
    
    try:
        session = api.user_get_session_token(email=EMAIL, password=PASSWORD, application_id='25145')
        api.session = session
    except Exception as e:
        print(f"❌ Erro ao logar no MediaFire: {e}")
        return

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog = match.group(1).replace("_", " ").strip()
                bloco = match.group(2).replace("_", " ").strip()
            else:
                prog = "OUTROS"
                bloco = url.split('/')[-1]

            print(f"⬇️ Baixando: {bloco}")
            r = requests.get(url, timeout=120)
            
            print(f"📦 Compactando: {prog}...")
            nome_zip = compactar_arquivo(r.content, prog, bloco)

            print(f"☁️ Enviando {nome_zip} para MediaFire...")
            # O MediaFire enviará para a pasta raiz da sua conta
            with open(nome_zip, 'rb') as f:
                uploader.upload(f, nome_zip)
            
            print(f"✅ Sucesso: {nome_zip}")
            
            # Limpa o ZIP local após o upload
            os.remove(nome_zip)

        except Exception as e:
            print(f"❌ Erro no processo: {e}")

if __name__ == "__main__":
    processar('links.txt')
    processar('links_fds.txt')
