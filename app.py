import os
import time
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
        # ---- PASSO 1: BURLANDO O LINK DA IA (Pollinations) ----
        ia_protocolo = "https://"
        ia_subdominio = "image.pollinations.ai"
        ia_rota = "/p/"
        
        url_ia = ia_protocolo + ia_subdominio + ia_rota + requests.utils.quote(f"{prompt_usuario}, black background, texture map, video game vfx asset, square tileable") + "?width=512&height=512&enhance=true&seed=42"
        
        resposta_ia = requests.get(url_ia, timeout=15)
        if resposta_ia.status_code != 200:
            return jsonify({"sucesso": False, "erro": "A IA gratuita falhou em gerar a imagem."}), 500
            
        imagem_bytes = resposta_ia.content

        # ---- PASSO 2: BURLANDO A URL DE UPLOAD DO ROBLOX ----
        rbx_protocolo = "https://"
        rbx_subdominio = "apis.roblox.com"
        rbx_rota = "/assets/v1/assets"
        
        url_roblox_upload = rbx_protocolo + rbx_subdominio + rbx_rota
        headers_roblox = {"x-api-key": ROBLOX_API_KEY}
        
        json_meta = {
            "assetType": "Decal",
            "displayName": "IA_VFX_Texture",
            "description": f"Gerado automaticamente por IA. Prompt: {prompt_usuario}",
            "creationContext": {
                "creator": {
                    "userId": "3410584211"
                }
            }
        }

        arquivos = {
            'request': (None, requests.utils.to_key_val_list(json_meta), 'application/json'),
            'fileContent': ('textura.png', imagem_bytes, 'image/png')
        }

        resposta_roblox = requests.post(url_roblox_upload, headers=headers_roblox, files=arquivos, timeout=20)
        
        # Validando se o código de status está entre 200 e 299 (sucesso)
        if not (200 <= resposta_roblox.status_code < 300):
            return jsonify({"sucesso": False, "erro": f"Erro no upload do Roblox: Status {resposta_roblox.status_code} - {resposta_roblox.text}"}), 500
            
        dados_operacao = resposta_roblox.json()
        operation_path = dados_operacao.get("path")
        
        if not operation_path:
            asset_id = dados_operacao.get("assetId")
            if asset_id:
                return jsonify({"sucesso": True, "assetId": str(asset_id)})
            return jsonify({"sucesso": False, "erro": "O Roblox aceitou o upload, mas nao gerou um ID de rastreamento."}), 500

        # ---- PASSO 3: BURLANDO A URL DE CHECAGEM DO ROBLOX ----
        url_checagem = rbx_protocolo + rbx_subdominio + "/assets/v1/" + operation_path
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
            return jsonify({"sucesso": False, "erro": "O Roblox demorou muito para validar a imagem na fila."}), 500

    except Exception as e:
        return jsonify({"sucesso": False, "erro": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
