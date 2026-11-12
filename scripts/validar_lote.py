"""Validacao isolada com dois PNGs reais, sem geracao/edicao de pixels."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('lote',Path(__file__).with_name('lote.py'))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('png1',type=Path);p.add_argument('png2',type=Path);args=p.parse_args()
assert m.png(args.png1)['sha256']!=m.png(args.png2)['sha256']
parent=Path.home()/'Downloads/receita_gpt_image/_organizacao'
parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='validacao_lote_',dir=parent) as temp:
 home=Path(temp)
 with patch.object(m.Path,'home',return_value=home),contextlib.redirect_stdout(io.StringIO()):
  scenes=[dict(family=f'familia_{i%2}',slug=f'cenario_{i}',environment=f'Validation environment {i}',surface='Table',lighting='Daylight',sleeves='Shirt') for i in range(4)]
  for i,s in enumerate(scenes):
   s.update(gender='female' if i%2 else 'male',min_age=55,prompt='Use case: photorealistic-natural.\nCustom age 55+ packaging.\nASSIGNED DISTINCT SCENE:\n'+s['environment'])
  src=home/'scenes.json';m.write(src,scenes)
  prep=NS(nome='planejamento',cenarios=src,quantidade=4,chats=2,seed=1,modelo='gpt-6-luna',reasoning='medium',permitir_repetidos=False)
  m.preparar(prep)
  batch=home/'Downloads/receita_gpt_image/planejamento'
  jobs=list(batch.glob('chats/*/job.json'))
  assert len(jobs)==2
  for j in jobs:
   data=m.read(j);assert len(data['slots'])==2
   assert len({s['family'] for s in data['slots']})==2
   assert all(len(s['id'])==3 and s['prompt'].startswith('Use case:') for s in data['slots'])
   assert {s['gender'] for s in data['slots']}=={'female','male'}
   assert all('Custom age 55+ packaging.' in s['prompt'] for s in data['slots'])
  try:m.preparar(prep)
  except ValueError:pass
  else:raise AssertionError('Planejamento existente foi sobrescrito')
  # Duas imagens: duplicata nao entra na meta; mesmo call-id nao conta duas vezes.
  small=NS(**vars(prep));small.nome='duas';small.quantidade=2;small.chats=1;m.preparar(small)
  root=home/'Downloads/receita_gpt_image/duas';job=root/'chats/chat_01/job.json'
  def register(j,sid,source,cid):m.registrar(NS(job=j,id=sid,source=source,veredito='approved',motivo='TEST fixture QA',call_id=cid,duracao=1.0,qa=None))
  register(job,1,args.png1,'test_1');register(job,1,args.png1,'test_1')
  register(job,1,args.png1,None)
  assert len(m.read(job.with_name('manifesto.json'))['slots'][0]['attempts'])==1
  register(job,2,args.png1,'test_duplicate')
  assert m.fechar(NS(lote=root,consolidar_cache=True))==2
  assert m.read(root/'manifesto.json')['approved_count']==1
  register(job,2,args.png2,'test_2')
  assert m.fechar(NS(lote=root,consolidar_cache=True))==0
  assert len(list((root/'aprovadas').glob('*.png')))==2
  assert (root/'galeria.html').exists()
  assert 'id="gender"' in (root/'galeria.html').read_text()
  # Retomada/substituicao depois de consolidar cache deve preservar ambos os originais.
  one=NS(**vars(prep));one.nome='cache';one.quantidade=1;one.chats=1;m.preparar(one)
  root=home/'Downloads/receita_gpt_image/cache';job=root/'chats/chat_01/job.json'
  cache=home/'.codex/generated_images/fixture';cache.mkdir(parents=True)
  a,b=cache/'a.png',cache/'b.png';shutil.copy2(args.png1,a);shutil.copy2(args.png2,b)
  register(job,1,a,'test_cache_a');assert m.fechar(NS(lote=root,consolidar_cache=True))==0
  assert a.is_symlink()
  register(job,1,b,'test_cache_b');assert m.fechar(NS(lote=root,consolidar_cache=True))==0
  assert a.is_symlink() and b.is_symlink()
  assert m.png(a)['sha256']==m.png(args.png1)['sha256']
  assert m.png(b)['sha256']==m.png(args.png2)['sha256']
  assert a.resolve().parent==root/'tentativas'
  assert b.resolve().parent==root/'aprovadas'
  assert len([p for p in root.rglob('*.png') if not p.is_symlink()])==2
print('PASS: destino, IDs, familias, retomada, idempotencia, duplicata, deficit, galeria e cache/substituicao; temporarios removidos')
