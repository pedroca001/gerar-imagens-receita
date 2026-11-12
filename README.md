# Gerar imagens de receita

Instruções e scripts para gerar lotes de fotografias UGC de receita no Codex, com prompts preparados antes da geração, cenários variados, revisão visual e entrega consolidada.

O ponto de entrada do agente é [SKILL.md](SKILL.md). Os dois perfis de receita são padrão, com bicarbonato, gelatina de limão, mel e limão, e azeite extra virgem com mel e canela. Pedidos de inícios de vídeo também podem incluir um hook independente, vinculado às duas primeiras frases reais do áudio.

## Como usar no Codex

Abra este repositório como workspace e peça ao agente para ler `AGENTS.md` e `SKILL.md`. Um pedido completo pode ser escrito assim.

> Gere 100 imagens individuais, 50 padrão e 50 de azeite, mel e canela. Em cada variante, use metade mãos femininas e metade masculinas, com aparência de 55 a 75 anos. Prepare os prompts antes e varie os ambientes. Abra dez chats GPT-6 Luna com reasoning médio, dez imagens por chat. Acompanhe até terminar e salve tudo em uma pasta própria dentro de Downloads/receita_gpt_image.

O agente precisa ter a ferramenta nativa de geração de imagens habilitada e seguir a skill `imagegen` instalada no ambiente. O modelo do chat coordena, escreve e revisa. A versão do gerador e seus custos só podem ser confirmados quando o ambiente os expuser. O padrão histórico dos executores é GPT-6 Luna Medium. A disponibilidade do modelo deve ser conferida no ambiente de destino.

Novos chats dependem do pedido do usuário. Em um lote simples, a execução pode ocorrer no chat atual. Para reduzir pressão de memória, cada chat faz uma geração por vez, registra o resultado logo após a revisão e guarda apenas metadados leves. Em caso de interrupção, retome os slots pendentes depois de reconciliar os retornos existentes.

## Arquivos

- [Contrato visual](references/contrato_visual.md) descreve os dois perfis, mãos, ingredientes, embalagens e enquadramento.
- [Quatro exemplos completos](examples/cenarios_mistos.json) trazem as duas variantes com mãos masculinas e femininas de 55 a 75 anos. São exemplos para adaptar a novos cenários.
- [Prompt base](references/prompt_base.txt) mantém o exemplo original da receita padrão. Prompts integrais por slot prevalecem sobre esse modelo.
- [Catálogo de cenários](references/catalogo_cenarios.json) serve de inspiração para variar fundos.
- [Execução paralela](references/execucao_paralela.md) cobre despacho, captura de imagem, registro e retomada.
- [Embalagens](references/embalagens_referencia.md) orienta o uso opcional de referências de produto fornecidas pelo usuário.
- [Pares de receita e hook](references/inicios_pareados.md) define a ligação com o áudio e a contagem de pares.
- [Helper Python](scripts/lote.py) prepara jobs, registra candidatos e confere a entrega.

## Comandos do helper

Python 3.9 ou superior, com biblioteca padrão. Execute na raiz deste repositório. No Windows, use `python` no lugar de `python3`.

```sh
python3 -B scripts/lote.py --help
python3 -B scripts/lote.py preparar --cenarios examples/cenarios_mistos.json --nome teste_quatro_receitas --quantidade 4 --chats 2
```

O planejamento cria `~/Downloads/receita_gpt_image/teste_quatro_receitas/`, com os prompts, hashes e um `job.json` por executor. Esse comando prepara os arquivos. A geração acontece pela ferramenta nativa no Codex, seguida de revisão visual.

Registre cada imagem com o caminho real retornado pela ferramenta. Substitua os argumentos entre sinais de menor e maior pelos valores reais.

```sh
python3 -B scripts/lote.py registrar --job <job.json> --id <id> --source <imagem.png> --veredito approved --motivo "Revisão visual concluída" --call-id <id_real_da_chamada>
python3 -B scripts/lote.py fechar --lote <pasta_do_lote> --consolidar_cache
```

Registros de um mesmo job são sequenciais. Cada executor escreve somente seu manifesto. O coordenador fecha o lote depois que os executores encerram as escritas. O helper confere arquivos, orientação vertical, dimensões mínimas, hashes, duplicatas e seleções. Anatomia, ingredientes, rótulos e enquadramento exigem inspeção visual pelo agente.

Os PNGs finais ficam juntos em `aprovadas/`. Candidatos distintos ficam em `tentativas/`. A entrega inclui galeria HTML, manifesto e relatório. Após verificar os hashes, o fechamento pode substituir cópias redundantes do cache daquele lote por links para os arquivos consolidados. Um destino explícito, como SSD externo, prevalece sobre Downloads e precisa estar montado.

## Verificação local

Os verificadores usam arquivos existentes e criam dados temporários isolados.

```sh
python3 -B scripts/validar_lote.py <png_vertical_1> <png_vertical_2>
python3 -B scripts/validar_pares.py --lote <lote_pareado_existente>
```

O primeiro verifica planejamento, retomada, idempotência, duplicatas, déficit, galeria e aliases. O segundo requer um lote pareado com seus áudios e transcrições disponíveis.

## Origem e manutenção

Pacote exportado em 12/11/2026 da skill `gerar_imagens_receita` do Brain. A fonte canônica permanece nessa skill. Os caminhos dos comandos foram adaptados para este repositório. Os quatro exemplos foram extraídos de prompts completos do lote concluído e preparados para uso independente, com referências de embalagem opcionais. O repositório contém instruções e ferramentas de organização. As imagens e os registros de produção ficam na pasta de cada lote.
