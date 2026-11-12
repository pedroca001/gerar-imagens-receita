# Gerar imagens de receita

## Purpose

Pacote reutilizável de instruções, prompts e helpers para geração nativa de imagens UGC de receita no Codex.

## Ownership

A fonte canônica é `<BRAIN_ROOT>/Skills/gerar_imagens_receita/`. Este repositório é uma exportação portátil. A ficha operacional é `<BRAIN_ROOT>/Ferramentas/midia/geracao_imagens_receita.md`. O uso independente segue os documentos locais.

## Local Contracts

- Leia `SKILL.md` antes de executar e consulte `README.md` para os comandos locais.
- Gere pela ferramenta nativa de imagens, com revisão visual de cada candidato.
- Prepare todos os prompts e hashes antes do despacho. Novos chats exigem pedido do usuário.
- Preserve parâmetros de quantidade, gênero, idade, variante e marcas do job atual.
- Faça uma geração por vez por chat, registre imediatamente e guarde metadados leves.
- Salve lotes fora do repositório, por padrão em `~/Downloads/receita_gpt_image/`. Um destino explícito do usuário prevalece.
- O executor registra apenas seu manifesto. O coordenador consolida depois que todas as escritas terminam.
- Reconcile retornos existentes antes de repetir chamadas após uma interrupção.
- Mantenha segredos e arquivos de produção fora do Git.

## Work Guidance

Em uma geração nova, adapte os exemplos a cenários diferentes. Leia `references/contrato_visual.md` e use o prompt integral de cada slot. Para hooks, leia `references/inicios_pareados.md`. Atualizações da exportação devem preservar as capacidades da skill canônica e revalidar os caminhos relativos.

## Verification

- Execute `python3 -B scripts/lote.py --help`.
- Verifique sintaxe Python e JSON e os links relativos dos documentos.
- Para alterações no helper, execute `scripts/validar_lote.py` com dois PNGs verticais existentes e distintos.
- Para mudanças nos pares, execute `scripts/validar_pares.py` com um lote pareado existente.
- A exportação inicial foi conferida com o verificador de lotes e arquivos existentes. A revisão de pares fica condicionada à disponibilidade dos áudios do lote.

## Child DOX Index

- `references/` contém contratos visuais e o fluxo de execução.
- `scripts/` contém o helper e os verificadores existentes.
- `examples/` contém quatro prompts completos configuráveis.
