import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURAÇÕES (Armazenadas de forma segura na nuvem)
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA VFX do Roblox ativo e online!", 200

@app.route("/gerar-textura", methods=["POST"])
def gerar_textura():
    dados = request.json
    prompt_usuario = dados.get("prompt")
    
    if not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    try:
        # ---- PASSO 1: Chamar a IA para gerar a Imagem (Exemplo usando OpenAI DALL-E) ----
        headers_ai = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        payload_ai = {
            "prompt": f"{prompt_usuario}, black background, texture map, tileable, video game vfx asset",
            "n": 1,
            "size": "512x512", # Tamanho ideal e econômico para VFX no Roblox
            "response_format": "url"
        }
        
        resposta_ai = requests.post("https://openai.com", json=payload_ai, headers=headers_ai)
        url_imagem = resposta_ai.json()['data'][0]['url']
        
        # Baixa a imagem gerada temporariamente na memória
        imagem_bytes = requests.get(url_imagem).content

        # ---- PASSO 2: Enviar a Imagem para o Roblox usando Open Cloud API ----
        # O Roblox exige o envio de arquivos multipart para upload de Assets
        url_roblox_upload = "https://roblox.com"
        headers_roblox = {"x-api-key": ROBLOX_API_KEY}
        
        # Dados necessários exigidos pelo protocolo do Roblox
        json_meta = {
            "assetType": "Decal",
            "displayName": "IA_VFX_Texture",
            "description": f"Gerado automaticamente por IA. Prompt: {prompt_usuario}",
            "creationContext": {
                "creator": {
                    "userId": "COLOQUE_SEU_USER_ID_AQUI" # Insira o ID numérico da sua conta do Roblox
                }
            }
        }

        arquivos = {
            'request': (None, requests.utils.to_key_val_list(json_meta), 'application/json'),
            'fileContent': ('textura.png', imagem_bytes, 'image/png')
        }

        # Envia para a Open Cloud do Roblox
        resposta_roblox = requests.post(url_roblox_upload, headers=headers_roblox, files=arquivos)
        
        if resposta_roblox.status_code == 200 or resposta_roblox.status_code == 201:
            dados_roblox = resposta_roblox.json()
            # O Roblox retorna um operation ID ou diretamente o assetId se o processamento for imediato
            asset_id = dados_roblox.get("assetId")
            
            return jsonify({
                "sucesso": True,
                "assetId": asset_id
            })
        else:
            return jsonify({"sucesso": False, "erro": f"Erro no upload do Roblox: {resposta_roblox.text}"}), 500

    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
