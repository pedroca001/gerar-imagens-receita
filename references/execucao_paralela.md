# Execucao paralela no Codex

Ler quando o pedido autorizar conversas novas ou execucao simultanea. O coordenador prepara todos os prompts antes de despachar. Os executores recebem somente contrato/job e arquivos necessarios, sem copiar toda a pesquisa historica para dez contextos.

Antes do despacho, conferir em todos os slots a coerencia entre genero/idade/marca e o texto integral, alem de SHA e quotas. Ao importar templates, normalizar genero nos dois sentidos; nunca presumir que a fonte e masculina. Se a revisao ocorrer durante a execucao, preservar PNGs compativeis, registrar antes/depois e SHA, atualizar job pelo coordenador e manifesto somente pelo executor dono. Recarregar prompts antes da proxima chamada e revalidar quotas globais e por chat.

## Briefing por executor

Substituir valores de runtime:

Quando o job incluir prompts completos de genero/idade/marcas variaveis, executar esses parametros, sem impor homem 50+ e marcas do exemplo antigo. Lote 200 misto: 20 jobs de dez, cinco mulheres e cinco homens 55+ em cada, todos os prompts prontos antes do despacho. O coordenador valida 100/100 e nao cria chats extras para compensar erro de contagem.

> Execute os slots do job `<JOB_ABSOLUTO>` com GPT-6 Luna Medium, Standard solicitado, usando exclusivamente image_gen nativo. Nao altere config global nem abra outros chats. Leia SKILL.md da skill gerar_imagens_receita e a skill imagegen instalada. Os prompts integrais ja estao prontos em slots[].prompt, com IDs normalizados. Valide a string, gere uma imagem por chamada e inspecione cada retorno. No maximo tres tentativas visuais por slot, seguindo os demais se algum falhar. Registre todas as chamadas tecnicas, inclusive sem PNG, e nao repita resultado cujo caminho apenas se perdeu. Use o helper registrar para salvar em aprovadas/tentativas na raiz deste lote e gravar apenas o manifesto do seu executor. Nao crie copias de PNG em chats/chat_NN nem altere manifesto global/docs compartilhados. Standard nao e verificavel pelo criador de chats: registre solicitado sem fingir confirmacao. Tokens/custo proprios das imagens so se expostos. Termine com quantidade aprovada e caminhos; o coordenador aguarda os chats e le os arquivos, sem mensagem automatica de volta a outro chat.

## Permissoes e staging

Antes de abrir todos os executores, validar um job com gravacao na area permitida do chat. Quando Downloads/SSD exigirem approval interativa por executor, o coordenador pode preparar copias dos jobs em `/tmp/<lote>/chats/chat_NN/`, mudando somente `root` para essa pasta e preservando IDs, prompts e hashes. Executores registram no staging; o coordenador consolida no destino solicitado, com hashes conferidos, sem alterar manifestos enquanto o dono ainda escreve. Estado de approval nao se resolve por automacao do app bloqueada nem por criar substitutas.

Ao revisar variantes, ler `packaging` completo. Um frasco squeeze pode ser `bear-shaped` quando o proprio job o especifica. Preservar o veredito original quando o coordenador corrigir uma interpretacao, sem contar reclassificacao como nova geracao. Chamadas nativas sao reconciliadas por item real e `source_path`, pois repetir registro sem call-id pode duplicar metadados.

Depois de tres candidatos do executor, o coordenador deve revisar todos antes de decidir por deficit. Se uma edicao localizada puder concluir a meta autorizada, admitir uma unica chamada adicional dirigida ao melhor candidato existente, no mesmo chat, seguida de QA integral e registro da excecao. Essa regra nao libera novas tentativas de geracao do zero. Falhas de leitura de prompt e chamadas de teste abreviado nunca entram nos finais; preservar o PNG e contar cada item nativo uma vez, mesmo quando ele tambem aparece como erro operacional no manifesto.

## Captura nativa

Na ferramenta functions.exec, ler o prompt integral por mecanismo de arquivo disponivel e preservar como string. Para transportar um prompt multilinha a partir do shell, emitir JSON em uma linha e usar JSON.parse no retorno. Validar o exit_code e o SHA do prompt em relacao ao slot antes de enviar. Interromper a chamada se faltar parte do prompt ou se a leitura retornar erro. O fragmento abaixo pressupoe `prompt` ja carregado e validado, nunca uma mensagem de erro de shell:

