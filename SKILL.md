---
name: gerar_imagens_receita
description: Gera imagens UGC de receita e pares de inicios de video (receita + hook ligado as duas primeiras frases do audio), com cenarios variados, quotas de maos/idade/marca e entrega consolidada. Use para preparar lotes no Codex e imagens pareadas. A copy de anuncios segue sua skill propria.
---

# Gerar imagens de receita

## Resultado e escolhas

Entregar a quantidade pedida de PNGs individuais aprovados, fundos distintos e uma galeria, com prompts, vereditos e chamadas reais rastreaveis. Padrao deste fluxo: planejamento no chat coordenador, executores GPT-6 Luna Medium, Standard solicitado, geracao nativa `image_gen`. O teste de referencia foi planejado em GPT-6.1 Sol High. Preservar escolhas diferentes expressas por Pedro; nao trocar o modelo do chat atual silenciosamente.

O modelo do agente prepara prompts e faz QA; o gerador de imagens e separado. Nao prometer ganho de renderizacao pelo Fast/reasoning nem inventar tokens ou custo. Confirmar versao do gerador apenas pela ferramenta/documentacao atual, sem gravar snapshot presumido.

## Inicios de video: receita e hook

Pedido de N inicios de video significa N pares, total2N imagens: uma receita normal e um hook inicial exclusivo por video. Cem inicios sao100receitas+100hooks. Quando houver audio indicado, ler [references/inicios_pareados.md](references/inicios_pareados.md) antes de planejar. A abertura real de duas frases orienta o hook, que e um plano independente e pode mostrar rostos/objetos/reacoes. O contrato de tigela/duas maos/ingredientes vale somente para a receita.

Preparar todos os pares antes do despacho com `scripts/lote.py preparar-pares --pares <pares.json> --nome <lote> --chats <quantidade_autorizada>`.

Cada chat recebe pares inteiros; dez imagens por chat equivalem a cinco pares.

Contar pares aprovados alem dos PNGs.

Pedido so de imagens nao inicia videos.

## Destino obrigatorio

- macOS: resolver `Path.home() / 'Downloads' / 'receita_gpt_image' / <nome_do_lote>`. Usar nome definido pelo usuario ou `receita_<quantidade>_<data_hora>` em snake_case.
- Se Pedro indicar SSD ou outro destino, esse pedido prevalece. Verificar volume realmente montado antes de escrever. Downloads/staging pode guardar o lote enquanto desconectado; consolidar no destino pedido e conferir hashes antes de reduzir copias a aliases. Nunca criar uma pasta com nome do SSD em /Volumes para simular montagem.
- Todas as imagens finais ficam em `aprovadas/` nesse lote. Candidatos nao selecionados ficam em `tentativas/`, uma copia fisica por hash. Planejamento, jobs e relatorios ficam no mesmo lote, sem imagens dentro das pastas dos chats.
- O gerador pode criar um original automatico no cache do Codex. Depois de renderizar, copiar/arquivar sem editar, verificar SHA256 e, no fechamento, substituir somente as copias de cache deste lote por symlinks para a copia consolidada. Isso preserva os links dos chats sem PNGs pesados duplicados. Se o sistema nao permitir, informar a excecao real.
- Nunca escolher Pictures, Desktop, raiz do usuario ou Brain para os PNGs finais. Nao varrer/apagar caches de outros chats.

## Planejar antes de gerar

Se receber um `job.json` ja preparado como executor, pular planejamento/despacho e executar somente seus slots. O coordenador consolida cache, galeria e documentos ao terminar o lote.

1. Confirmar quantidade, tema e contrato visual a partir do pedido. Para esta receita, ler [references/contrato_visual.md](references/contrato_visual.md) e o prompt base em [references/prompt_base.txt](references/prompt_base.txt). Alteracoes explicitas de Pedro prevalecem.
2. Definir cenarios distintos antes de qualquer chamada. Misturar casa/oficina, hobbies, carros/estrada, veiculos de lazer, ar livre, esportes, comunidade, campo/trabalho, lanchonetes/nostalgia e lojas/cotidiano. Variar arquitetura e contexto, nao apenas cor/luz. Consultar historico dos lotes em Downloads; o [catalogo de cem cenarios](references/catalogo_cenarios.json) e inspiracao, nao uma lista para repetir sempre.
3. Preparar JSON com `family`, `slug`, `environment`, `surface`, `lighting`, `sleeves` por cenario. Para variacoes autorizadas, incluir `gender`, `min_age`, `max_age`, `packaging` e `prompt` integral por slot. Quando Pedro fornecer referencias de embalagens ou quotas por marca, ler [references/embalagens_referencia.md](references/embalagens_referencia.md), registrar marca/referencia por slot e validar tambem essas quotas. O prompt integral prevalece sobre o exemplo antigo masculino/marcas fixas; validar que expressa o pedido atual. O helper normaliza IDs, distribui familias, limita capacidade por chat e aplica quotas iguais de genero quando divisiveis pelo numero de chats. Grava prompts e hashes antes do despacho. Conferir quotas globais e locais antes de chamar create_thread:

```sh
python3 scripts/lote.py preparar --cenarios <arquivo_json> --nome <nome_do_lote> --quantidade 100 --chats 10
```

Quantidade e numero de executores sao configuraveis. Nao abrir dez chats para um pedido pequeno so porque o teste anterior usou dez.

## Executar e acompanhar

