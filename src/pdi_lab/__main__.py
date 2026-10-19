import argparse
import csv
import json
import sys
from pathlib import Path
import cv2
import numpy as np

def fixed(imagem, threshold):
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    _, mascara = cv2.threshold(cinza, threshold, 255, cv2.THRESH_BINARY)
    return mascara

def otsu(imagem):
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    _, mascara = cv2.threshold(
        cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return mascara

def adaptive(imagem, tam, constante):
    if tam < 3 or tam % 2 == 0:
        raise ValueError("--block-size deve ser ímpar >= 3")
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(
        cinza,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        tam,
        constante,
    )

def hsv(imagem, hsvMin, hsvMax):
    hMin, sMin, vMin = hsvMin
    hMax, sMax, vMax = hsvMax
    if not (0 <= hMin <= 179 and 0 <= hMax <= 179):
        raise ValueError("H deve estar entre 0 e 179.")
    if not all(
        0 <= valor <= 255 for valor in (sMin, vMin, sMax, vMax)
    ):
        raise ValueError("S e V devem estar entre 0 e 255.")
    hsv_img = cv2.cvtColor(imagem, cv2.COLOR_BGR2HSV)
    if hMin <= hMax:
        inferior = np.array(hsvMin, dtype=np.uint8)
        superior = np.array(hsvMax, dtype=np.uint8)
        return cv2.inRange(hsv_img, inferior, superior)
    mascara_1 = cv2.inRange(
        hsv_img,
        np.array([hMin, sMin, vMin], dtype=np.uint8),
        np.array([179, sMax, vMax], dtype=np.uint8),
    )
    mascara_2 = cv2.inRange(
        hsv_img,
        np.array([0, sMin, vMin], dtype=np.uint8),
        np.array([hMax, sMax, vMax], dtype=np.uint8),
    )
    return cv2.bitwise_or(mascara_1, mascara_2)

def validarMascara(mascara, imagem_ou_shape):
    target_shape = (
        imagem_ou_shape.shape[:2]
        if hasattr(imagem_ou_shape, "shape")
        else imagem_ou_shape
    )
    return (
        mascara.ndim == 2
        and mascara.shape == target_shape
        and set(np.unique(mascara).tolist()).issubset({0, 255})
    )

def analisaCompConectados(mascara, conectividade=8):
    if conectividade not in (4, 8):
        raise ValueError("Conectividade deve ser 4 ou 8.")
    numLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mascara, connectivity=conectividade, ltype=cv2.CV_32S
    )
    return numLabels, labels, stats, centroids

def exportarCSV(stats, centroids, min_area, csv_path):
    numLabels = stats.shape[0]
    rows = []
    for i in range(1, numLabels):
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        area = int(stats[i, cv2.CC_STAT_AREA])
        cx = float(centroids[i, 0])
        cy = float(centroids[i, 1])
        kept = area >= min_area
        rows.append(
            {
                "label": i,
                "area": area,
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "cx": f"{cx:.2f}",
                "cy": f"{cy:.2f}",
                "kept": "true" if kept else "false",
            }
        )
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "label",
                "area",
                "x",
                "y",
                "width",
                "height",
                "cx",
                "cy",
                "kept",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    raw_count = len(rows)
    kept_count = sum(1 for r in rows if r["kept"] == "true")
    return raw_count, kept_count

def getKernel(shape_str, size):
    shape_map = {
        "rect": cv2.MORPH_RECT,
        "ellipse": cv2.MORPH_ELLIPSE,
        "cross": cv2.MORPH_CROSS,
    }
    if shape_str.lower() not in shape_map:
        raise ValueError(f"Forma de elemento estruturante inválida: {shape_str}")
    return cv2.getStructuringElement(shape_map[shape_str.lower()], (size, size))

def seqMorf(
    mascara, sequencia, kernel_shape, kernel_size, iterations, output_prefix
):
    kernel = getKernel(kernel_shape, kernel_size)
    mascaraAtual = mascara.copy()
    stage_info = []
    for idx, operacao in enumerate(sequencia, start=1):
        op_clean = operacao.lower().strip()
        if op_clean == "opening":
            op_code = cv2.MORPH_OPEN
        elif op_clean == "closing":
            op_code = cv2.MORPH_CLOSE
        elif op_clean == "erosion":
            op_code = cv2.MORPH_ERODE
        elif op_clean == "dilation":
            op_code = cv2.MORPH_DILATE
        else:
            raise ValueError(f"Operação morfológica desconhecida: {operacao}")
        mascaraAtual = cv2.morphologyEx(
            mascaraAtual, op_code, kernel, iterations=iterations
        )
        stage_filename = f"{output_prefix}_stage{idx}_{op_clean}.png"
        cv2.imwrite(stage_filename, mascaraAtual)
        stage_info.append(
            {
                "stage": idx,
                "operation": op_clean,
                "kernel_shape": kernel_shape,
                "kernel_size": kernel_size,
                "iterations": iterations,
                "output_file": stage_filename,
            }
        )
    return mascaraAtual, stage_info

