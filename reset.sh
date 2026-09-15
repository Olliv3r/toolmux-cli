#!/usr/bin/env bash
set -u

found=0
while IFS= read -r -d '' cache_dir; do
    printf 'Removendo %s\n' "$cache_dir"
    rm -rf -- "$cache_dir"
    found=1
done < <(find . -type d -name '__pycache__' -print0)

if [ "$found" -eq 0 ]; then
    echo "Nenhum cache do Python encontrado."
else
    echo "Cache do Python removido."
fi
