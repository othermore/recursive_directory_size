import os
import sys
import time
import concurrent.futures
import select
import argparse
from collections import defaultdict, deque

# --- CONFIGURACIÓN DE COLORES ---
RESET = "\033[0m"
YELLOW = "\033[93m"

def get_size_format(b, factor=1024, suffix="B"):
    """
    Convierte bytes a formato legible SIN ESPACIOS para facilitar el sort.
    Ejemplo: 10.50GB, 500.00KB
    """
    for unit in ["", "K", "M", "G", "T", "P"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}P{suffix}"

def scan_folder(path):
    """Escanea UNA carpeta y devuelve estadísticas locales."""
    local_size = 0
    subdirs = []
    file_count = 0
    
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file(follow_symlinks=False):
                    local_size += entry.stat().st_size
                    file_count += 1
                elif entry.is_dir(follow_symlinks=False):
                    subdirs.append(entry.path)
    except (PermissionError, OSError):
        pass
        
    return local_size, subdirs, file_count

def print_dashboard(folders, files, total_bytes, queue, speed_files, speed_bytes):
    """Imprime panel de estado."""
    human_size = get_size_format(total_bytes)
    human_throughput = get_size_format(speed_bytes, suffix="/s")
    
    msg = (
        f"\r[Total: {human_size:>10}] | "
        f"[Archivos: {files:>7}] | "
        f"[Flujo: {human_throughput:>11}] | "
        f"[Arch/s: {speed_files:>5.0f}] | "
        f"[Cola: {queue:>3}]"
    )
    sys.stderr.write(msg.ljust(110))
    sys.stderr.flush()

def calculate_totals(folder_local_sizes, root_dir):
    """Calcula la suma recursiva de carpetas."""
    temp_totals = defaultdict(int)
    for path, size in folder_local_sizes.items():
        temp_totals[path] = size

    # Ordenamos de más profundo a más superficial
    sorted_paths = sorted(folder_local_sizes.keys(), key=lambda p: len(p.split(os.sep)), reverse=True)

    for path in sorted_paths:
        parent = os.path.dirname(path)
        if parent in temp_totals and path != root_dir:
            temp_totals[parent] += temp_totals[path]
            
    return temp_totals

def show_results(folder_total_sizes, root_dir, folders_with_children, max_depth=None, limit_lines=0, final=False):
    """
    Muestra la tabla de resultados ordenada ALFABÉTICAMENTE.
    Guarda el resultado en /tmp/ si es la ejecución final.
    """
    
    status_msg = "\n\n--- RESULTADOS PARCIALES ---\n"
    output_filepath = None

    if final:
        status_msg = "\n\n--- RESULTADOS FINALES ---\n"
        timestamp = int(time.time())
        output_filepath = f"/tmp/drive_scan_{timestamp}.txt"
    
    sys.stderr.write(status_msg)
    
    lines_to_output = []
    
    # Cabecera ajustada
    header = f"{'TAMAÑO':>12} | {'RUTA'}"
    separator = "-" * 100
    
    lines_to_output.append(header)
    lines_to_output.append(separator)

    # Ordenación Alfabética (Árbol)
    sorted_results = sorted(folder_total_sizes.items(), key=lambda item: item[0])
    
    root_dir = os.path.normpath(root_dir)
    count = 0
    
    for path, size in sorted_results:
        if size < 1 * 1024 * 1024: # Filtro < 1MB
            continue

        # Cálculo de profundidad
        if path == root_dir:
            depth = 0
        else:
            try:
                rel_path = os.path.relpath(path, root_dir)
                depth = rel_path.count(os.sep) + 1
            except ValueError:
                depth = 0

        # Lógica de profundidad máxima y asterisco
        marker = ""
        if max_depth is not None:
            if depth > max_depth:
                continue
            if depth == max_depth and path in folders_with_children:
                marker = f" (*)"

        # Formateamos la línea SIN espacios en la unidad
        line_clean = f"{get_size_format(size):>12} | {path}{marker}"
        lines_to_output.append(line_clean)
        
        count += 1
        if not final and limit_lines > 0 and count >= limit_lines:
            lines_to_output.append(f"... (mostrando {limit_lines} resultados. Usa --lines 0 para ver todos) ...")
            break
    
    # 1. Imprimir en pantalla (con colores si aplica)
    for line in lines_to_output:
        if "(*)" in line:
            print(line.replace("(*)", f"{YELLOW}(*){RESET}"))
        else:
            print(line)

    # 2. Guardar en archivo (Solo si es final)
    if final and output_filepath:
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                for line in lines_to_output:
                    f.write(line + "\n")
            print(f"\n✅ Resultados guardados en: {output_filepath}")
        except IOError as e:
            print(f"\n❌ Error guardando archivo: {e}")

    if not final:
        print("\n... Pulsa ENTER para actualizar o Ctrl+C para finalizar ...\n")

