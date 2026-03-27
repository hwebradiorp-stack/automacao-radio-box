import os
import requests
import re
import datetime
import dropbox
from dropbox.files import WriteMode

TOKEN = os.getenv('DROPBOX_TOKEN')

def get_data_formatada(tipo="semana"):
    dias = ["Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"]
    agora = datetime.datetime.now()
    data_str = agora.strftime("%d-%m-%Y")
    if tipo == "fds":
        return f"Final_de_Semana {data_str}"
    return f"{dias[agora.weekday()]} {data_str}"

def processar(arquivo_txt, dbx, pasta_raiz):
    if not os.path.exists(arquivo_txt): return

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog = match.group(1).replace("_", " ").strip()
                bloco = match.group(2).replace("_", " ").strip()
                nome_arq = f"{prog} - {bloco}"
            else:
                prog = "OUTROS"
                nome_arq = url.split('/')[-1]

            # Caminho no Dropbox: /PROGRAMAS_GRAVADOS/Data/Programa/Arquivo.mp3
            caminho_dbx = f"/PROGRAMAS_GRAVADOS/{pasta_raiz}/{prog}/{nome_arq}"

            print(f"⬇️ Baixando: {nome_arq}")
            r = requests.get(url, timeout=120)
            
            print(f"☁️ Enviando para Dropbox...")
            dbx.files_upload(r.content, caminho_dbx, mode=WriteMode('overwrite'))
            print(f"✅ Sucesso: {nome_arq}")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    dbx = dropbox.Dropbox(TOKEN)
    processar('links.txt', dbx, get_data_formatada("semana"))
    processar('links_fds.txt', dbx, get_data_formatada("fds"))
