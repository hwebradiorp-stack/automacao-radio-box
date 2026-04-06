import os
import requests
import re
import datetime
import zipfile
import time

# Configurações do GitHub Secrets
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')
ESPACO_MINIMO_BYTES = 2 * 1024 * 1024 * 1024 

def get_pasta_do_dia():
    # Retorna algo como "Segunda-feira 06-04"
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    agora = datetime.datetime.now()
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
    livre = res_user.get('quota', 0) - res_user.get('usedquota', 0)
    
    if livre < ESPACO_MINIMO_BYTES:
        print("⚠️ Limpando pastas antigas para liberar espaço...")
        url_list = "https://api.pcloud.com/listfolder"
        res_list = requests.get(url_list, params={'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id}).json()
        
        itens = res_list.get('metadata', {}).get('contents', [])
        # Ordena as pastas da mais antiga para a mais nova
        itens_ordenados = sorted(itens, key=lambda x: x['created'])

        for item in itens_ordenados:
            print(f"🗑️ Removendo pasta antiga: {item['name']}")
            url_del = "https://api.pcloud.com/deletefolderrecursive"
            requests.get(url_del, params={'username': EMAIL, 'password': PASSWORD, 'folderid': item['folderid']})
            break # Remove uma pasta por vez até ter espaço

def enviar_pcloud(caminho_arquivo, folder_id):
    url = "https://api.pcloud.com/uploadfile"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id, 'nopartial': 1}
    with open(caminho_arquivo, 'rb') as f:
        files = {'file': f}
        r = requests.post(url, params=params, files=files)
    return r.status_code == 200

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt): return

    # 1. Pasta Principal
    id_raiz = obter_ou_criar_pasta("PROGRAMAS_GRAVADOS")
    gerenciar_espaco(id_raiz)

    # 2. Subpasta do Dia (Ex: "Segunda-feira 06-04")
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
            r = requests.get(url, timeout=120)
            
            nome_zip = f"{prog}.zip" # O dia já está no nome da pasta
            with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(bloco, r.content)

            print(f"☁️ Enviando para {nome_subpasta}: {nome_zip}")
            if enviar_pcloud(nome_zip, id_subpasta):
                print(f"✅ SUCESSO!")

            if os.path.exists(nome_zip):
                os.remove(nome_zip)
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    processar('links.txt')
    processar('links_fds.txt')
