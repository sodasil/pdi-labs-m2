import json
import os
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np
import pytest

ARQUIVO_TESTE = Path(__file__).resolve()
PASTA_TESTES = ARQUIVO_TESTE.parent
RAIZ_PROJETO = PASTA_TESTES.parent
caminhos_busca = [
    RAIZ_PROJETO / "src",
    RAIZ_PROJETO,
]
for caminho in caminhos_busca:
    if caminho.exists() and str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))
from pdi_lab.__main__ import (
    adaptive,
    analisaCompConectados,
    exportarCSV,
    fixed,
    hsv,
    otsu,
    seqMorf,
    validarMascara,
)

def test_limiarFixoSintetico():
    cinza = np.array([[119, 120, 121]], dtype=np.uint8)
    imagem = cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)
    mascara = fixed(imagem, 120)
    esperada = np.array([[0, 0, 255]], dtype=np.uint8)
    assert np.array_equal(mascara, esperada)

def test_mascaraBinaria():
    imagem = np.zeros((10, 12, 3), dtype=np.uint8)
    mascara = fixed(imagem, 120)
    assert validarMascara(mascara, imagem)
    assert mascara.shape == imagem.shape[:2]
    assert mascara.ndim == 2
    assert set(np.unique(mascara)).issubset({0, 255})

def test_otsu():
    cinza = np.array(
        [[0, 0, 0, 255, 255, 255]],
        dtype=np.uint8,
    )
    imagem = cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)
    mascara = otsu(imagem)
    assert mascara.shape == (1, 6)
    assert mascara.ndim == 2
    assert set(np.unique(mascara)).issubset({0, 255})
    assert np.count_nonzero(mascara) == 3

def test_conectividadeSinteticaDiagonal():
    mascara = np.array([[255, 0], [0, 255]], dtype=np.uint8)
    num_4, _, _, _ = analisaCompConectados(mascara, conectividade=4)
    num_8, _, _, _ = analisaCompConectados(mascara, conectividade=8)
    assert num_4 - 1 == 2
    assert num_8 - 1 == 1

def test_morfRuidoEFuro(tmp_path):
    mascara = np.zeros((11, 11), dtype=np.uint8)
    mascara[3:8, 3:8] = 255
    mascara[5, 5] = 0  
    mascara[0, 0] = 255 

    prefix = str(tmp_path / "test_morph")
    final_mask, stage_info = seqMorf(
        mascara, ["opening", "closing"], "ellipse", 3, 1, prefix
    )
    assert final_mask[0, 0] == 0
    assert final_mask[5, 5] == 255
    assert len(stage_info) == 2

def test_mascaraVazia():
    mascara = np.zeros((20, 20), dtype=np.uint8)
    num_4, _, _, _ = analisaCompConectados(mascara, conectividade=4)
    num_8, _, _, _ = analisaCompConectados(mascara, conectividade=8)

    assert num_4 - 1 == 0
    assert num_8 - 1 == 0

def test_objetoTocaBorda():
    mascara = np.zeros((10, 10), dtype=np.uint8)
    mascara[0:3, 0:3] = 255
    num_8, _, stats_8, _ = analisaCompConectados(
        mascara, conectividade=8
    )
    assert num_8 - 1 == 1
    assert stats_8[1, cv2.CC_STAT_LEFT] == 0
    assert stats_8[1, cv2.CC_STAT_TOP] == 0
    assert stats_8[1, cv2.CC_STAT_AREA] == 9

def test_somaAreasPixelsBrutos():
    mascara = np.zeros((50, 50), dtype=np.uint8)
    mascara[5:15, 5:15] = 255
    mascara[20:30, 20:35] = 255
    mascara[40, 40] = 255
    total_fg = np.count_nonzero(mascara)
    for conn in (4, 8):
        num_labels, _, stats, _ = analisaCompConectados(
            mascara, conectividade=conn
        )
        soma_areas = sum(stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels))
        assert soma_areas == total_fg

def executar(*argumentos):
    ambiente = os.environ.copy()
    raiz = RAIZ_PROJETO
    raiz_src = str(raiz / "src")
    pythonpath_atual = ambiente.get("PYTHONPATH", "")
    caminhos = [raiz_src, str(raiz)]
    if pythonpath_atual:
        caminhos.append(pythonpath_atual)
    ambiente["PYTHONPATH"] = os.pathsep.join(caminhos)
    return subprocess.run(
        [sys.executable, "-m", "pdi_lab", *argumentos],
        capture_output=True,
        text=True,
        env=ambiente,
        cwd=raiz,
    )

def test_falhaConectividadeInvalida(tmp_path):
    entrada = tmp_path / "mask.png"
    cv2.imwrite(str(entrada), np.zeros((10, 10), dtype=np.uint8))
    resultado = executar(
        "--input",
        str(entrada),
        "--output",
        str(tmp_path / "out"),
        "--operation",
        "analyze",
        "--connectivity",
        "6",
    )
    assert resultado.returncode != 0

def test_execucaoAnalyzeCLICompleta(tmp_path):
    entrada = tmp_path / "mask_input.png"
    mascara = np.zeros((30, 30), dtype=np.uint8)
    mascara[5:15, 5:15] = 255
    mascara[0, 0] = 255
    cv2.imwrite(str(entrada), mascara)
    out_prefix = tmp_path / "res_cena"
    resultado = executar(
        "--input",
        str(entrada),
        "--output",
        str(out_prefix),
        "--operation",
        "analyze",
        "--connectivity",
        "8",
        "--min-area",
        "5",
    )

    assert resultado.returncode == 0, f"Erro na execução CLI: {resultado.stderr}"
    assert (tmp_path / "res_cena_initial.csv").exists()
    assert (tmp_path / "res_cena_final.csv").exists()
    assert (tmp_path / "res_cena_labels.png").exists()
    assert (tmp_path / "res_cena_summary.json").exists()
    assert (tmp_path / "res_cena_stage1_opening.png").exists()
    assert (tmp_path / "res_cena_stage2_closing.png").exists()
    with open(tmp_path / "res_cena_summary.json", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["connectivity"] == 8
    assert summary["min_area"] == 5
    assert summary["initial_mask"]["raw_components"] == 2
    assert summary["final_mask"]["kept_components"] == 1