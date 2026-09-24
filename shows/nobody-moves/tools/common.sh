# Shared by setup.sh and tools/install-kokoro.sh (sourced, not run).

# kokoro-onnx 0.6.1 supports Python 3.10-3.13. macOS's built-in python3 is 3.9 and a
# current Homebrew python3 can be newer than 3.13, so look for a compatible one.
find_python() {
  local p
  for p in python3.13 python3.12 python3.11 python3.10 python3; do
    command -v "$p" >/dev/null 2>&1 || continue
    if "$p" -c 'import sys; sys.exit(not (3, 10) <= sys.version_info[:2] <= (3, 13))' 2>/dev/null; then
      echo "$p"
      return 0
    fi
  done
  echo "Kokoro needs Python 3.10-3.13 and none was found. On a Mac: brew install python@3.12" >&2
  return 1
}

download() { [ -s "$2" ] || { echo "downloading $(basename "$2")"; curl -fsSL -o "$2" "$1"; }; }

# verify <python> <sha256> <file>
verify() {
  "$1" -c "import hashlib, sys
h = hashlib.sha256(open(sys.argv[2], 'rb').read()).hexdigest()
sys.exit(h != sys.argv[1] and f'checksum mismatch for {sys.argv[2]}: the voices would sound different. Delete it and re-run.')" "$2" "$3"
}

# The exact model files the series cast (cast.py) was voiced with.
KOKORO_URL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
KOKORO_ONNX_SHA256=6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb
KOKORO_VOICES_SHA256=bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d

# fetch_models <dir> <python>
fetch_models() {
  mkdir -p "$1"
  download "$KOKORO_URL/kokoro-v1.0.int8.onnx" "$1/kokoro.onnx"
  download "$KOKORO_URL/voices-v1.0.bin" "$1/voices.bin"
  verify "$2" "$KOKORO_ONNX_SHA256" "$1/kokoro.onnx"
  verify "$2" "$KOKORO_VOICES_SHA256" "$1/voices.bin"
}

# espeak-ng (Kokoro's pronunciation engine) cannot read its data from a path longer than
# ~160 characters and fails with "Error processing file .../phontab". Warn early.
# check_espeak_path <python>
check_espeak_path() {
  local data
  data=$("$1" -c 'import espeakng_loader; print(espeakng_loader.get_data_path())')
  if [ "${#data}" -gt 150 ]; then
    echo "warning: espeak-ng data path is ${#data} characters (limit ~160):" >&2
    echo "  $data" >&2
    echo "  voices may fail with 'Error processing file ... phontab'; move this folder to a shorter path." >&2
  fi
}