def generate_label_visualization(labels_map, stats, centroids, min_area, output_path):
    h, w = labels_map.shape
    vis = np.zeros((h, w, 3), dtype=np.uint8)
    num_labels = stats.shape[0]
    np.random.seed(42)
    colors = np.random.randint(60, 255, size=(num_labels, 3), dtype=np.uint8)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        is_kept = area >= min_area
        color = colors[i].tolist() if is_kept else [60, 60, 60]
        vis[labels_map == i] = color
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        is_kept = area >= min_area
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        bw = int(stats[i, cv2.CC_STAT_WIDTH])
        bh = int(stats[i, cv2.CC_STAT_HEIGHT])
        cx, cy = int(centroids[i, 0]), int(centroids[i, 1])
        box_color = (0, 255, 0) if is_kept else (0, 0, 180)
        cv2.rectangle(vis, (x, y), (x + bw, y + bh), box_color, 1)
        cv2.drawMarker(vis, (cx, cy), (0, 255, 255), cv2.MARKER_CROSS, 6, 1)
        if is_kept:
            cv2.putText(
                vis,
                str(i),
                (x, max(12, y - 3)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    cv2.imwrite(str(output_path), vis)

def processarSegment(args):
    imagem = cv2.imread(args.input, cv2.IMREAD_COLOR)
    if imagem is None:
        raise ValueError(f"Não foi possível ler a imagem: {args.input}")
    if args.method == "fixed":
        mascara = fixed(imagem, args.threshold)
    elif args.method == "otsu":
        mascara = otsu(imagem)
    elif args.method == "adaptive":
        mascara = adaptive(imagem, args.block_size, args.constant)
    elif args.method == "hsv":
        mascara = hsv(imagem, args.hsv_min, args.hsv_max)
    else:
        raise ValueError(f"Método desconhecido: {args.method}")
    if not validarMascara(mascara, imagem):
        raise RuntimeError("A máscara gerada não é válida.")
    caminho_saida = Path(args.output)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(caminho_saida), mascara):
        raise OSError(f"Não foi possível salvar a máscara: {caminho_saida}")
    total = mascara.size
    pixelsObjeto = int(np.count_nonzero(mascara))
    pixelsFundo = total - pixelsObjeto
    proporcao = 100.0 * pixelsObjeto / total
    print(f"Método: {args.method}")
    print(f"Entrada: {args.input}")
    print(f"Saída: {caminho_saida}")
    print(f"Dimensões: {mascara.shape[1]} x {mascara.shape[0]}")
    print(f"Pixels objeto: {pixelsObjeto}")
    print(f"Pixels fundo: {pixelsFundo}")
    print(f"Proporção primeiro plano: {proporcao:.2f}%")
    print("Máscara binária válida: sim")

def processarAnalyze(args):
    mascaraInt = cv2.imread(args.input, cv2.IMREAD_GRAYSCALE)
    if mascaraInt is None:
        raise ValueError(f"Não foi possível ler a máscara: {args.input}")
    if getattr(args, "invert", False):
        mascaraInt = cv2.bitwise_not(mascaraInt)
    unique_vals = set(np.unique(mascaraInt).tolist())
    if not unique_vals.issubset({0, 255}):
        raise ValueError(
            "A imagem de entrada deve ser uma máscara binária (valores 0 e 255)."
        )
    output_prefix = args.output
    prefix_path = Path(output_prefix)
    prefix_path.parent.mkdir(parents=True, exist_ok=True)
    num_4, _, _, _ = analisaCompConectados(
        mascaraInt, conectividade=4
    )
    num_8, labels_init_8, stats_init_8, centroids_init_8 = (
        analisaCompConectados(mascaraInt, conectividade=args.connectivity)
    )
    raw_count_4 = num_4 - 1
    raw_count_8_init = num_8 - 1
    total_fg_initial = int(np.count_nonzero(mascaraInt))
    sum_area_init = sum(
        int(stats_init_8[i, cv2.CC_STAT_AREA]) for i in range(1, num_8)
    )
    if total_fg_initial != sum_area_init:
        raise RuntimeError("Inconsistência na área acumulada dos componentes brutos.")
    initial_csv = f"{output_prefix}_initial.csv"
    raw_init_count, kept_init_count = exportarCSV(
        stats_init_8, centroids_init_8, args.min_area, initial_csv
    )
    mascaraFinal, stage_info = seqMorf(
        mascaraInt,
        args.morph_sequence,
        args.kernel_shape,
        args.kernel_size,
        args.iterations,
        output_prefix,
    )
    num_final, labels_final, stats_final, centroids_final = (
        analisaCompConectados(
            mascaraFinal, conectividade=args.connectivity
        )
    )
    total_fg_final = int(np.count_nonzero(mascaraFinal))
    sum_area_final = sum(
        int(stats_final[i, cv2.CC_STAT_AREA]) for i in range(1, num_final)
    )
    if total_fg_final != sum_area_final:
        raise RuntimeError("Inconsistência na área acumulada final.")
    final_csv = f"{output_prefix}_final.csv"
    raw_final_count, kept_final_count = exportarCSV(
        stats_final, centroids_final, args.min_area, final_csv
    )
    labels_png = f"{output_prefix}_labels.png"
    generate_label_visualization(
        labels_final, stats_final, centroids_final, args.min_area, labels_png
    )
    summary_data = {
        "input_mask": args.input,
        "connectivity": args.connectivity,
        "min_area": args.min_area,
        "connectivity_comparison_initial": {
            "count_conn4_raw": raw_count_4,
            "count_conn8_raw": raw_count_8_init,
        },
        "initial_mask": {
            "raw_components": raw_init_count,
            "kept_components": kept_init_count,
            "total_foreground_pixels": total_fg_initial,
        },
        "morphological_sequence": stage_info,
        "final_mask": {
            "raw_components": raw_final_count,
            "kept_components": kept_final_count,
            "total_foreground_pixels": total_fg_final,
        },
    }
    summary_json = f"{output_prefix}_summary.json"
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"Análise concluída com sucesso para: {args.input}")
    print(f" - CSV Inicial: {initial_csv}")
    print(f" - CSV Final: {final_csv}")
    print(f" - Rótulos visualizáveis: {labels_png}")
    print(f" - Resumo JSON: {summary_json}")
    print(
        f" - Componentes Iniciais (conn={args.connectivity}): brutos={raw_init_count}, filtrados={kept_init_count}"
    )
    print(
        f" - Componentes Finais (conn={args.connectivity}): brutos={raw_final_count}, filtrados={kept_final_count}"
    )

