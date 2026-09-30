# -- || Made by @dbl_von || --
import os
import time
import json
import requests
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# CONFIGURAÇÃO DO ROBLOX
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")

def baixar_imagem_limpa(prompt_usuario):
    prompt_formatado = f"{prompt_usuario}, black background, texture map, video game vfx asset, square tileable, no text, no watermark"
    url_ia = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_formatado)}?width=768&height=768&seed=42&nologo=true"

    resposta_ia = requests.get(url_ia, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    if resposta_ia.status_code != 200:
        print(f"ERRO Pollinations: {resposta_ia.status_code} - {resposta_ia.text[:300]}", flush=True)
        return None, resposta_ia.status_code

    imagem = Image.open(BytesIO(resposta_ia.content)).convert("RGB")
    imagem = imagem.crop((128, 128, 640, 640))

    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue(), 200

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA VFX do Roblox ativo, online e GRATUITO!", 200

@app.route("/preview", methods=["GET"])
def preview():
    prompt_usuario = request.args.get("prompt")

    if not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    try:
        imagem_bytes, status = baixar_imagem_limpa(prompt_usuario)
        if imagem_bytes is None:
            return jsonify({"sucesso": False, "erro": f"A IA Pollinations falhou. Status: {status}"}), 500
        return Response(imagem_bytes, mimetype="image/png")
    except Exception as e:
        print(f"ERRO interno: {str(e)}", flush=True)
        return jsonify({"sucesso": False, "erro": f"Erro interno no servidor Python: {str(e)}"}), 500

@app.route("/gerar-textura", methods=["POST"])
def gerar_textura():
    dados = request.json or {}
    prompt_usuario = dados.get("prompt")
    
    if not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    if not ROBLOX_API_KEY:
        print("ERRO: ROBLOX_API_KEY nao configurada no Render", flush=True)
        return jsonify({"sucesso": False, "erro": "ROBLOX_API_KEY nao configurada no servidor"}), 500

    try:
        # ---- PASSO 1: Baixando Imagem da IA (Pollinations) ----
        imagem_bytes, status = baixar_imagem_limpa(prompt_usuario)
        if imagem_bytes is None:
            return jsonify({"sucesso": False, "erro": f"A IA Pollinations falhou. Status: {status}"}), 500

        # ---- PASSO 2: Envio para a Assets API do Roblox ----
        url_roblox_upload = "https://apis.roblox.com/assets/v1/assets"
        headers_roblox = {"x-api-key": ROBLOX_API_KEY}
        
        json_meta = {
            "assetType": "Decal",
            "displayName": "IA_VFX_Texture",
            "description": "Textura de VFX gerada por IA",
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

        resposta_roblox = requests.post(url_roblox_upload, headers=headers_roblox, files=arquivos, timeout=30)
        
        if not (200 <= resposta_roblox.status_code < 300):
            print(f"ERRO Roblox upload: {resposta_roblox.status_code} - {resposta_roblox.text}", flush=True)
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
        print(f"ERRO interno: {str(e)}", flush=True)
        return jsonify({"sucesso": False, "erro": f"Erro interno no servidor Python: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
