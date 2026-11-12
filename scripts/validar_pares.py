"""Valida pareamento com um lote real de dois pares, sem gerar pixels ou videos."""
import argparse
import contextlib
import copy
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.dont_write_bytecode=True
sp=importlib.util.spec_from_file_location('lote',Path(__file__).with_name('lote.py'))
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
parser=argparse.ArgumentParser();parser.add_argument('--lote',type=Path,required=True);a=parser.parse_args()
pairs=m.read(a.lote/'planejamento/pares_entrada.json')[:2]
assert len(pairs)==2
original=m.read(a.lote/'manifesto.json')
images=[(a.lote/s['approved_path']).resolve() for s in sorted(original['slots'],key=lambda s:s['id'])[:4]]
assert len({m.png(p)['sha256'] for p in images})==4
with tempfile.TemporaryDirectory(prefix='validar_pares_') as temp:
 home=Path(temp)
 with patch.object(m.Path,'home',return_value=home),contextlib.redirect_stdout(io.StringIO()):
  source=home/'pares.json';m.write(source,pairs)
  args=NS(pares=source,nome='teste',chats=2,modelo='fixture',reasoning='fixture')
  m.preparar_pares(args)
  root=home/'Downloads/receita_gpt_image/teste'
  manifest=m.read(root/'manifesto.json')
  assert manifest['target_pairs']==2 and manifest['target_images']==4
  assert all(len(m.read(p)['slots'])==2 and len(m.read(p)['pairs'])==1 for p in root.glob('chats/*/job.json'))
  # Falha antes de criar destino quando audio e abertura nao correspondem.
  bad=copy.deepcopy(pairs);bad[0]['audio_binding']['audio_sha256']='0'*64;m.write(source,bad)
  args.nome='audio_errado'
  try:m.preparar_pares(args)
  except ValueError:pass
  else:raise AssertionError('Audio divergente foi aceito')
  assert not (root.parent/args.nome).exists()
  bad=copy.deepcopy(pairs);bad[0]['audio_binding']['opening_sentences']=bad[0]['audio_binding']['opening_sentences'][:1];m.write(source,bad)
  args.nome='uma_frase'
  try:m.preparar_pares(args)
  except ValueError:pass
  else:raise AssertionError('Uma frase foi aceita')
  assert not (root.parent/args.nome).exists()
  jobs={s['id']:p for p in root.glob('chats/*/job.json') for s in m.read(p)['slots']}
  for i in range(3):
   sid=f'{i+1:03d}'
   m.registrar(NS(job=jobs[sid],id=sid,source=images[i],veredito='approved',motivo='Fixture de arquivo real, sem QA novo',call_id='fixture_'+sid,duracao=None,qa=None))
  assert m.fechar(NS(lote=root,consolidar_cache=False))==2
  partial=m.read(root/'manifesto.json')
  assert partial['approved_count']==3 and partial['approved_pair_count']==1
  m.registrar(NS(job=jobs['004'],id='004',source=images[3],veredito='approved',motivo='Fixture',call_id='fixture_004',duracao=None,qa=None))
  assert m.fechar(NS(lote=root,consolidar_cache=False))==0
  done=m.read(root/'manifesto.json')
  assert done['approved_pair_count']==2 and len(done['pairs'])==2
  assert 'Hook inicial' in (root/'galeria.html').read_text()
  for pair in done['pairs']:
   assert pair['status']=='approved'
  invalid=copy.deepcopy(done);invalid['pairs'][1]['recipe_image_id']=invalid['pairs'][0]['recipe_image_id']
  try:m.pair_results(invalid,invalid['slots'])
  except ValueError:pass
  else:raise AssertionError('Imagem reutilizada entre pares foi aceita')
  invalid=copy.deepcopy(done);invalid['slots'][0]['kind']='hook'
  try:m.pair_results(invalid,invalid['slots'])
  except ValueError:pass
  else:raise AssertionError('Receita/hook trocados foram aceitos')
print('PASS: audio/SHA e duas frases, pares inteiros por chat, deficit, fechamento, galeria, IDs/tipos exclusivos; sem novas geracoes, temporarios removidos')
