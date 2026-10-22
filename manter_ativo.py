#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Faz uma chamada diária ao Supabase para o projeto gratuito não ser pausado por inatividade.
Lê a URL e a chave do config.js. Se não estiverem preenchidas, não faz nada."""
import json, os, re, sys, urllib.request

pasta = os.path.dirname(os.path.abspath(__file__))
try:
    cfg = open(os.path.join(pasta, "config.js"), encoding="utf-8").read()
except OSError:
    print("config.js não encontrado; nada a fazer."); sys.exit(0)

def pega(campo):
    m = re.search(r"^\s*%s\s*:\s*[\"']([^\"']*)[\"']" % campo, cfg, re.M)
    return m.group(1).strip() if m else ""

url, key = pega("url").rstrip("/"), pega("key")
if not url or not key:
    print("Supabase ainda não configurado no config.js; nada a fazer."); sys.exit(0)

req = urllib.request.Request(url + "/rest/v1/rpc/ping", data=b"{}", method="POST",
        headers={"apikey": key, "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print("Supabase respondeu:", r.status, r.read(100).decode("utf-8", "ignore"))
except Exception as e:
    print("Aviso: não consegui falar com o Supabase:", str(e)[:200]); sys.exit(1)
