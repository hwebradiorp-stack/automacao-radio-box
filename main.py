import os
import requests
import re
from mega import Mega

# Credenciais vindas do GitHub Secrets
EMAIL = os.getenv('MEGA_EMAIL')
PASSWORD = os.getenv('MEGA_PASSWORD')

def processar_radio():
    # Login no Mega
    mega = Mega()
    try:
        m = mega.login(EMAIL, PASSWORD)
        print("✅ Login no Mega.nz realizado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao logar no Mega: {e}")
        return

    # 1. Garante que a pasta principal PROGRAMAS_GRAVADOS existe
    folder_root = m.find('PROGRAMAS_GRAVADOS')
    if not folder_root:
        print("📁 Criando pasta principal: PROGRAMAS_GRAVADOS")
        folder_root = m.create_folder('PROGRAMAS_GRAVADOS')
    
    # Pegamos o ID da pasta principal (é uma lista, pegamos o primeiro item)
    root_id = folder_root['PROGRAMAS_GRAVADOS']

    # Verifica arquivo de links
    if not os.path.exists('links.txt'):
        print("❌ Erro: Arquivo links.txt nao encontrado.")
        return

    with open('links.txt', 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            # Extrai Nome do Programa e do Bloco
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                nome_programa = match.group(1).replace("_", " ").strip()
                nome_bloco = match.group(2).replace("_", " ").strip()
                nome_final_arquivo = f"{nome_programa} - {nome_bloco}"
            else:
                nome_programa = "OUTROS"
                nome_final_arquivo = url.split('/')[-1]

            # 2. Cria ou Localiza a subpasta do programa dentro de PROGRAMAS_GRAVADOS
            sub_folder = m.find(nome_programa)
            if not sub_folder:
                print(f"📂 Criando subpasta para: {nome_programa}")
                m.create_folder(nome_programa, dest=root_id)
                sub_folder = m.find(nome_programa)
            
            prog_folder_id = sub_folder[nome_programa]

            # 3. Download do arquivo
            print(f"⬇️ Baixando: {nome_final_arquivo}...")
            r = requests.get(url, stream=True, timeout=120)
            
            if r.status_code == 200:
                with open(nome_final_arquivo, 'wb') as f_audio:
                    for chunk in r.iter_content(chunk_size=8192):
                        f_audio.write(chunk)

                # 4. Upload para a pasta correta no Mega
                print(f"☁️ Enviando {nome_final_arquivo} para a pasta {nome_programa}...")
                m.upload(nome_final_arquivo, dest=prog_folder_id)
                
                # Limpeza de disco temporario do GitHub
                os.remove(nome_final_arquivo)
                print(f"✅ Concluido!")
            else:
                print(f"⚠️ Erro no download: Status {r.status_code}")

        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")

if __name__ == "__main__":
    processar_radio()