- Se Pedro pedir novos chats ou repetir explicitamente o teste de dez conversas, usar `list_projects` e `create_thread` no workspace escolhido pelo usuario, `model: gpt-6-luna`, `thinking: medium`, um job por chat, enviados em paralelo. Registrar IDs antes de continuar e emitir as diretivas de chats criados no fechamento.
- Sem pedido de novos chats, executar no chat atual ou usar subagentes internos quando autorizados pelo pedido/contrato da sessao. Esta skill nao autoriza abrir conversas por conta propria nem contornar a politica de delegacao.
- Para o caso dez chats/dez imagens, ler [references/execucao_paralela.md](references/execucao_paralela.md), que inclui o briefing do executor e a captura correta da ferramenta.
- Em chats locais com gravacao externa sujeita a approval, preparar jobs de staging em uma area temporaria permitida, fora do Brain, antes do despacho. Preservar prompts/IDs; o coordenador copia PNGs e manifestos para o destino final, confere hashes e limpa somente redundancias deste lote. Um chat preso em approval continua bloqueado ate liberacao normal, sem novos chats substitutos ou protocolos alternativos.
- Uma chamada nativa por imagem. Sem API/CLI paga como fallback. Ler a skill `imagegen` instalada antes da primeira geracao; se a ferramenta faltar, reportar bloqueio, sem simular entrega.
- Usar a string integral do `job.json`, validada antes de enviar. Nunca enviar stdout de um comando de leitura falho. Renderizar e guardar retorno na mesma execucao. Se perder caminho, reconciliar `imageGeneration.savedPath` do proprio chat antes de repetir.
- QA usa o prompt integral de cada slot como autoridade para as variantes. Conferir literalmente `packaging` antes de rejeitar formato/marca/tamanho, inclusive frasco `bear-shaped` quando previsto. Reclassificacao pelo coordenador preserva veredito anterior e usa o mesmo retorno nativo, sem gerar novamente.
- Inspecionar cada candidato pelo contrato. Executor faz no maximo tres tentativas visuais por slot; registrar falha tecnica separadamente, sem repeticao ilimitada. Seguir os outros slots e reportar deficit se necessario. Antes de fechar com deficit, o coordenador revisa os candidatos existentes. Quando faltar apenas uma correcao localizada para cumprir a quantidade autorizada, pode despachar uma unica edicao adicional daquele candidato, documentando a excecao e inspecionando novamente a cena inteira. Nao reiniciar o slot nem abrir chat substituto. Pedro aceita proporcao vertical aproximada: nao refazer apenas pela diferenca de 9:16 se o quadro essencial estiver inteiro e utilizavel, inclusive 887x1774. O helper verifica orientacao e pixels minimos; o agente avalia o enquadramento, sem corte ou esticamento por codigo.
- Salvar cada resultado com o helper `registrar`, incluindo veredito e motivo real. Cada executor escreve seu manifesto; nomes globais de imagem sao exclusivos por ID. Nao escrever manifesto global/logs em varios chats simultaneamente.
- Acompanhar com `wait_threads`, excluindo concluidos e usando cursores. Reconciliar chamadas nativas no fechamento; uma chamada perdida/falha ainda entra na contagem real. Nao parar depois de despachar.

## Fechar e consolidar

```sh
python3 scripts/lote.py fechar --lote <pasta_do_lote> --consolidar_cache
```

O helper confere arquivos, dimensoes, hashes, duplicatas e selecoes; gera `manifesto.json`, `galeria.html` e `relatorios/relatorio.md`. Ele nao avalia anatomia/rotulos por codigo. O coordenador faz amostra visual de um arquivo por executor e corrige falhas observadas antes de declarar a quantidade aprovada. Falha/uncertain critica nao entra na meta.

No fechamento, `aprovadas/` contem exatamente a selecao final, e `tentativas/` preserva candidatos diferentes nao selecionados. Nao manter segunda pasta com PNGs por chat. Caminhos dos manifestos sao relativos ao lote; caminho original da ferramenta e mantido como evidencia, com alias leve quando consolidado.

Registrar resultado real e destino no relatorio do lote. Na instalacao canonica do Brain, atualizar tambem a ficha operacional e o log diario. Responder com aprovadas/meta, numero real de chamadas quando reconciliado, tempo observado e links para galeria/pasta. Tokens dos agentes, cache e reasoning devem ser separados da cobranca do gerador. Producao diaria e videos dependem de pedido explicito.

## Encaminhar a producao de videos quando solicitado

- Quando Pedro designar o chat coordenador e autorizar mensagem a um chat Vids, concluir QA e manifesto de ID/path/hash das novas imagens antes do encaminhamento. Usar somente o chat nomeado; preservar lotes anteriores. A mensagem inclui quantidade, pasta real, conta inicial, meta e instrucao de continuidade autorizada.
- Se o SSD solicitado estiver ausente, registrar que a entrega esta temporariamente em Downloads. Encaminhamento preparado pode pedir ao executor consolidar e verificar no volume real quando conectado antes de iniciar videos; nao afirmar transferencia ou iniciar uma entrega pesada no destino errado.
- Quando disponivel, ler a skill de producao de videos instalada e a ficha operacional atual. Confirmar email na UI, pois indice da URL varia. Pedido para usar todas as contas autoriza seguir nas contas existentes autorizadas ate completar a meta ou constatar quota de todas; nao parar na primeira quota, nao exceder a meta nem assumir capacidade ilimitada.
- Enviar instrucoes usando `send_message_to_thread` apenas com autorizacao humana. Acompanhar `wait_threads` e estado real; despacho nao confirma videos concluidos. Salvar aceite, progresso ou bloqueio concreto e o texto enviado nos relatorios do lote.
