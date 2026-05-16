import os
import requests
import re
import datetime
import time
import sys

def processar(arquivo_txt):
    print(f"🚀 Iniciando processamento dos links do arquivo: {arquivo_txt}...")
    
    # Cria a estrutura de pastas local: PROGRAMAS_GRAVADOS/DD-MM
    nome_pasta_dia = datetime.datetime.now().strftime('%d-%m')
    pasta_destino_raiz = os.path.join("PROGRAMAS_GRAVADOS", nome_pasta_dia)

    if not os.path.exists(arquivo_txt):
        print(f"❌ Arquivo de links '{arquivo_txt}' não encontrado.")
        return

    # Lê os links válidos do arquivo de texto
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if "http" in line]

    if not links:
        print("⚠️ Nenhum link válido encontrado no arquivo de texto.")
        return

    for url in links:
        try:
            # Separa o nome do programa e do arquivo .mp3 pela URL
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                # Remove os underlines para deixar as pastas limpas e legíveis no GitHub
                prog_nome = match.group(1).replace("_", " ").strip()
                arquivo_nome = match.group(2).strip()
            else:
                prog_nome = "GERAL"
                arquivo_nome = f"audio_{int(time.time())}.mp3"

            # Define o caminho completo da pasta do programa específico
            pasta_programa = os.path.join(pasta_destino_raiz, prog_nome)
            os.makedirs(pasta_programa, exist_ok=True)

            caminho_final_arquivo = os.path.join(pasta_programa, arquivo_nome)

            # Verifica se o arquivo já foi baixado antes para poupar banda
            if os.path.exists(caminho_final_arquivo):
                print(f"⏩ {arquivo_nome} já existe no repositório. Pulando...")
                continue

            print(f"⬇️ Baixando: {arquivo_nome} para a pasta {prog_nome}...")
            r = requests.get(url, timeout=300)
            r.raise_for_status()

            # Salva o arquivo permanentemente na pasta para o Git comitar depois
            with open(caminho_final_arquivo, 'wb') as f:
                f.write(r.content)
            print(f"✅ {arquivo_nome} baixado e guardado com sucesso!")
            
            # Pequena pausa apenas para gerenciar requisições do servidor de áudio
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro ao processar o link [{url}]: {e}")

if __name__ == "__main__":
    # Permite passar links.txt ou links_fds.txt por argumento no terminal/actions
    target_file = sys.argv[1] if len(sys.argv) > 1 else 'links.txt'
    processar(target_file)
