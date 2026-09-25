"""Reassemble and verify the exact Episode 1 CapCut export."""

from hashlib import sha256
from pathlib import Path


HERE = Path(__file__).resolve().parent
NAME = "ep01_clean_for_capcut.mp4"
EXPECTED_SHA256 = "0bbf71b10ea537244129eecd1001596625a9cdfc75b404e66247c7db9f2b6047"
PARTS = [HERE / f"{NAME}.part-{index:02d}" for index in range(3)]


def main() -> None:
    missing = [part.name for part in PARTS if not part.is_file()]
    if missing:
        raise SystemExit(f"Missing video parts: {', '.join(missing)}")

    output = HERE / NAME
    digest = sha256()
    with output.open("wb") as video:
        for part in PARTS:
            with part.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    video.write(chunk)

    if digest.hexdigest() != EXPECTED_SHA256:
        output.unlink()
        raise SystemExit("Video checksum mismatch; check the downloaded parts")

    print(f"Verified {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
