# -- || Made by @dbl_von || --
import os
import time
import json
import math
import random
import uuid
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# CONFIGURAÇÃO DO ROBLOX
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY")
MODELOS_PERMITIDOS = ("flux", "turbo")

def cor_hex(valor, padrao=(0, 200, 255)):
    try:
        valor = str(valor).lstrip("#")
        return tuple(int(valor[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return padrao

def nome_unico(base):
    return f"{base}_{time.strftime('%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

def baixar_imagem_limpa(prompt_usuario, modelo="flux", seed=None):
    prompt_usuario = str(prompt_usuario).strip()[:300]
    modelo = modelo if modelo in MODELOS_PERMITIDOS else "flux"
    seed = int(seed) if seed not in (None, "") else random.randint(1, 999999)

    prompt_formatado = f"{prompt_usuario}, black background, texture map, video game vfx asset, square tileable, no text, no watermark"
    url_ia = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_formatado)}?width=768&height=768&seed={seed}&model={modelo}&nologo=true"

    resposta_ia = requests.get(url_ia, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    if resposta_ia.status_code != 200:
        print(f"ERRO Pollinations: {resposta_ia.status_code} - {resposta_ia.text[:300]}", flush=True)
        return None, resposta_ia.status_code, seed

    imagem = Image.open(BytesIO(resposta_ia.content)).convert("RGB")
    imagem = imagem.crop((128, 128, 640, 640))

    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue(), 200, seed

def quadro_flare(t, tamanho, cor):
    centro = tamanho / 2
    brilho = 1 - t
    quadro = Image.new("RGB", (tamanho, tamanho), (0, 0, 0))
    desenho = ImageDraw.Draw(quadro)
    raio = 4 + t * 26 * (tamanho / 128)
    cor_raio = tuple(int(c * brilho) for c in cor)

    for r in range(12):
        ang = math.radians(r * 30 + t * 40)
        comp = min(raio * (1.0 + (r % 2) * 0.8), centro - 6)
        fim = (centro + math.cos(ang) * comp, centro + math.sin(ang) * comp)
        desenho.line([(centro, centro), fim], fill=cor_raio, width=max(2, tamanho // 40))

    nucleo = int(255 * brilho)
    n = tamanho / 16
    desenho.ellipse([centro - n, centro - n, centro + n, centro + n], fill=(nucleo, nucleo, nucleo))
    return quadro.filter(ImageFilter.GaussianBlur(max(1, tamanho // 40)))

def quadro_fumaca(t, tamanho, cor):
    rng = random.Random(7)
    centro = tamanho / 2
    quadro = Image.new("RGB", (tamanho, tamanho), (0, 0, 0))
    desenho = ImageDraw.Draw(quadro)
    brilho = (1 - t) ** 1.5

    for _ in range(9):
        dx = rng.uniform(-0.25, 0.25) * tamanho
        dy = rng.uniform(-0.25, 0.25) * tamanho
        base = rng.uniform(0.08, 0.16) * tamanho
        raio = base * (1 + t * 1.8)
        x = centro + dx * (1 + t)
        y = centro + dy * (1 + t) - t * tamanho * 0.1
        c = tuple(int(v * brilho * 0.8) for v in cor)
        desenho.ellipse([x - raio, y - raio, x + raio, y + raio], fill=c)

    return quadro.filter(ImageFilter.GaussianBlur(max(2, tamanho // 12)))

def quadro_faisca(t, tamanho, cor):
    rng = random.Random(21)
    centro = tamanho / 2
    quadro = Image.new("RGB", (tamanho, tamanho), (0, 0, 0))
    desenho = ImageDraw.Draw(quadro)
    brilho = 1 - t

    for _ in range(16):
        ang = rng.uniform(0, math.tau)
        vel = rng.uniform(0.4, 0.95)
        dist = vel * t * centro
        x = centro + math.cos(ang) * dist
        y = centro + math.sin(ang) * dist
        r = max(1.5, tamanho / 40) * (1 + brilho)
        desenho.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * brilho) for v in cor))
        desenho.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=(int(255 * brilho),) * 3)

    return quadro.filter(ImageFilter.GaussianBlur(1))

ESTILOS = {"flare": quadro_flare, "fumaca": quadro_fumaca, "faisca": quadro_faisca}

def gerar_flipbook(estilo="flare", cor=(0, 200, 255), grade=4):
    grade = grade if grade in (2, 4, 8) else 4
    tamanho = 512 // grade
    funcao = ESTILOS.get(estilo, quadro_flare)
    folha = Image.new("RGB", (grade * tamanho, grade * tamanho), (0, 0, 0))
    total = grade * grade

    for i in range(total):
        t = i / (total - 1)
        folha.paste(funcao(t, tamanho, cor), ((i % grade) * tamanho, (i // grade) * tamanho))

    saida = BytesIO()
    folha.save(saida, format="PNG")
    return saida.getvalue()

def subir_roblox(imagem_bytes, nome, descricao):
    url_roblox_upload = "https://apis.roblox.com/assets/v1/assets"
    headers_roblox = {"x-api-key": ROBLOX_API_KEY}

    json_meta = {
        "assetType": "Decal",
        "displayName": nome,
        "description": descricao,
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
        return None, f"Roblox recusou o envio. Status: {resposta_roblox.status_code} - {resposta_roblox.text}"

    dados_operacao = resposta_roblox.json()
    operation_path = dados_operacao.get("path")

    if not operation_path:
        asset_id = dados_operacao.get("assetId")
        if asset_id:
            return str(asset_id), None
        return None, "Roblox aceitou, mas nao gerou codigo de rastreamento."

    url_checagem = f"https://apis.roblox.com/assets/v1/{operation_path}"

    for _ in range(10):
        time.sleep(2)
        status_resposta = requests.get(url_checagem, headers=headers_roblox, timeout=10)

        if status_resposta.status_code == 200:
            dados_status = status_resposta.json()
            if dados_status.get("done") == True:
                response_obj = dados_status.get("response", {})
                asset_id = response_obj.get("assetId")
                if asset_id:
                    return str(asset_id), None
                break

    return None, "O Roblox demorou para responder na fila de processamento."

@app.route("/", methods=["GET"])
def home():
    return "Servidor de IA VFX do Roblox ativo, online e GRATUITO!", 200

@app.route("/preview", methods=["GET"])
def preview():
    prompt_usuario = request.args.get("prompt")

    if not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    try:
        imagem_bytes, status, seed = baixar_imagem_limpa(
            prompt_usuario,
            request.args.get("modelo", "flux"),
            request.args.get("seed")
        )
        if imagem_bytes is None:
            return jsonify({"sucesso": False, "erro": f"A IA Pollinations falhou. Status: {status}"}), 500
        resposta = Response(imagem_bytes, mimetype="image/png")
        resposta.headers["X-Seed"] = str(seed)
        return resposta
    except Exception as e:
        print(f"ERRO interno: {str(e)}", flush=True)
        return jsonify({"sucesso": False, "erro": f"Erro interno no servidor Python: {str(e)}"}), 500

@app.route("/flipbook-preview", methods=["GET"])
def flipbook_preview():
    estilo = request.args.get("estilo", "flare")
    cor = cor_hex(request.args.get("cor", "00c8ff"))
    grade = int(request.args.get("grade", 4))

    try:
        return Response(gerar_flipbook(estilo, cor, grade), mimetype="image/png")
    except Exception as e:
        print(f"ERRO interno: {str(e)}", flush=True)
        return jsonify({"sucesso": False, "erro": f"Erro interno no servidor Python: {str(e)}"}), 500

@app.route("/gerar-textura", methods=["POST"])
def gerar_textura():
    dados = request.json or {}
    tipo = dados.get("tipo", "imagem")
    prompt_usuario = dados.get("prompt")

    if tipo != "flipbook" and not prompt_usuario:
        return jsonify({"sucesso": False, "erro": "Prompt vazio"}), 400

    if not ROBLOX_API_KEY:
        print("ERRO: ROBLOX_API_KEY nao configurada no Render", flush=True)
        return jsonify({"sucesso": False, "erro": "ROBLOX_API_KEY nao configurada no servidor"}), 500

    try:
        seed = None
        if tipo == "flipbook":
            estilo = dados.get("estilo", "flare")
            cor = cor_hex(dados.get("cor", "00c8ff"))
            grade = int(dados.get("grade", 4))
            imagem_bytes = gerar_flipbook(estilo, cor, grade)
            nome = nome_unico("IA_VFX_Flipbook")
            descricao = "Flipbook de VFX gerado por codigo"
        else:
            imagem_bytes, status, seed = baixar_imagem_limpa(
                prompt_usuario,
                dados.get("modelo", "flux"),
                dados.get("seed")
            )
            if imagem_bytes is None:
                return jsonify({"sucesso": False, "erro": f"A IA Pollinations falhou. Status: {status}"}), 500
            nome = nome_unico("IA_VFX_Texture")
            descricao = "Textura de VFX gerada por IA"

        asset_id, erro = subir_roblox(imagem_bytes, nome, descricao)

        if asset_id:
            return jsonify({"sucesso": True, "assetId": asset_id, "nome": nome, "seed": seed})
        return jsonify({"sucesso": False, "erro": erro}), 500

    except Exception as e:
        print(f"ERRO interno: {str(e)}", flush=True)
        return jsonify({"sucesso": False, "erro": f"Erro interno no servidor Python: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
