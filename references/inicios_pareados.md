# Inicios de video vinculados ao audio

Um inicio e um par: recipe + hook, imagens novas e independentes.

N pares significam2N PNGs finais, nunca reutilizar um hook ou corpo entre videos.

## Audio e conceito

Localizar os MP3s reais indicados. Conferir SHA256 e obter as duas primeiras frases na ordem por transcricao existente correspondente ou Whisper local; nao afirmar audicao quando houve leitura de transcricao. `audio_binding` registra `audio_path`, `audio_sha256`, `audio_id`, `opening_sentences` (duas strings), `opening_text` (as duas unidas por espaco) e `transcript_source` absoluto existente com as frases. Arquivo ausente/hash divergente bloqueia o par antes da geracao. Guardar texto/hash por par mesmo quando um audio se repete.

Traduzir a abertura em reacao, objeto ou metafora visual concreta. Ela precisa ser legivel desde o primeiro quadro e permitir acao imediata em ate2.5-3s de um hook6s. Manter o idioma do audio como contexto, sem imprimir suas frases na imagem. Variar conceitos e fundos dentro da mesma abertura, sem escolher um gancho generico por conveniencia. Hook pode ter rostos e corpos vestidos: nao aplicar o contrato de maos/receita ao hook. Receita conserva seu contrato proprio.

COPY18 pede reacao de admiracao da esposa; COPY19 permite metafora de macarrao mole; sao exemplos vinculados a esses audios, nao hooks universais.

## Planejamento e manifesto

Entrada JSON e uma lista de pares. Cada item contem:

- `recipe`: family, slug, environment, prompt integral e variantes de genero/idade/marca/referencia quando aplicaveis.
- `hook`: family, slug, environment e prompt integral, incluindo as duas frases como contexto sem texto sobreposto.
- `hook_idea`, `hook_video_prompt` (acao6s, resolvida cedo) e `audio_binding`.

Ambos prompts iniciam `Use case: photorealistic-natural.` e incluem `ASSIGNED DISTINCT SCENE:`. `preparar-pares` grava prompts/hashes, normaliza IDs e preserva cada par no mesmo chat. Exemplo autorizado60chats/600imagens:300pares,cinco pares/dez imagens por chat. `target_pairs` e `target_videos` descrevem quantidade, nao comprovam videos gerados.

`manifesto.json` tem slots com `kind` recipe/hook e `pair_id`; pairs referem `recipe_image_id`, `hook_image_id`, audio_binding e hook_video_prompt. `registrar` conserva vereditos/caminhos; `fechar` so aprova um par com as duas imagens presentes, indices coerentes e audio ainda integro. Galeria mostra pares ao lado de suas frases. Os arquivos aprovados ficam juntos em aprovadas/, sem copias por chat.