def main():
    parser = argparse.ArgumentParser(description="Analizador de espacio recursivo G-Drive.")
    parser.add_argument("folder", help="Ruta de la carpeta a analizar")
    parser.add_argument("--max-display-depth", type=int, default=None, 
                        help="Nivel de profundidad máxima a mostrar.")
    parser.add_argument("--lines", type=int, default=0, 
                        help="Líneas a mostrar. 0 = Todas (Por defecto).")
    
    args = parser.parse_args()
    
    root_dir = args.folder
    max_display_depth = args.max_display_depth
    limit_lines = args.lines
    
    if not os.path.exists(root_dir):
        print(f"Error: La carpeta '{root_dir}' no existe.")
        sys.exit(1)

    print(f"Iniciando analisis en: {root_dir}")
    print("================================================================================")
    print("CONTROLES: [ENTER] -> Ver parciales | [Ctrl+C] -> Finalizar y Guardar")
    print("================================================================================")

    folder_local_sizes = defaultdict(int)
    folders_with_children = set()
    total_files = 0
    total_scanned_bytes = 0
    processed_folders = 0
    speed_history = deque() 
    WINDOW_SECONDS = 20 

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
    
    try:
        future_to_path = {executor.submit(scan_folder, root_dir): root_dir}
        start_time = time.time()
        speed_history.append((start_time, 0, 0))

        while future_to_path:
            # 1. DETECCIÓN ENTER
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.readline()
                temp_totals = calculate_totals(folder_local_sizes, root_dir)
                show_results(temp_totals, root_dir, folders_with_children, max_display_depth, limit_lines, final=False)
                sys.stderr.write("Reanudando dashboard...\n")

            # 2. HILOS
            done, not_done = concurrent.futures.wait(future_to_path, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
            
            # 3. VELOCIDAD
            now = time.time()
            speed_history.append((now, total_files, total_scanned_bytes))
            while speed_history and speed_history[0][0] < (now - WINDOW_SECONDS):
                speed_history.popleft()
            
            current_speed_bytes = 0
            current_speed_files = 0
            if len(speed_history) > 1:
                old_time, old_files, old_bytes = speed_history[0]
                delta_time = now - old_time
                if delta_time > 0:
                    current_speed_bytes = (total_scanned_bytes - old_bytes) / delta_time
                    current_speed_files = (total_files - old_files) / delta_time

            print_dashboard(processed_folders, total_files, total_scanned_bytes, len(future_to_path), current_speed_files, current_speed_bytes)

            if not done: continue

            for future in done:
                path = future_to_path.pop(future)
                processed_folders += 1
                try:
                    size, subdirs, count = future.result()
                    folder_local_sizes[path] = size
                    total_files += count
                    total_scanned_bytes += size
                    if subdirs:
                        folders_with_children.add(path)
                        for subdir in subdirs:
                            future_to_path[executor.submit(scan_folder, subdir)] = subdir
                except Exception: pass 

        # FIN NORMAL
        sys.stderr.write(f"\nFinalizado.\n")
        final_totals = calculate_totals(folder_local_sizes, root_dir)
        show_results(final_totals, root_dir, folders_with_children, max_display_depth, limit_lines=0, final=True)

    except KeyboardInterrupt:
        print("\n\n*** Ctrl+C detectado ***")
        executor.shutdown(wait=False, cancel_futures=True)
        final_totals = calculate_totals(folder_local_sizes, root_dir)
        show_results(final_totals, root_dir, folders_with_children, max_display_depth, limit_lines=0, final=True)
        sys.exit(0)
        
    except Exception as e:
        print(f"\nError: {e}")
        executor.shutdown(wait=False)
        sys.exit(1)
    
    finally:
        executor.shutdown(wait=False)

if __name__ == "__main__":
    main()
