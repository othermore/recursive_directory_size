# 🚀 Directory Structure Tools

A collection of high-performance tools designed to analyze folder sizes, cloud-mounted drives, and hardlink distributions across multiple directories.

Standard tools like `du`, `ls`, or Finder often fall short when dealing with cloud-streaming files or complex hardlink structures. This repository provides specialized scripts to solve these issues.

## 1. 🚀 G-Drive Fast Analyzer (`recursive_directory_size.py`)

A high-performance, multi-threaded Python script designed to analyze folder sizes recursively for cases where `du` does not work (because there's no metadata for the directories). A common use case is **Google Drive for Desktop** (and other cloud-mounted drives).

Standard tools like `du` often fail with cloud drives because:

1. **Streaming files** report 0 bytes on disk usage.
2. **Latency** makes sequential scanning incredibly slow.
3. **Finder/Explorer** do not calculate folder sizes automatically.

This script solves these issues by reading file metadata in parallel and calculating recursive folder sizes in memory.

### ✨ Features

* **⚡ Multi-threaded:** Uses `ThreadPoolExecutor` to scan 20 folders simultaneously, saturating the network latency for maximum speed.
* **📊 Real-time Dashboard:** Shows current speed (files/s), throughput (MB/s), and queue size.
* **Interactive:**
  * Press **`ENTER`** to see partial results without stopping the scan.
  * Press **`Ctrl+C`** to stop immediately and generate the final report.
* **🌲 Tree View:** Outputs results alphabetically (by path) to easily compare directory structures.
* **💾 Auto-Save:** Automatically saves the report to a temporary file (`/tmp/drive_scan_timestamp.txt`).
* **🔍 Depth Control:** Limit the display depth (e.g., only show top-level folders) with visual indicators `(*)`.

### 📦 Installation

No external dependencies required! This script uses only Python standard libraries.

1. Ensure you have **Python 3.6+** installed.
2. Download the script:

```bash
curl -O [https://raw.githubusercontent.com/othermore/directory_structure_tools/main/recursive_directory_size.py](https://raw.githubusercontent.com/othermore/directory_structure_tools/main/recursive_directory_size.py)
```

*(Or simply copy the code into a file named `gdrive_analyzer.py`)*

### 🚀 Usage

#### Basic Scan

Simply provide the path to your Google Drive folder.

```bash
python3 recursive_directory_size.py "/Volumes/GoogleDrive/My Drive"
```

#### Advanced Options

```bash
python3 recursive_directory_size.py "/Volumes/GoogleDrive/My Drive" --max-display-depth 2 --lines 50
```

| Argument | Description | 
| ----- | ----- | 
| `folder` | The target directory path to analyze. | 
| `--max-display-depth N` | (Optional) Limit the output to `N` levels of depth. Folders with hidden subfolders are marked with `(*)`. | 
| `--lines N` | (Optional) Limit the number of lines shown when pressing ENTER (Partial view). Use `0` for all lines. Default: `0`. | 

### 💡 Pro Tips

#### Sorting by Size

By default, the script outputs an **alphabetical tree structure** (easier to navigate visually). To sort the output file by size (largest first), use the `sort` command with the `-h` (human-readable) flag.

After the script finishes, it will print the location of the output file (e.g., `/tmp/drive_scan_12345.txt`).

**Sort from Largest to Smallest:**

```bash
# Skip the header lines (+3)
tail -n +3 /tmp/drive_scan_xxxx.txt | sort -hr
```

#### Understanding the Output

```text
    15.40GB | /My Drive/Projects
    10.20GB | /My Drive/Backups (*)
     5.10GB | /My Drive/Photos
```

* **10.20 GB**: The total size of the folder (files inside it + all subfolders).
* **(\*)**: Indicates that this folder has subfolders inside, but they are not shown because you used `--max-display-depth`.

#### ⚠️ Notes on Google Drive

* **Initial Cache:** The first time you run this on a massive drive, it might take a while as Google Drive needs to fetch metadata. Subsequent runs will be much faster due to OS caching.
* **Memory Usage:** The script builds the directory tree in memory. For drives with millions of files, Python may use a few hundred MB of RAM.

## 2. 🔗 Hardlink Analyzer (`hardlink_analyzer.sh` & `hardlink_analyzer_mac.sh`)

Bash scripts that recursively scan multiple directories and calculate how files are hardlinked within themselves and across different directories.

When using hardlinks (for example, in backup systems, macOS Time Machine equivalents, or media servers like Immich), it is difficult to determine how many files are actually sharing the same disk blocks. This tool rapidly reads file inodes and cross-references them to generate an accurate map of your hardlinks.

### ✨ Features

* **Recursive Scanning:** Automatically analyzes the base directories and all nested subdirectories.
* **OS-Specific Optimizations:**
  * `hardlink_analyzer.sh`: Uses GNU `find -printf` for maximum execution speed on Linux environments.
  * `hardlink_analyzer_mac.sh`: Uses native BSD `stat` for seamless macOS compatibility.
* **Detailed Tabular Output:** Categorizes file links into total, internal, external, and unlinked.

### 📦 Installation

Download the script corresponding to your Operating System and grant it execution permissions:

**For Linux:**

```bash
curl -O [https://raw.githubusercontent.com/othermore/directory_structure_tools/main/hardlink_analyzer.sh](https://raw.githubusercontent.com/othermore/directory_structure_tools/main/hardlink_analyzer.sh)
chmod +x hardlink_analyzer.sh
```

**For macOS:**

```bash
curl -O [https://raw.githubusercontent.com/othermore/directory_structure_tools/main/hardlink_analyzer_mac.sh](https://raw.githubusercontent.com/othermore/directory_structure_tools/main/hardlink_analyzer_mac.sh)
chmod +x hardlink_analyzer_mac.sh
```

### 🚀 Usage

Provide the directories you want to cross-examine as arguments. You can pass as many directories as you need:

```bash
# Example for macOS:
./hardlink_analyzer_mac.sh /path/to/folder1 /path/to/folder2 /path/to/folder3
```

### 📊 Understanding the Output

The script generates a table with the following categories:

* **Total Archivos (Total Files):** Total number of files found recursively inside that specific directory.
* **Links Internos (Internal Links):** Files that share an inode with at least one other file *inside the exact same base directory*.
* **Links Externos (External Links):** Files that share an inode with a file located in *a different base directory* from the ones passed as arguments.
* **Sin Enlazar (Unlinked):** Files that have a unique, non-shared inode across all analyzed directories.

*(Note: A single file might be counted in both "Internal" and "External" columns if it has a clone within its own folder AND another clone in a different folder).*
