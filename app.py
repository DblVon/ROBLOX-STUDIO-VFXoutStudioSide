# -- || Made by @dbl_von || --
import os
import time
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURAÇÃO DO ROBLOX
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA VFX do Roblox ativo, online e GRATUITO!", 200

@app.route("/gerar-textura", methods=["POST"])
def gerar_textura():
    dados = request.json or {}
    prompt_usuario = dados.get("prompt")
    
    if not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    try:
        # ---- PASSO 1: Baixando Imagem da IA (Pollinations) ----
        prompt_formatado = f"{prompt_usuario}, black background, texture map, video game vfx asset, square tileable"
        url_ia = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_formatado)}?width=512&height=512&seed=42"
        
        resposta_ia = requests.get(url_ia, timeout=15)
        if resposta_ia.status_code != 200:
            return jsonify({"sucesso": False, "erro": f"A IA Pollinations falhou. Status: {resposta_ia.status_code}"}), 500
            
        imagem_bytes = resposta_ia.content

        # ---- PASSO 2: Envio para a Assets API do Roblox ----
        url_roblox_upload = "https://apis.roblox.com/assets/v1/assets"
        headers_roblox = {"x-api-key": ROBLOX_API_KEY}
        
        json_meta = {
            "assetType": "Decal",
            "displayName": "IA_VFX_Texture",
            "description": f"Gerado por IA. Prompt: {prompt_usuario}",
            "creationContext": {
                "creator": {
                    "userId": "3410584211" # Seu ID de usuario
                }
            }
        }

        arquivos = {
            'request': (None, json.dumps(json_meta), 'application/json'),
            'fileContent': ('textura.png', imagem_bytes, 'image/png')
        }

        resposta_roblox = requests.post(url_roblox_upload, headers=headers_roblox, files=arquivos, timeout=20)
        
        if not (200 <= resposta_roblox.status_code < 300):
            return jsonify({"sucesso": False, "erro": f"Roblox recusou o envio. Status: {resposta_roblox.status_code} - {resposta_roblox.text}"}), 500
            
        dados_operacao = resposta_roblox.json()
        operation_path = dados_operacao.get("path")
        
        if not operation_path:
            asset_id = dados_operacao.get("assetId")
            if asset_id:
                return jsonify({"sucesso": True, "assetId": str(asset_id)})
            return jsonify({"sucesso": False, "erro": "Roblox aceitou, mas nao gerou codigo de rastreamento."}), 500

        # ---- PASSO 3: Consulta ao Caminho da Operação ----
        url_checagem = f"https://apis.roblox.com/assets/v1/{operation_path}"
        asset_id = None
        
        for _ in range(10):
            time.sleep(2)
            status_resposta = requests.get(url_checagem, headers=headers_roblox, timeout=10)
            
            if status_resposta.status_code == 200:
                dados_status = status_resposta.json()
                if dados_status.get("done") == True:
                    response_obj = dados_status.get("response", {})
                    asset_id = response_obj.get("assetId")
                    break
                    
        if asset_id:
            return jsonify({
                "sucesso": True,
                "assetId": str(asset_id)
            })
        else:
            return jsonify({"sucesso": False, "erro": "O Roblox demorou para responder na fila de processamento."}), 500

    except Exception as e:
        return jsonify({"sucesso": False, "erro": f"Erro interno no servidor Python: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
