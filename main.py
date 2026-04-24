import os
import requests
import re
import datetime
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
    # O GitHub Actions usa UTC, então o dia pode variar dependendo do horário da execução
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
    except Exception as e:
        print(f"Erro ao acessar/criar pasta {nome_pasta}: {e}")
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
            # Extrai o nome do programa e do arquivo mp3 do link
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                prog_nome = match.group(1).replace("_", " ").strip()
                arquivo_nome = match.group(2).replace("_", " ").strip()
            else:
                prog_nome = "GERAL"
                arquivo_nome = f"audio_{int(time.time())}.mp3"

            # Cria/Obtém a pasta específica do programa dentro da pasta do dia
            id_pasta_programa = obter_ou_criar_pasta(prog_nome, id_pasta_dia)

            print(f"⬇️ Baixando: {prog_nome} -> {arquivo_nome}...")
            r = requests.get(url, timeout=300) # Aumentado timeout para arquivos maiores
            r.raise_for_status()

            # Salva temporariamente o arquivo local
            with open(arquivo_nome, 'wb') as f:
                f.write(r.content)

            print(f"☁️ Enviando para pCloud: {nome_pasta_dia}/{prog_nome}/")
            if enviar_pcloud(arquivo_nome, id_pasta_programa):
                print(f"✅ {arquivo_nome} enviado com sucesso!")
            
            # Remove o arquivo temporário local
            if os.path.exists(arquivo_nome):
                os.remove(arquivo_nome)
            
            time.sleep(1) # Pequena pausa para não sobrecarregar a API
        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")

if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Configure PCLOUD_EMAIL e PCLOUD_PASS no GitHub Secrets!")
    else:
        target_file = sys.argv[1] if len(sys.argv) > 1 else 'links.txt'
        print(f"🚀 Iniciando processamento: {target_file}")
        processar(target_file)
