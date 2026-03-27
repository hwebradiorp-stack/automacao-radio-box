import os
import requests
import re
from boxsdk import OAuth2, Client

# Puxa as chaves dos Secrets do GitHub
CLIENT_ID = os.getenv('BOX_CLIENT_ID')
CLIENT_SECRET = os.getenv('BOX_CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('BOX_TOKEN')
ID_PASTA_BOX = '373375034301'

def baixar_e_enviar():
    # Configura conexão com o Box
    auth = OAuth2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, access_token=ACCESS_TOKEN)
    client = Client(auth)

    # Abre sua lista de links (deve estar no repositório também)
    if not os.path.exists('links.txt'):
        print("Arquivo links.txt não encontrado.")
        return

    with open('links.txt', 'r') as f:
        for url in f:
            url = url.strip()
            if "http" not in url: continue
            
            # Extrai o nome do programa (ex: Adrenalina, Vibe Mix)
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                nome_arquivo = f"{match.group(1)} - {match.group(2)}".replace("_", " ")
                
                print(f"Baixando: {nome_arquivo}")
                r = requests.get(url)
                with open(nome_arquivo, 'wb') as f_audio:
                    f_audio.write(r.content)

                # Envia para o Box do Henrique
                print(f"Enviando para o Box...")
                with open(nome_arquivo, 'rb') as f_upload:
                    client.folder(ID_PASTA_BOX).upload_stream(f_upload, nome_arquivo)
                
                os.remove(nome_arquivo) # Limpa o disco do GitHub após enviar
                print(f"✅ Sucesso: {nome_arquivo}")

if __name__ == "__main__":
    baixar_e_enviar()
