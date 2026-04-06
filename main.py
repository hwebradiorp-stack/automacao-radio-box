import os
import requests
import re
import datetime
import zipfile
import time

def get_data_formatada():
    return datetime.datetime.now().strftime("%d-%m")

def compactar_arquivo(conteudo_audio, nome_programa, nome_bloco):
    data = get_data_formatada()
    nome_zip = f"{nome_programa}_{data}.zip"
    
    with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(nome_bloco, conteudo_audio)
    
    return nome_zip

def enviar_transfer_sh(caminho_arquivo):
    # Envia para o serviço Transfer.sh (armazenamento temporário de 14 dias)
    print(f"☁️ Fazendo upload de {caminho_arquivo}...")
    with open(caminho_arquivo, 'rb') as f:
        url = f"https://transfer.sh/{caminho_arquivo}"
        r = requests.put(url, data=f)
    
    if r.status_code == 200:
        return r.text.strip() # Retorna o link para baixar
    return None

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt):
        print(f"ℹ️ {arquivo_txt} não encontrado.")
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
                prog = "PROGRAMA"
                bloco = "audio.mp3"

            print(f"⬇️ Baixando: {prog}...")
            r = requests.get(url, timeout=120)
            r.raise_for_status()

            nome_zip = compactar_arquivo(r.content, prog, bloco)
            
            link_final = enviar_transfer_sh(nome_zip)
            
            if link_final:
                print(f"✅ SUCESSO! Link para o cliente: {link_final}")
                # Aqui você pode salvar esse link em um TXT ou log
            else:
                print(f"❌ Falha no upload.")

            if os.path.exists(nome_zip):
                os.remove(nome_zip)
            
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    processar('links.txt')
    processar('links_fds.txt')
