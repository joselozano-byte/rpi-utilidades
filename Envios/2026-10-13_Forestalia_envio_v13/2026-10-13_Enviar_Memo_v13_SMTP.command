#!/bin/zsh
cd "$(dirname "$0")"
/usr/bin/python3 enviar_memo_v13_smtp.py
echo; read -k1 "?Pulse una tecla para cerrar"
