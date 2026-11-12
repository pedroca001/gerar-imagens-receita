# Embalagens fornecidas por Pedro

Aplicar quando o pedido incluir fotos de produtos ou quotas por marca. As quotas sao parametros do lote, nao um padrao permanente de tres marcas.

- Copiar referencias sem editar para `referencias/` no lote externo. Nenhum PNG pesado no Brain. Registrar `baking_soda_brand`, `reference_image_path` e o papel da referencia em cada slot.
- Descrever marca, tipo fisico (cartucho, saco ou pouch), cor, peso e elementos principais do rotulo no prompt integral. Referencia de loja orienta somente a embalagem: ignorar interface, precos, bordas e vistas duplicadas do produto. Mostrar uma embalagem por cena mesmo quando a captura exibir multipack.
- Inspecionar cada referencia local antes da primeira chamada que a utiliza. Em geracao de cena nova guiada por embalagem, usar `referenced_image_paths:[reference_image_path]`, sem `num_last_images_to_include`. A foto de produto e referencia, nao alvo de edicao da captura.
- Conferir quotas por marca no planejamento e nas selecoes finais, alem de genero, idade, IDs e numero por chat. O helper preserva campos adicionais mas nao valida quotas de marca por conta propria.
- Na QA, comparar embalagem do candidato com sua propria referencia. Um saco grande precisa escala e campo de visao suficientes para aparecer inteiro; nao substituir por cartucho menor para facilitar o enquadramento. Preservar a categoria Baking Soda.
- Nao fazer chamadas abreviadas de teste para descobrir o formato do retorno. Quando ja houver um PNG nativo, reconciliar `savedPath` e inspecionar esse mesmo arquivo antes de repetir. Qualquer chamada extra entra na auditoria real, mesmo fora dos slots.

Referencias do lote de 2026-10-08: Arm & Hammer em saco flexivel dourado de 3 lb, Great Value em cartucho peach/laranja de 1 lb e Bob's Red Mill em um pouch rosa/lavanda de 16 oz. Cem selecoes por marca, cinquenta mulheres e cinquenta homens por marca, todos 55-75. Estes tamanhos se aplicam a esse pedido e nao substituem variantes explicitamente autorizadas em outros lotes.
