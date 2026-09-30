import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURAÇÃO DO ROBLOX (Armazenada de forma segura nas configurações do Render)
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA VFX do Roblox ativo, online e GRATUITO!", 200

@app.route("/gerar-textura", methods=["POST"])
def gerar_textura():
    dados = request.json
    prompt_usuario = dados.get("prompt")
    
    if not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    try:
        # ---- PASSO 1: Chamar a IA Gratuita (Pollinations.ai) ----
        # Formatamos o prompt para garantir que seja uma textura de VFX ideal
        prompt_formatado = f"{prompt_usuario}, black background, texture map, video game vfx asset, square tileable"
        
        # O Pollinations gera a imagem direto via URL estruturada
        url_ia = f"https://pollinations.ai{requests.utils.quote(prompt_formatado)}?width=512&height=512&enhance=true&seed=42"
        
        # Baixa os bytes da imagem criada pela IA
        resposta_ia = requests.get(url_ia)
        if resposta_ia.status_code != 200:
            return jsonify({"sucesso": False, "erro": "A IA gratuita falhou em gerar a imagem."}), 500
            
        imagem_bytes = resposta_ia.content

        # ---- PASSO 2: Enviar a Imagem para o Roblox usando Open Cloud API ----
        url_roblox_upload = "https://roblox.com"
        headers_roblox = {"x-api-key": ROBLOX_API_KEY}
        
        json_meta = {
            "assetType": "Decal",
            "displayName": "IA_VFX_Texture",
            "description": f"Gerado automaticamente por IA. Prompt: {prompt_usuario}",
            "creationContext": {
                "creator": {
                    "userId": "3410584211"  # Opcional: Coloque o ID numérico da sua conta do Roblox se quiser associar diretamente
                }
            }
        }

        arquivos = {
            'request': (None, requests.utils.to_key_val_list(json_meta), 'application/json'),
            'fileContent': ('textura.png', imagem_bytes, 'image/png')
        }

        # Envia a imagem para a nuvem do Roblox
        resposta_roblox = requests.post(url_roblox_upload, headers=headers_roblox, files=arquivos)
        
        if resposta_roblox.status_code in [200, 201]:
            dados_roblox = resposta_roblox.json()
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
