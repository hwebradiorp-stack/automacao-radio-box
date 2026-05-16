import os
import requests
import re
import datetime
import time
import sys

# Pega direto dos Secrets do GitHub
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')
BASE_URL = "https://api.pcloud.com"

def obter_ou_criar_pasta(nome_pasta, parent_id=0):
    url_list = f"{BASE_URL}/listfolder"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': parent_id}
    try:
        r = requests.get(url_list, params=params).json()
        # Se a pasta já existir, pega o ID dela
        if r.get('result') == 0:
            for item in r.get('metadata', {}).get('contents', []):
                if item['name'] == nome_pasta and item['isfolder']:
                    return item['folderid']
        
        # Se não existir, cria uma nova
        url_create = f"{BASE_URL}/createfolder"
        params_create = {'username': EMAIL, 'password': PASSWORD, 'name': nome_pasta, 'folderid': parent_id}
        r_create = requests.get(url_create, params=params_create).json()
        return r_create.get('metadata', {}).get('folderid', parent_id)
    except:
        return parent_id

def enviar_pcloud(caminho_arquivo, folder_id):
    url = f"{BASE_URL}/uploadfile"
    # Passa e-mail e senha direto nos parâmetros junto com a pasta
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id, 'nopartial': 1}
    try:
        with open(caminho_arquivo, 'rb') as f:
            files = {'file': (os.path.basename(caminho_arquivo), f)}
            r = requests.post(url, params=params, files=files).json()
            return r.get('result') == 0
    except:
        return False

def processar(arquivo_txt):
    if not EMAIL or not PASSWORD:
        print("❌ Configure PCLOUD_EMAIL e PCLOUD_PASS no GitHub!")
        return

    print("🚀 Iniciando upload usando E-mail e Senha...")
    
    # Cria a pasta principal
    id_raiz = obter_ou_criar_pasta("PROGRAMAS_GRAVADOS")
    
    # Cria a pasta do dia (Ex: 16-05)
    nome_pasta_dia = datetime.datetime.now().strftime('%d-%m')
    id_pasta_dia = obter_ou_criar_pasta(nome_pasta_dia, id_raiz)

    if not os.path.exists(arquivo_txt):
        print(f"❌ Arquivo {arquivo_txt} não encontrado.")
        return

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            # Separa o nome do programa e do arquivo
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog_nome = match.group(1).replace("_", " ").strip()
                arquivo_nome = match.group(2).replace("_", " ").strip()
            else:
                prog_nome = "GERAL"
                arquivo_nome = f"audio_{int(time.time())}.mp3"

            # Cria a pasta do programa dentro da pasta do dia
            id_pasta_programa = obter_ou_criar_pasta(prog_nome, id_pasta_dia)

            print(f"⬇️ Baixando: {arquivo_nome}...")
            r = requests.get(url, timeout=300)
            r.raise_for_status()

            # Salva o arquivo local temporariamente
            with open(arquivo_nome, 'wb') as f:
                f.write(r.content)

            print(f"☁️ Enviando para pCloud: {nome_pasta_dia}/{prog_nome}/")
            if enviar_pcloud(arquivo_nome, id_pasta_programa):
                print(f"✅ {arquivo_nome} enviado com sucesso!")
            else:
                print(f"❌ Falha ao enviar {arquivo_nome}")
            
            # Limpa o arquivo local
            if os.path.exists(arquivo_nome):
                os.remove(arquivo_nome)
            
            # Pausa de 2 segundos para o pCloud não bloquear por excesso de velocidade
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Erro ao processar o link: {e}")

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else 'links.txt'
    processar(target_file)
