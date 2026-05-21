"""
gerar_token_google.py
=====================
Roda UMA VEZ para gerar o refresh_token do Google Ads.
Depois cole o refresh_token em atualizar_google.py.

Execute: python gerar_token_google.py
"""

# Cole aqui os valores do JSON baixado do Google Cloud Console
CLIENT_ID     = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"

# ─────────────────────────────────────────────────────────────────────────────

import webbrowser
import urllib.parse
import urllib.request

SCOPE    = "https://www.googleapis.com/auth/adwords"
REDIRECT = "urn:ietf:wg:oauth:2.0:oob"

# 1. Gera URL de autorizacao
params = {
    "client_id":     CLIENT_ID,
    "redirect_uri":  REDIRECT,
    "response_type": "code",
    "scope":         SCOPE,
    "access_type":   "offline",
}
url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("\n1. Abrindo navegador para autorizacao...")
print(f"   Se nao abrir, acesse manualmente:\n   {url}\n")
webbrowser.open(url)

code = input("2. Cole o codigo de autorizacao que apareceu na tela: ").strip()

# 2. Troca code por tokens
data = urllib.parse.urlencode({
    "code":          code,
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri":  REDIRECT,
    "grant_type":    "authorization_code",
}).encode()

req  = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
resp = urllib.request.urlopen(req)
tokens = __import__("json").loads(resp.read())

print("\n✅ Tokens obtidos!")
print(f"\n   REFRESH_TOKEN = \"{tokens.get('refresh_token', 'N/A')}\"")
print("\nCole esse REFRESH_TOKEN em atualizar_google.py")
