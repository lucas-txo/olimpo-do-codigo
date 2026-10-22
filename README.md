# Olimpo do Código

- `index.html` – o jogo (com sincronização via Supabase)
- `config.js` – **você preenche**: URL e chave pública do Supabase
- `supabase.sql` – cole no SQL Editor do Supabase (cria a tabela e as regras de segurança)
- `atualizar_noticias.py` – baixa as manchetes e grava `noticias.js`
- `manter_ativo.py` – chamada diária que evita a pausa do Supabase gratuito
- `noticias.js` – placeholder; o GitHub gera um novo todo dia às 06:00 (Brasília)
- `.github/workflows/publicar.yml` – rotina que atualiza as notícias e publica no GitHub Pages

Para rodar na hora: aba **Actions** → *Atualizar noticias e publicar* → **Run workflow**.
