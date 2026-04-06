import os
import requests
import re
import datetime
import zipfile
import time

# Puxa as credenciais que você salvou no GitHub
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')

def get_data_formatada():
    return datetime.datetime.now().strftime("%d-%m")

def compactar_arquivo(conteudo_audio, nome_programa, nome_bloco):
    data = get_data_formatada()
    nome_zip = f"{nome_programa}_{data}.zip"
    
    with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(nome_bloco, conteudo_audio)
    
    return nome_zip

def enviar_pcloud(caminho_arquivo):
    # API do pCloud para upload direto
    url = "https://api.pcloud.com/uploadfile"
    params = {
        'username': EMAIL,
        'password': PASSWORD,
        'folderid': 0,  # 0 envia para a pasta raiz
        'nopartial': 1
    }
    
    try:
        with open(caminho_arquivo, 'rb') as f:
            files = {'file': f}
            r = requests.post(url, params=params, files=files)
        return r.status_code == 200
    except:
        return False

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt):
        print(f"ℹ️ Arquivo {arquivo_txt} não encontrado.")
        return

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            # Extrai o nome do programa do link
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog = match.group(1).replace("_", " ").strip()
                bloco = match.group(2).replace("_", " ").strip()
            else:
                prog = "PROGRAMA"
                bloco = url.split('/')[-1]

            print(f"⬇️ Baixando: {prog}...")
            r = requests.get(url, timeout=120)
            r.raise_for_status()

            # Gera o ZIP com a data
            nome_zip = compactar_arquivo(r.content, prog, bloco)

            print(f"☁️ Enviando para pCloud: {nome_zip}")
            if enviar_pcloud(nome_zip):
                print(f"✅ SUCESSO!")
            else:
                print(f"❌ Falha no upload para o pCloud.")

            # Limpa o arquivo temporário no GitHub
            if os.path.exists(nome_zip):
                os.remove(nome_zip)
            
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro no link {url}: {e}")

if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ ERRO: Configure PCLOUD_EMAIL e PCLOUD_PASS no GitHub!")
    else:
        processar('links.txt')
        processar('links_fds.txt')
