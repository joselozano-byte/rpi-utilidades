#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RPI - Envio SMTP (grupoloor.es, SSL 465) del memorando Forestalia v1.3 con adjuntos, sin Apple Mail.
Credenciales: llavero de macOS (servicio 'rpi_smtp_grupoloor', cuenta = usuario SMTP) o fichero smtp_grupoloor.env
(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD) en esta carpeta. La contrasena nunca se escribe en el log."""
import os, sys, ssl, smtplib, subprocess, mimetypes, datetime
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

BASE = os.path.dirname(os.path.abspath(__file__))
TO = ["santiagogarcia@rpi-e.com", "juan.revilla@ig4capital.com", "joselozano@rpi-e.com"]
SUBJECT = "[RPI] Forestalia — memorandum VERSION 1.3 with attachments (resend) / memorando VERSIÓN 1.3 con adjuntos (reenvío)"
BODY = os.path.join(BASE, "2026-10-13_memo_v13_reenvio_body.txt")
ATTS = [os.path.join(BASE, "2026-10-12_Forestalia_GIC_Investment_Committee_Memo.docx"),
        os.path.join(BASE, "2026-10-12_Forestalia_Group_Organisation_Chart.pptx")]
LOG = os.path.join(BASE, "2026-10-13_envio_smtp.log")

def cfg():
    c = {"SMTP_HOST": "smtp.serviciodecorreo.es", "SMTP_PORT": "465", "SMTP_USER": "joselozano@grupoloor.es", "SMTP_PASSWORD": ""}
    envf = os.path.join(BASE, "smtp_grupoloor.env")
    if os.path.exists(envf):
        for line in open(envf, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1); c[k.strip()] = v.strip().strip('"').strip("'")
    if not c["SMTP_PASSWORD"]:
        try:
            c["SMTP_PASSWORD"] = subprocess.check_output(["security", "find-generic-password", "-s", "rpi_smtp_grupoloor",
                                                          "-a", c["SMTP_USER"], "-w"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            pass
    return c

def log(t):
    with open(LOG, "a", encoding="utf-8") as f: f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {t}\n")

def main():
    c = cfg()
    if not c["SMTP_PASSWORD"]:
        msg = "ERROR: sin contrasena SMTP (llavero 'rpi_smtp_grupoloor' o smtp_grupoloor.env)"; log(msg); print(msg); sys.exit(2)
    m = EmailMessage()
    m["From"] = f"José Lozano Muñoz <{c['SMTP_USER']}>"; m["To"] = ", ".join(TO); m["Subject"] = SUBJECT
    m["Date"] = formatdate(localtime=True); m["Message-ID"] = make_msgid(domain=c["SMTP_USER"].split("@")[-1])
    m.set_content(open(BODY, encoding="utf-8").read())
    for p in ATTS:
        ctype, _ = mimetypes.guess_type(p); maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        with open(p, "rb") as f:
            m.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(p))
    for i in range(3):
        try:
            with smtplib.SMTP_SSL(c["SMTP_HOST"], int(c["SMTP_PORT"]), context=ssl.create_default_context(), timeout=60) as s:
                s.login(c["SMTP_USER"], c["SMTP_PASSWORD"]); s.send_message(m)
            t = f"ENVIADO {m['Message-ID']} from={c['SMTP_USER']} to={','.join(TO)} adjuntos={[os.path.basename(a) for a in ATTS]}"
            log(t); print(t); return
        except Exception as ex:
            log(f"intento {i+1} fallido: {type(ex).__name__}: {ex}")
    print("ERROR: envio fallido tras 3 intentos; ver " + LOG); sys.exit(1)

if __name__ == "__main__":
    main()
