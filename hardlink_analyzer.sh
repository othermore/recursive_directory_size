#!/bin/bash

# Comprobar que se han pasado argumentos
if [ "$#" -eq 0 ]; then
    echo "Uso: $0 <dir1> <dir2> ..."
    exit 1
fi

# Archivo temporal para almacenar inodos
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT INT TERM

echo "Analizando directorios (esto puede tardar unos segundos dependiendo del número de archivos)..."

for dir in "$@"; do
    clean_dir="${dir%/}"
    
    # VERSIÓN PARA LINUX: 
    # Usamos -printf "%i" nativo de GNU find para sacar el inodo directamente, 
    # añadiendo una tabulación y el directorio base. Es la forma más rápida en Linux.
    find "$clean_dir" -type f -printf "%i\t$clean_dir\n" 2>/dev/null >> "$tmp"
done

# Procesamos los datos con awk
awk -F'\t' '
{
    inode=$1
    dir=$2
    
    if (!dir_seen[dir]++) {
        dirs[dir] = 1
    }
    
    count_inode_dir[inode, dir]++
    
    if (!seen_inode_dir[inode, dir]) {
        seen_inode_dir[inode, dir] = 1
        unique_dirs_for_inode[inode]++
    }
}
END {
    for (comb in count_inode_dir) {
        split(comb, parts, SUBSEP)
        inode = parts[1]
        dir = parts[2]
        
        # Cantidad de veces que este inodo aparece en ESTE directorio (y sus subdirectorios)
        c = count_inode_dir[inode, dir]
        
        # 1. TOTAL ARCHIVOS
        total[dir] += c
        
        # 2. SIN ENLAZAR: Solo aparece 1 vez aquí y no aparece en ningún otro directorio
        if (c == 1 && unique_dirs_for_inode[inode] == 1) {
            unlinked[dir] += c
        }
        
        # 3. LINKS INTERNOS: El inodo está repetido dentro de este mismo directorio base
        if (c > 1) {
            internal[dir] += c
        }
        
        # 4. LINKS EXTERNOS: El inodo aparece en más de un directorio base en total
        if (unique_dirs_for_inode[inode] > 1) {
            external[dir] += c
        }
    }
    
    # Formato de la tabla
    printf "\n%-48s | %-14s | %-14s | %-14s | %-14s\n", "Directorio", "Total Archivos", "Links Internos", "Links Externos", "Sin Enlazar"
    printf "-------------------------------------------------|----------------|----------------|----------------|----------------\n"
    for (d in dirs) {
        printf "%-48s | %-14d | %-14d | %-14d | %-14d\n", d, total[d]+0, internal[d]+0, external[d]+0, unlinked[d]+0
    }
    print ""
}
' "$tmp"
