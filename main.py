import os
import requests
import re
import datetime
from mega import Mega

# Credenciais do GitHub Secrets
EMAIL = os.getenv('MEGA_EMAIL')
PASSWORD = os.getenv('MEGA_PASSWORD')

def get_data_formatada():
    # Configura o nome do dia em português e a data para a pasta
    dias = ["Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"]
    agora = datetime.datetime.now()
    dia_semana = dias[agora.weekday()]
    data_str = agora.strftime("%d-%m-%Y")
    return f"{dia_semana} {data_str}"

def processar_radio():
    mega = Mega()
    try:
        m = mega.login(EMAIL, PASSWORD)
        print("✅ Login no Mega.nz realizado!")
    except Exception as e:
        print(f"❌ Erro login Mega: {e}")
        return

    # 1. Pasta Raiz: PROGRAMAS_GRAVADOS
    folder_root = m.find('PROGRAMAS_GRAVADOS')
    if not folder_root:
        print("📁 Criando pasta principal: PROGRAMAS_GRAVADOS")
        folder_root = m.create_folder('PROGRAMAS_GRAVADOS')
    root_id = folder_root['PROGRAMAS_GRAVADOS']

    # 2. Subpasta com a DATA (Ex: Sexta-feira 27-03-2026)
    nome_dia = get_data_formatada()
    folder_dia = m.find(nome_dia)
    if not folder_dia:
        print(f"📁 Criando pasta do dia: {nome_dia}")
        m.create_folder(nome_dia, dest=root_id)
        folder_dia = m.find(nome_dia)
    dia_id = folder_dia[nome_dia]

    # Verifica arquivo de links
    if not os.path.exists('links.txt'):
        print("❌ Erro: links.txt nao encontrado.")
        return

    with open('links.txt', 'r') as f:
        links = [line.strip() for line in f if "http" in line]

    for url in links:
        try:
            # Extrai Nome do Programa e Bloco para o arquivo e para a pasta
            match = re.search(r"musica=(.*?)/(.*?\.mp3)", url)
            if match:
                nome_programa = match.group(1).replace("_", " ").strip()
                nome_bloco = match.group(2).replace("_", " ").strip()
                # Mantém o nome do programa e bloco no arquivo MP3
                nome_final_arquivo = f"{nome_programa} - {nome_bloco}"
            else:
                nome_programa = "OUTROS"
                nome_final_arquivo = url.split('/')[-1]

            # 3. Subpasta do Programa dentro da pasta da DATA
            # Procuramos se a pasta do programa já existe dentro da pasta do dia
            sub_folder = m.find(nome_programa)
            if not sub_folder:
                print(f"📂 Criando pasta do programa: {nome_programa}")
                m.create_folder(nome_programa, dest=dia_id)
                sub_folder = m.find(nome_programa)
            
            prog_folder_id = sub_folder[nome_programa]

            # 4. Download e Upload
            print(f"⬇️ Baixando: {nome_final_arquivo}...")
            r = requests.get(url, stream=True, timeout=120)
            
            if r.status_code == 200:
                with open(nome_final_arquivo, 'wb') as f_audio:
                    for chunk in r.iter_content(chunk_size=8192):
                        f_audio.write(chunk)

                print(f"☁️ Enviando {nome_final_arquivo} para: {nome_dia} > {nome_programa}")
                m.upload(nome_final_arquivo, dest=prog_folder_id)
                
                # Limpa o arquivo temporário do GitHub
                os.remove(nome_final_arquivo)
                print(f"✅ Sucesso!")
            else:
                print(f"⚠️ Erro no download: {r.status_code}")

        except Exception as e:
            print(f"❌ Erro ao processar {url}: {e}")

if __name__ == "__main__":
    processar_radio()
