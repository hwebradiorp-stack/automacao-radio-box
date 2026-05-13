import os
import requests
import re
import datetime
import time
import sys

# Configurações do GitHub Secrets
EMAIL = os.getenv('PCLOUD_EMAIL')
PASSWORD = os.getenv('PCLOUD_PASS')
# Se sua conta for Europeia, use: https://eapi.pcloud.com
BASE_URL = "https://api.pcloud.com" 
ESPACO_MINIMO_BYTES = 2 * 1024 * 1024 * 1024 

def get_pasta_do_dia():
    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    agora = datetime.datetime.now()
    dia_semana = dias[agora.weekday()]
    data = agora.strftime("%d-%m")
    return f"{dia_semana} {data}"

def obter_ou_criar_pasta(nome_pasta, parent_id=0):
    url_list = f"{BASE_URL}/listfolder"
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': parent_id}
    try:
        r = requests.get(url_list, params=params).json()
        if r.get('result') == 0:
            for item in r.get('metadata', {}).get('contents', []):
                if item['name'] == nome_pasta and item['isfolder']:
                    return item['folderid']
        
        # Se não achou, cria
        url_create = f"{BASE_URL}/createfolder"
        params_create = {'username': EMAIL, 'password': PASSWORD, 'name': nome_pasta, 'folderid': parent_id}
        r_create = requests.get(url_create, params=params_create).json()
        
        if r_create.get('result') == 0:
            return r_create.get('metadata', {}).get('folderid')
        else:
            print(f"⚠️ Erro pCloud ao criar pasta: {r_create.get('error')}")
            return parent_id
    except Exception as e:
        print(f"Erro ao acessar/criar pasta {nome_pasta}: {e}")
        return parent_id

def gerenciar_espaco(folder_id):
    try:
        res_user = requests.get(f"{BASE_URL}/userinfo", params={'username': EMAIL, 'password': PASSWORD}).json()
        quota = res_user.get('quota', 0)
        used = res_user.get('usedquota', 0)
        livre = quota - used
        
        if livre < ESPACO_MINIMO_BYTES:
            print(f"⚠️ Espaço crítico ({livre/(1024**3):.2f}GB). Limpando pastas antigas...")
            res_list = requests.get(f"{BASE_URL}/listfolder", params={'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id}).json()
            itens = res_list.get('metadata', {}).get('contents', [])
            itens_ordenados = sorted(itens, key=lambda x: x.get('created', 0))
            if itens_ordenados:
                velha = itens_ordenados[0]
                print(f"🗑️ Removendo pasta antiga: {velha['name']}")
                requests.get(f"{BASE_URL}/deletefolderrecursive", params={'username': EMAIL, 'password': PASSWORD, 'folderid': velha['folderid']})
    except:
        pass

def enviar_pcloud(caminho_arquivo, folder_id):
    url = f"{BASE_URL}/uploadfile"
    # IMPORTANTE: Passamos credenciais nos params e o arquivo no files
    params = {'username': EMAIL, 'password': PASSWORD, 'folderid': folder_id, 'nopartial': 1}
    try:
        with open(caminho_arquivo, 'rb') as f:
            files = {'file': (os.path.basename(caminho_arquivo), f)}
            r = requests.post(url, params=params, files=files)
            resultado = r.json()
            if resultado.get('result') == 0:
                return True
            else:
                print(f"❌ Erro no upload pCloud: {resultado.get('error')}")
                return False
    except Exception as e:
        print(f"❌ Falha técnica no upload: {e}")
        return False

def processar(arquivo_txt):
    if not os.path.exists(arquivo_txt):
        print(f"❌ Arquivo {arquivo_txt} não encontrado.")
        return

    id_raiz = obter_ou_criar_pasta("PROGRAMAS_GRAVADOS")
    gerenciar_espaco(id_raiz)
    
    nome_pasta_dia = get_pasta_do_dia()
    id_pasta_dia = obter_ou_criar_pasta(nome_pasta_dia, id_raiz)

    with open(arquivo_txt, 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog_nome = match.group(1).replace("_", " ").strip()
                arquivo_nome = match.group(2).replace("_", " ").strip()
            else:
                prog_nome = "GERAL"
                arquivo_nome = f"audio_{int(time.time())}.mp3"

            id_pasta_programa = obter_ou_criar_pasta(prog_nome, id_pasta_dia)

            print(f"⬇️ Baixando: {arquivo_nome}...")
            r = requests.get(url, timeout=600) 
            r.raise_for_status()

            with open(arquivo_nome, 'wb') as f:
                f.write(r.content)

            print(f"☁️ Enviando para pCloud...")
            if enviar_pcloud(arquivo_nome, id_pasta_programa):
                print(f"✅ {arquivo_nome} enviado com sucesso!")
            
            if os.path.exists(arquivo_nome):
                os.remove(arquivo_nome)
            
            time.sleep(2) 
        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")

if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Faltam credenciais PCLOUD_EMAIL e PCLOUD_PASS!")
    else:
        target_file = sys.argv[1] if len(sys.argv) > 1 else 'links.txt'
        processar(target_file)
