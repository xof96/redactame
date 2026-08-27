from pathlib import Path
import argparse
import random


def shuffle_jsonl(file_path: Path, seed: int | None = None) -> Path:
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    if file_path.suffix.lower() != ".jsonl":
        raise ValueError("El archivo debe tener extensión .jsonl")

    with file_path.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    rng = random.Random(seed)
    rng.shuffle(lines)

    output_path = file_path.with_name(
        f"{file_path.stem}-shuffled{file_path.suffix}"
    )

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Reordena aleatoriamente las líneas de un archivo JSONL."
    )

    parser.add_argument(
        "file",
        type=Path,
        help="Ruta al archivo .jsonl"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed opcional para obtener siempre el mismo shuffle"
    )

    args = parser.parse_args()

    output_path = shuffle_jsonl(args.file, args.seed)

    print(f"Archivo generado: {output_path}")


if __name__ == "__main__":
    main()