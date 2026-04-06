import os
import requests
import re
import datetime
import zipfile
import time
import sys

# Configurações do GitHub Secrets
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')
# Mantém sempre pelo menos 2GB livres no pCloud
ESPACO_MINIMO_BYTES = 2 * 1024 * 1024 * 1024 

def get_pasta_do_dia():
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    agora = datetime.datetime.now()
    # Ajuste para fuso horário de Brasília se necessário (GitHub usa UTC)
    dia_semana = dias[agora.weekday()]
    data = agora.strftime("%d-%m")
    return f"{dia_semana} {data}"

def obter_ou_criar_pasta(nome_pasta, parent_id=0):
    url_list = "https://api.pcloud.com/listfolder"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': parent_id}
    try:
        r = requests.get(url_list, params=params).json()
        for item in r.get('metadata', {}).get('contents', []):
            if item['name'] == nome_pasta and item['isfolder']:
                return item['folderid']
        url_create = "https://api.pcloud.com/createfolder"
        params_create = {'username': EMAIL, 'password': PASSWORD, 'name': nome_pasta, 'folderid': parent_id}
        r_create = requests.get(url_create, params=params_create).json()
        return r_create.get('metadata', {}).get('folderid')
    except:
        return parent_id

def gerenciar_espaco(folder_id):
    url_user = "https://api.pcloud.com/userinfo"
    res_user = requests.get(url_user, params={'username': EMAIL, 'password': PASSWORD}).json()
    quota = res_user.get('quota', 0)
    used = res_user.get('usedquota', 0)
    livre = quota - used
    
    if livre < ESPACO_MINIMO_BYTES:
        print(f"⚠️ Espaço crítico ({livre/(1024**3):.2f}GB). Limpando pastas antigas...")
        url_list = "https://api.pcloud.com/listfolder"
        res_list = requests.get(url_list, params={'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id}).json()
        itens = res_list.get('metadata', {}).get('contents', [])
        # Ordena pastas pela data de criação
        itens_ordenados = sorted(itens, key=lambda x: x['created'])
        if itens_ordenados:
            velha = itens_ordenados[0]
            print(f"🗑️ Removendo pasta antiga: {velha['name']}")
            requests.get("https://api.pcloud.com/deletefolderrecursive", 
                         params={'username': EMAIL, 'password': PASSWORD, 'folderid': velha['folderid']})

def enviar_pcloud(caminho_arquivo, folder_id):
    url = "https://api.pcloud.com/uploadfile"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id, 'nopartial': 1}
    with open(caminho_arquivo, 'rb') as f:
        files = {'file': f}
        r = requests.post(url, params=params, files=files)
    return r.status_code == 200

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt):
        print(f"❌ Arquivo {arquivo_txt} não encontrado no repositório.")
        return

    id_raiz = obter_ou_criar_pasta("PROGRAMAS_GRAVADOS")
    gerenciar_espaco(id_raiz)
    
    nome_subpasta = get_pasta_do_dia()
    id_subpasta = obter_ou_criar_pasta(nome_subpasta, id_raiz)

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            prog = match.group(1).replace("_", " ").strip() if match else "PROGRAMA"
            bloco = match.group(2).replace("_", " ").strip() if match else "audio.mp3"

            print(f"⬇️ Baixando: {prog}...")
            r = requests.get(url, timeout=180)
            r.raise_for_status()

            nome_zip = f"{prog}.zip"
            with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(bloco, r.content)

            print(f"☁️ Enviando para {nome_subpasta}...")
            if enviar_pcloud(nome_zip, id_subpasta):
                print(f"✅ Sucesso!")
            
            if os.path.exists(nome_zip):
                os.remove(nome_zip)
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro em {url}: {e}")

if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Configure PCLOUD_EMAIL e PCLOUD_PASS no GitHub Secrets!")
    else:
        # Pega o nome do arquivo TXT passado pelo GitHub Actions
        target_file = sys.argv[1] if len(sys.argv) > 1 else 'links.txt'
        print(f"🚀 Iniciando processamento do arquivo: {target_file}")
        processar(target_file)