```js
// @exec: {"yield_time_ms": 120000, "max_output_tokens": 1000}
if (!prompt.startsWith("Use case: photorealistic-natural.") || !prompt.includes("ASSIGNED DISTINCT SCENE:")) throw Error("Prompt invalido");
const started = Date.now();
const result = await tools.image_gen__imagegen({prompt, transparent_background:false});
store("candidate", {started, elapsed_ms:Date.now()-started, output_hint:result.output_hint});
generatedImage(result);
```

Sem `referenced_image_paths` e `num_last_images_to_include` em geracao nova sem referencias. Quando houver referencia de embalagem, seguir `embalagens_referencia.md` e incluir somente a referencia daquele slot, com seu papel explicito no prompt. Se usar edicao para corrigir candidato, inspecionar antes e usar mecanismo de referencia apropriado. Capturar o caminho real em output_hint; se o retorno encapsular pixels, encaminhar os pixels pelo renderer apropriado. Nao imprimir base64. Esperar cell somente depois de exec anunciar execucao em curso.

## Registro por imagem

```sh
python3 scripts/lote.py registrar --job <job.json> --id 001 --source <PNG_REAL> --veredito approved --motivo "Criterios inspecionados e aprovados" --call-id <ID_REAL> --duracao <SEGUNDOS_OBSERVADOS>
```

Vereditos: `approved`, `rejected`, `uncertain`. Para chamada tecnica sem PNG: `erro --job <job.json> --id 001 --call-id <ID_REAL> --motivo <erro_observado>`. Usar ID real quando exposto; nunca fabricar. Repetir registro do mesmo call-id e idempotente. Detalhes de QA podem ser fornecidos em `--qa <arquivo_json>`.

Cada `chats/chat_NN/manifesto.json` usa caminhos relativos a raiz do lote. `source_path` e evidencia absoluta do retorno nativo. PNG aprovado fica direto em `aprovadas/ID_slug.png`; rejeitado/incerto em `tentativas/`. Uma selecao substituida e preservada como tentativa antes da nova aprovacao. No fechamento, conferir amostra visual por executor, hashes dos arquivos finais e caminhos.

Mesmo quando duas geracoes independentes ocorrerem em paralelo, registrar candidatos e erros sequencialmente, aguardando cada escrita no manifesto. Registros simultaneos do mesmo executor podem sobrescrever entradas. Depois de mover um PNG por reclassificacao, reconciliar seus aliases de cache/staging pelo SHA original registrado: um link existente tambem pode apontar para uma selecao substituta de hash diferente.

Em lotes pareados os IDs de um chat podem ser nao contiguos. Reabrir o slot pelo ID e conferir seu prompt integral antes do QA; nunca comparar com o cenario de outro slot. Se o prompt pede mao segurando o fouet parado, segurar o cabo e correto. Hook independente nao herda criterios de tigela, maos ou mistura da receita. Corrigir apenas o criterio errado no mesmo registro, preservando historico, sem gerar novamente por falha de classificacao.

## Retomada e contagem

Antes de reenviar, consultar manifesto e `read_thread`/`imageGeneration.savedPath` quando houver resultado ambiguo. Uma conversa criada com resultado incerto deve ser reconciliada por list_threads, sem abrir substituta as cegas.

Registrar IDs de todas as conversas no manifesto global, observar `wait_threads` com cursores, ate oito alvos por chamada. Guardar quantidades reais de chamadas nativas separadas dos registros visuais. Um PNG perdido/nao avaliado nao conta como aprovado. Falhas operacionais de prompt nao sao tentativas visuais validas, mas contam como chamadas reais; parar repeticao tecnica se a mesma falha reaparecer duas vezes e corrigir/reconciliar primeiro.

Uma execucao real de 2026-09-30 entregou 100 aprovadas em 19m39s de dez conversas, com 114 chamadas. Esse e historico, nao SLA nem garantia de comparacao entre modelos/Fast. Custo do gerador nao foi exposto.