def criarParser():
    parser = argparse.ArgumentParser(
        description="PDI Lab — Segmentação e Análise Morfológica / Componentes Conexos."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--operation", required=True, choices=["segment", "analyze"]
    )

    parser.add_argument(
        "--method",
        choices=["fixed", "otsu", "adaptive", "hsv"],
        default="otsu",
    )
    parser.add_argument("--threshold", type=int, default=120)
    parser.add_argument("--block-size", type=int, default=11)
    parser.add_argument("--constant", type=float, default=2.0)
    parser.add_argument(
        "--hsv-min",
        type=int,
        nargs=3,
        default=[0, 100, 100],
        metavar=("H", "S", "V"),
    )
    parser.add_argument(
        "--hsv-max",
        type=int,
        nargs=3,
        default=[10, 255, 255],
        metavar=("H", "S", "V"),
    )

    parser.add_argument(
        "--connectivity", type=int, choices=[4, 8], default=8
    )
    parser.add_argument("--min-area", type=int, default=20)
    parser.add_argument(
        "--kernel-shape",
        choices=["ellipse", "rect", "cross"],
        default="ellipse",
    )
    parser.add_argument("--kernel-size", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument(
        "--morph-sequence",
        nargs="+",
        default=["opening", "closing"]
    )
    parser.add_argument(
        "--invert",
        action="store_true",
    )
    return parser

def main():
    parser = criarParser()
    args = parser.parse_args()
    if args.operation == "segment":
        if not 0 <= args.threshold <= 255:
            parser.error("--threshold deve estar entre 0 e 255")
        for nome, valores in (
            ("--hsv-min", args.hsv_min),
            ("--hsv-max", args.hsv_max),
        ):
            limites = (179, 255, 255)
            if any(
                valor < 0 or valor > limite
                for valor, limite in zip(valores, limites)
            ):
                parser.error(
                    f"{nome}: H deve estar entre 0 e 179; "
                    "S e V devem estar entre 0 e 255"
                )

    try:
        if args.operation == "segment":
            processarSegment(args)
        elif args.operation == "analyze":
            processarAnalyze(args)
    except (ValueError, OSError, RuntimeError, cv2.error) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())