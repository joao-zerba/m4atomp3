import os
import subprocess
import json
from mutagen.m4a import M4A
from mutagen.mp3 import EasyMP3
from mutagen.id3 import ID3, APIC
from mutagen import File

# Caminhos ABSOLUTOS
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"


def get_bitrate(input_file):
    """Extrai o bitrate original usando ffprobe."""
    cmd = [
        FFPROBE, "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=bit_rate",
        "-of", "json",
        input_file
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)

    try:
        return int(info["streams"][0]["bit_rate"])
    except:
        print(f"[Aviso] Não foi possível detectar o bitrate de: {input_file}. Usando 320k.")
        return 320000


def copy_metadata(m4a_file, mp3_file):
    """Copia metadados faltantes + capa."""
    src = File(m4a_file)

    # Carregar tags existentes do MP3 (ffmpeg já escreveu algumas!)
    dest = EasyMP3(mp3_file)

    # Copiar apenas metadados que NÃO vieram do ffmpeg
    mapping = {
        "©nam": "title",
        "©ART": "artist",
        "©alb": "album",
        "trkn": "tracknumber",
        "©day": "date",
        "©gen": "genre",
    }

    for k, v in mapping.items():
        if k in src.tags:
            if v not in dest.tags:
                dest[v] = str(src.tags[k])

    dest.save()

    # Copiar capa
    try:
        if "covr" in src.tags:
            cover = src.tags["covr"][0]
            mime = "image/jpeg" if cover.imageformat == 13 else "image/png"

            id3 = ID3(mp3_file)

            # Remover capa antiga, caso exista
            id3.delall("APIC")

            id3.add(APIC(
                encoding=3,
                mime=mime,
                type=3,
                desc="Cover",
                data=bytes(cover)
            ))
            id3.save()
            print(" → Capa copiada.")
    except Exception as e:
        print(" → Sem capa ou erro ao copiar capa:", e)


def convert_m4a_to_mp3(folder):
    for file in os.listdir(folder):
        if file.lower().endswith(".m4a"):
            inp = os.path.join(folder, file)
            out = os.path.join(folder, os.path.splitext(file)[0] + ".mp3")

            print(f"\n🔄 Convertendo: {file}")

            bitrate = get_bitrate(inp)
            print(f" → Bitrate original: {bitrate/1000:.0f} kbps")

            # FFmpeg converte e copia metadados automáticos
            cmd = [
                FFMPEG, "-y",
                "-i", inp,
                "-codec:a", "libmp3lame",
                "-b:a", str(bitrate),
                "-map_metadata", "0",  # COPIA TUDO AUTOMATICAMENTE
                "-id3v2_version", "3",
                out
            ]

            subprocess.run(cmd)
            print(" → Conversão OK.")

            print(" → Copiando metadados faltantes...")
            copy_metadata(inp, out)

    print("\n Finalizado com sucesso! MP3 com tags completas + capa.")


if __name__ == "__main__":
    pasta = input("Digite o caminho da pasta com arquivos .m4a: ")
    convert_m4a_to_mp3(pasta)
