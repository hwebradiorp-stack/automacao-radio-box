import os
import requests
import re
import datetime
import zipfile
import time

# Configurações do GitHub Secrets
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')

# Limite de segurança: se tiver menos de 2GB livres, ele apaga o antigo.
# (1GB = 1024 * 1024 * 1024 bytes)
ESPACO_MINIMO_BYTES = 2 * 1024 * 1024 * 1024 

def get_data_formatada():
    return datetime.datetime.now().strftime("%d-%m")

def gerenciar_espaco(folder_id):
    # 1. Verifica o espaço da conta
    url_user = "https://api.pcloud.com/userinfo"
    res_user = requests.get(url_user, params={'username': EMAIL, 'password': PASSWORD}).json()
    
    quota = res_user.get('quota', 0)
    used = res_user.get('usedquota', 0)
    livre = quota - used
    
    print(f"📊 Espaço no pCloud: {livre / (1024**3):.2f} GB livres.")

    if livre < ESPACO_MINIMO_BYTES:
        print("⚠️ Pouco espaço! Iniciando limpeza de arquivos antigos...")
        
        # 2. Lista arquivos na pasta para apagar os mais velhos
        url_list = "https://api.pcloud.com/listfolder"
        res_list = requests.get(url_list, params={'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id}).json()
        
        arquivos = res_list.get('metadata', {}).get('contents', [])
        # Ordena por data de criação (mais antigos primeiro)
        arquivos_ordenados = sorted(arquivos, key=lambda x: x['created'])

        for arq in arquivos_ordenados:
            if not arq['isfolder']:
                print(f"🗑️ Apagando arquivo antigo: {arq['name']}")
                url_del = "https://api.pcloud.com/deletefile"
                requests.get(url_del, params={'username': EMAIL, 'password': PASSWORD, 'fileid': arq['fileid']})
                
                # Re-verifica o espaço após deletar
                used -= arq['size']
                if (quota - used) > ESPACO_MINIMO_BYTES:
                    print("✅ Espaço suficiente liberado.")
                    break

def obter_ou_criar_pasta(nome_pasta):
    url_list = "https://api.pcloud.com/listfolder"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': 0}
    
    try:
        r = requests.get(url_list, params=params).json()
        for item in r.get('metadata', {}).get('contents', []):
            if item['name'] == nome_pasta and item['isfolder']:
                return item['folderid']
        
        url_create = "https://api.pcloud.com/createfolder"
        params_create = {'username': EMAIL, 'password': PASSWORD, 'name': nome_pasta, 'folderid': 0}
        r_create = requests.get(url_create, params=params_create).json()
        return r_create.get('metadata', {}).get('folderid')
    except:
        return 0

def enviar_pcloud(caminho_arquivo, folder_id):
    url = "https://api.pcloud.com/uploadfile"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id, 'nopartial': 1}
    
    try:
        with open(caminho_arquivo, 'rb') as f:
            files = {'file': f}
            r = requests.post(url, params=params, files=files)
        return r.status_code == 200
    except:
        return False

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt): return

    id_pasta = obter_ou_criar_pasta("PROGRAMAS_GRAVADOS")
    
    # Roda a limpeza antes de começar os novos uploads
    gerenciar_espaco(id_pasta)

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            prog = match.group(1).replace("_", " ").strip() if match else "PROGRAMA"
            bloco = match.group(2).replace("_", " ").strip() if match else "audio.mp3"

            print(f"⬇️ Baixando: {prog}...")
            r = requests.get(url, timeout=120)
            
            # ZIP com a data
            nome_zip = f"{prog}_{get_data_formatada()}.zip"
            with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(bloco, r.content)

            print(f"☁️ Enviando: {nome_zip}")
            if enviar_pcloud(nome_zip, id_pasta):
                print(f"✅ SUCESSO!")
            else:
                print(f"❌ Falha no upload.")

            if os.path.exists(nome_zip):
                os.remove(nome_zip)
            
            time.sleep(2)
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Verifique os Secrets no GitHub!")
    else:
        processar('links.txt')
        processar('links_fds.txt')
