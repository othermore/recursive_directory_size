# 🚀 G-Drive Fast Analyzer

A high-performance, multi-threaded Python script designed to analyze folder sizes recursively for cases where du does not work (because there's no metadata for the directories). A common use case is **Google Drive for Desktop** (and other cloud-mounted drives).

Standard tools like `du` often fail with cloud drives because:

1. **Streaming files** report 0 bytes on disk usage.
2. **Latency** makes sequential scanning incredibly slow.
3. **Finder/Explorer** do not calculate folder sizes automatically.

This script solves these issues by reading file metadata in parallel and calculating recursive folder sizes in memory.

## ✨ Features

* **⚡ Multi-threaded:** Uses `ThreadPoolExecutor` to scan 20 folders simultaneously, saturating the network latency for maximum speed.
* **📊 Real-time Dashboard:** Shows current speed (files/s), throughput (MB/s), and queue size.
* **interactive:**
* Press **`ENTER`** to see partial results without stopping the scan.
* Press **`Ctrl+C`** to stop immediately and generate the final report.


* **🌲 Tree View:** Outputs results alphabetically (by path) to easily compare directory structures.
* **💾 Auto-Save:** Automatically saves the report to a temporary file (`/tmp/drive_scan_timestamp.txt`).
* **🔍 Depth Control:** Limit the display depth (e.g., only show top-level folders) with visual indicators `(*)` for hidden content.

## 📦 Installation

No external dependencies required! This script uses only Python standard libraries.

1. Ensure you have **Python 3.6+** installed.
2. Download the script:

```bash
curl -O https://raw.githubusercontent.com/your-username/repo-name/main/gdrive_analyzer.py

```

*(Or simply copy the code into a file named `gdrive_analyzer.py`)*

## 🚀 Usage

### Basic Scan

Simply provide the path to your Google Drive folder.

```bash
python3 gdrive_analyzer.py "/Volumes/GoogleDrive/My Drive"

```

### Advanced Options

```bash
python3 gdrive_analyzer.py "/Volumes/GoogleDrive/My Drive" --max-display-depth 2 --lines 50

```

| Argument | Description |
| --- | --- |
| `folder` | The target directory path to analyze. |
| `--max-display-depth N` | (Optional) Limit the output to `N` levels of depth. Folders with hidden subfolders are marked with `(*)`. |
| `--lines N` | (Optional) Limit the number of lines shown when pressing ENTER (Partial view). Use `0` for all lines. Default: `0`. |

## 💡 Pro Tips

### Sorting by Size

By default, the script outputs an **alphabetical tree structure** (easier to navigate visually). To sort the output file by size (largest first), use the `sort` command with the `-h` (human-readable) flag.

After the script finishes, it will print the location of the output file (e.g., `/tmp/drive_scan_12345.txt`).

**Sort from Largest to Smallest:**

```bash
# Skip the header lines (+3) and sort by the first column (-k1,2)
tail -n +3 /tmp/drive_scan_12345.txt | sort -hr -k1,2

```

### Understanding the Output

```text
    15.40 GB | /My Drive/Projects
    10.20 GB | /My Drive/Backups (*)
     5.10 GB | /My Drive/Photos

```

* **10.20 GB**: The total size of the folder (files inside it + all subfolders).
* **(*)**: Indicates that this folder has subfolders inside, but they are not shown because you used `--max-display-depth`.

## ⚠️ Notes on Google Drive

* **Initial Cache:** The first time you run this on a massive drive, it might take a while as Google Drive needs to fetch metadata. Subsequent runs will be much faster due to OS caching.
* **Memory Usage:** The script builds the directory tree in memory. For drives with millions of files, Python may use a few hundred MB of RAM.

## 📄 License

MIT License. Feel free to modify and use it!

---

### Pasos siguientes para ti:

1. Crea un archivo llamado `README.md` en tu carpeta.
2. Copia el texto de arriba.
3. Donde pone `curl -O https://raw.githubusercontent...`, asegúrate de cambiar "your-username" y "repo-name" por tu usuario y nombre del repositorio real cuando lo crees.
4. Sube el script (`gdrive_analyzer.py`) y el `README.md` a GitHub.

¡Listo! Tienes una herramienta súper útil documentada como un profesional.
