#!/usr/bin/env python3
"""Organiza lotes nativos. Nao chama API nem gera/edita pixels."""
import argparse
import collections
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import random
import re
import shutil
import struct
import sys
import uuid

SKILL = Path(__file__).resolve().parents[1]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(temp, path)


def safe_name(value):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_]*', value):
        raise ValueError('Nome/slug deve usar snake_case, sem espacos, acentos ou caminhos')
    return value


def png(path):
    b = Path(path).read_bytes()
    if b[:8] != b'\x89PNG\r\n\x1a\n' or b[-12:] != b'\0\0\0\0IEND\xaeB`\x82':
        raise ValueError('PNG incompleto ou invalido')
    w, h = struct.unpack('>II', b[16:24])
    return {'width': w, 'height': h, 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def copy_verified(src, dest, sha):
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_name(dest.name + '.' + uuid.uuid4().hex + '.tmp')
    shutil.copy2(src, temp)
    if hashlib.sha256(temp.read_bytes()).hexdigest() != sha:
        temp.unlink()
        raise ValueError('Copia nao corresponde ao hash original')
    os.replace(temp, dest)


def cache_alias(src, target, sha):
    src, target = Path(src), Path(target).resolve()
    cache = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'generated_images'
    if not src.is_absolute() or not src.is_relative_to(cache) or src == target:
        return False
    if src.is_symlink():
        if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
            raise ValueError('Destino do alias nao validado')
        if src.resolve() == target:
            return True
        temp = src.with_name(src.name + '.' + uuid.uuid4().hex + '.link')
        temp.symlink_to(os.path.relpath(target, src.parent))
        os.replace(temp, src)
        return True
    if not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest() != sha:
        return False
    if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
        raise ValueError('Destino do cache nao validado')
    temp = src.with_name(src.name + '.' + uuid.uuid4().hex + '.link')
    temp.symlink_to(os.path.relpath(target, src.parent))
    os.replace(temp, src)
    return True


def preparar(args):
    root = Path.home()/'Downloads'/'receita_gpt_image'
    name = safe_name(args.nome or f'receita_{args.quantidade}_'+dt.datetime.now().strftime('%Y_%m_%d_%H%M%S'))
    batch = root/name
    if batch.exists():
        raise ValueError('Lote ja existe; retomar pelos jobs atuais, sem sobrescrever planejamento')
    scenes = read(args.cenarios)
    if not isinstance(scenes, list) or not 1 <= args.chats <= args.quantidade <= len(scenes):
        raise ValueError('Quantidade/chats incompativeis com lista de cenarios')
    fields = ('family', 'slug', 'environment', 'surface', 'lighting', 'sleeves')
    for s in scenes:
        if any(not isinstance(s.get(k), str) or not s[k].strip() for k in fields):
            raise ValueError('Cenario sem campos obrigatorios')
        safe_name(s['slug'])
    if len({s['slug'] for s in scenes}) != len(scenes) or len({s['environment'].strip().lower() for s in scenes}) != len(scenes):
        raise ValueError('Slugs ou ambientes repetidos no planejamento')
    used = set()
    for path in root.glob('*/manifesto.json'):
        for s in read(path).get('slots', []):
            if s.get('status') == 'approved' and s.get('environment'):
                used.add(s['environment'].strip().lower())
    if not args.permitir_repetidos:
        scenes = [s for s in scenes if s['environment'].strip().lower() not in used]
    if len(scenes) < args.quantidade:
        raise ValueError('Cenarios novos insuficientes; ampliar lista. Repeticao exige escolha explicita')
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**32)
    rng = random.Random(seed)
    families = collections.defaultdict(list)
    for s in scenes:
        families[s['family']].append(s)
    for group in families.values():
        rng.shuffle(group)
    selected = []
    while len(selected) < args.quantidade:
        keys = [k for k,v in families.items() if v]
        rng.shuffle(keys)
        for key in keys:
            selected.append(families[key].pop())
            if len(selected) == args.quantidade:
                break
    groups = [[] for _ in range(args.chats)]
    group_capacity = (args.quantidade + args.chats - 1) // args.chats
    genders = collections.Counter(s.get('gender') for s in selected)
    gender_caps = {k:v//args.chats for k,v in genders.items()} if None not in genders and all(v%args.chats==0 for v in genders.values()) else {}
    for s in selected:
        eligible = [i for i,g in enumerate(groups) if len(g)<group_capacity and (not gender_caps or sum(x.get('gender')==s['gender'] for x in g)<gender_caps[s['gender']])]
        if not eligible:
            raise ValueError('Distribuicao sem capacidade; revisar quotas/chats')
        scores = {i:(sum(x['family']==s['family'] for x in groups[i]),len(groups[i])) for i in eligible}
        best = min(scores.values())
        idx = rng.choice([i for i,score in scores.items() if score==best])
        groups[idx].append(s)
    base = (SKILL/'references/prompt_base.txt').read_text().strip()
    batch.mkdir(parents=True)
    for d in ('aprovadas', 'tentativas', 'planejamento', 'relatorios'):
        (batch/d).mkdir()
    manifest = dict(version=2, name=name, created_at=now(), status='planned', target_images=args.quantidade, target_chats=args.chats, planning_seed=seed, agent_model=args.modelo, reasoning=args.reasoning, requested_speed='standard', threads=[], slots=[])
    sid = 0
    for n,group in enumerate(groups,1):
        rng.shuffle(group)
        slots = []
        for s in group:
            sid += 1
            prompt = s.get('prompt') or base+'\n\nASSIGNED DISTINCT SCENE:\n'+s['environment']+'\nPreparation surface: '+s['surface']+'\nLighting: '+s['lighting']+'\nSleeves: '+s['sleeves']+'\n'
            if not prompt.startswith('Use case: photorealistic-natural.') or 'ASSIGNED DISTINCT SCENE:' not in prompt:
                raise ValueError('Prompt base invalido')
            slot = dict(s, id=f'{sid:03d}', chat=n, prompt=prompt, status='pending', attempts=[], approved_path=None)
            slot['prompt_sha256'] = hashlib.sha256(prompt.encode()).hexdigest()
            (batch/'planejamento'/f"{slot['id']}_{slot['slug']}.txt").write_text(prompt)
            slots.append(slot)
            manifest['slots'].append({k:v for k,v in slot.items() if k!='prompt'})
        job = dict(version=2, root=str(batch), chat=n, model=args.modelo, reasoning=args.reasoning, speed_requested='standard', slots=slots)
        path = batch/'chats'/f'chat_{n:02d}'/'job.json'
        write(path,job)
        write(path.with_name('manifesto.json'),dict(job,status='pending',technical_errors=[]))
    write(batch/'manifesto.json',manifest)
    print(json.dumps({'root':str(batch),'prompts':sid,'jobs':args.chats,'seed':seed}))


def locate(args):
    jobpath = Path(args.job).resolve()
    job = read(jobpath)
    root = Path(job['root']).resolve()
    if not jobpath.is_relative_to(root/'chats'):
        raise ValueError('Job fora da pasta de chats deste lote')
    manifestpath = jobpath.with_name('manifesto.json')
    wm = read(manifestpath)
    sid = f'{int(args.id):03d}'
    slot = next((s for s in wm['slots'] if s['id']==sid),None)
    if slot is None:
        raise ValueError('ID nao pertence ao job')
    return root, manifestpath, wm, slot


def validate_audio_binding(binding):
    if not isinstance(binding, dict) or any(not binding.get(k) for k in ('audio_path', 'audio_sha256', 'opening_text', 'transcript_source')):
        raise ValueError('Par exige audio real, SHA256, duas frases e origem da transcricao')
    audio = Path(binding['audio_path'])
    transcript = Path(binding['transcript_source'])
    if not audio.is_absolute() or not transcript.is_absolute() or not transcript.is_file():
        raise ValueError('Audio/transcricao precisam de caminhos absolutos existentes')
    if hashlib.sha256(audio.read_bytes()).hexdigest() != binding['audio_sha256']:
        raise ValueError('SHA256 do audio divergente')
    sentences = binding.get('opening_sentences')
    if not isinstance(sentences, list) or len(sentences) != 2 or any(not isinstance(s, str) or not s.strip() for s in sentences):
        raise ValueError('opening_sentences exige exatamente duas frases reais, revisadas')
    if binding['opening_text'] != ' '.join(sentences):
        raise ValueError('opening_text deve preservar as duas frases na ordem')
    evidence = transcript.read_text(encoding='utf-8')
    if any(s not in evidence for s in sentences):
        raise ValueError('Frases nao encontradas na fonte de transcricao indicada')


def preparar_pares(args):
    pairs = read(args.pares)
    if not isinstance(pairs, list) or not pairs or not 1 <= args.chats <= len(pairs):
        raise ValueError('Lista de pares/chats invalida')
    # Validar todos os insumos antes de criar a pasta ou despachar geracoes.
    for pair in pairs:
        validate_audio_binding(pair.get('audio_binding'))
        if not pair.get('hook_idea') or not pair.get('hook_video_prompt'):
            raise ValueError('Par exige conceito de hook e acao futura de seis segundos')
        for kind in ('recipe', 'hook'):
            scene = pair.get(kind, {})
            if any(not isinstance(scene.get(k), str) or not scene[k].strip() for k in ('family', 'slug', 'environment', 'prompt')):
                raise ValueError('Cada par exige recipe e hook com cenario e prompt integrais')
            safe_name(scene['slug'])
            if not scene['prompt'].startswith('Use case: photorealistic-natural.') or 'ASSIGNED DISTINCT SCENE:' not in scene['prompt']:
                raise ValueError('Prompt integral de imagem invalido')
        if any(s not in pair['hook']['prompt'] for s in pair['audio_binding']['opening_sentences']):
            raise ValueError('Prompt de hook deve conter as duas frases como contexto, sem imprimi-las na imagem')
    slugs = [p[k]['slug'] for p in pairs for k in ('recipe','hook')]
    if len(set(slugs)) != len(slugs):
        raise ValueError('Slugs de imagem repetidos')
    name = safe_name(args.nome or f'inicios_{len(pairs)}_'+dt.datetime.now().strftime('%Y_%m_%d_%H%M%S'))
    root = Path.home()/'Downloads'/'receita_gpt_image'/name
    if root.exists():
        raise ValueError('Lote ja existe; retomar os pares atuais')
    manifest = dict(version=3, name=name, root=str(root), created_at=now(), status='planned', target_images=2*len(pairs), target_pairs=len(pairs), target_videos=len(pairs), target_chats=args.chats, agent_model=args.modelo, reasoning=args.reasoning, requested_speed='standard', threads=[], slots=[], pairs=[], output_contract=dict(images_per_pair=2, hook_seconds=6, recipe_scenes=4, recipe_seconds=8, total_seconds=38, outputs_per_scene=1))
    jobs = [dict(version=3, root=str(root), chat=i+1, model=args.modelo, reasoning=args.reasoning, speed_requested='standard', slots=[], pairs=[]) for i in range(args.chats)]
    for i, pair in enumerate(pairs):
        job = jobs[i % args.chats]
        pid = f'{i+1:03d}'
        ids = {}
        for k, kind in enumerate(('recipe','hook'),1):
            sid = f'{2*i+k:03d}'
            scene = pair[kind]
            slot = dict(scene, id=sid, pair_id=pid, kind=kind, chat=job['chat'], status='pending', attempts=[], approved_path=None, prompt_sha256=hashlib.sha256(scene['prompt'].encode()).hexdigest())
            ids[kind] = sid
            job['slots'].append(slot)
            manifest['slots'].append({k:v for k,v in slot.items() if k!='prompt'})
        record = dict(id=pid, chat=job['chat'], recipe_image_id=ids['recipe'], hook_image_id=ids['hook'], hook_idea=pair['hook_idea'], hook_video_prompt=pair['hook_video_prompt'], audio_binding=pair['audio_binding'], status='pending')
        job['pairs'].append(record)
        manifest['pairs'].append(record)
    for d in ('aprovadas','tentativas','planejamento','relatorios'):
        (root/d).mkdir(parents=True, exist_ok=True)
    write(root/'planejamento/pares_entrada.json',pairs)
    for job in jobs:
        for s in job['slots']:
            (root/'planejamento'/f"{s['id']}_{s['slug']}.txt").write_text(s['prompt'],encoding='utf-8')
        p = root/'chats'/f"chat_{job['chat']:02d}"/'job.json'
        write(p,job)
        write(p.with_name('manifesto.json'),dict(job,status='pending',technical_errors=[]))
    write(root/'manifesto.json',manifest)
    print(json.dumps(dict(root=str(root),pairs=len(pairs),images=2*len(pairs),jobs=args.chats)))


def pair_results(manifest, slots):
    by_id = {s['id']:s for s in slots}
    complete = 0
    used = set()
    for pair in manifest.get('pairs',[]):
        validate_audio_binding(pair.get('audio_binding'))
        images = []
        for kind in ('recipe','hook'):
            sid = pair[kind+'_image_id']
            if sid in used or sid not in by_id:
                raise ValueError('Imagem ausente ou reutilizada entre pares')
            used.add(sid)
            s = by_id[sid]
            if s.get('pair_id') != pair['id'] or s.get('kind') != kind:
                raise ValueError('Tipo ou vinculo de imagem divergente no par')
            images.append(s)
        pair['status'] = 'approved' if all(s['status']=='approved' for s in images) else 'pending'
        complete += pair['status']=='approved'
    if manifest.get('pairs') and (len(used)!=len(slots) or len(manifest['pairs'])!=manifest['target_pairs']):
        raise ValueError('Pares nao cobrem todos os slots previstos')
    return complete


def registrar(args):
    root, manifestpath, wm, slot = locate(args)
    if args.call_id and any(a.get('call_id')==args.call_id for a in slot['attempts']):
        print('Chamada ja registrada; nenhuma copia ou contagem extra')
        return
    meta = png(args.source)
    if not args.call_id and any(a.get('source_path')==str(Path(args.source).absolute()) and a.get('sha256')==meta['sha256'] for a in slot['attempts']):
        print('Retorno source_path/hash ja registrado; nenhuma copia ou contagem extra')
        return
    if args.veredito=='approved' and (meta['width']<720 or meta['height']<1280 or meta['width']>=meta['height']):
        raise ValueError('Imagem aprovada deve ser vertical e no minimo 720x1280; enquadramento utilizavel exige QA visual')
    if args.veredito=='approved':
        for other in (root/'aprovadas').glob('*.png'):
            if not other.name.startswith('._') and other.name!=f"{slot['id']}_{slot['slug']}.png" and png(other)['sha256']==meta['sha256']:
                args.veredito='uncertain'
                args.motivo+='; hash repetido de '+other.name+', nao conta na meta'
                break
    n = len(slot['attempts'])+1
    if slot.get('approved_path') and args.veredito=='approved':
        old = root/slot['approved_path']
        if old.is_file() and png(old)['sha256'] != meta['sha256']:
            oldmeta = png(old)
            olddest = root/'tentativas'/f"{slot['id']}_{slot['slug']}_substituida_{oldmeta['sha256'][:12]}.png"
            copy_verified(old, olddest, oldmeta['sha256'])
            for a in slot['attempts']:
                if a.get('sha256')==oldmeta['sha256']:
                    a['saved_path']=str(olddest.relative_to(root))
                    a['selected']=False
    filename = f"{slot['id']}_{slot['slug']}.png" if args.veredito=='approved' else f"{slot['id']}_{slot['slug']}_t{n}_{meta['sha256'][:12]}.png"
    dest = root/('aprovadas' if args.veredito=='approved' else 'tentativas')/filename
    copy_verified(args.source,dest,meta['sha256'])
    attempt = dict(attempt=n, recorded_at=now(), source_path=str(Path(args.source).absolute()), saved_path=str(dest.relative_to(root)), verdict=args.veredito, reasons=[args.motivo], call_id=args.call_id, duration_seconds=args.duracao, **meta)
    if args.qa:
        attempt['qa']=read(args.qa)
    slot['attempts'].append(attempt)
    if args.veredito=='approved':
        slot['status']='approved'
        slot['approved_path']=attempt['saved_path']
    elif slot['status']!='approved':
        slot['status']='needs_retry'
    wm['status']='complete' if all(s['status']=='approved' for s in wm['slots']) else 'running'
    wm['updated_at']=now()
    write(manifestpath,wm)
    print(json.dumps({'id':slot['id'],'verdict':args.veredito,'path':str(dest),'sha256':meta['sha256']}))


def erro(args):
    root,path,wm,slot=locate(args)
    errors=wm.setdefault('technical_errors',[])
    if not args.call_id or not any(e.get('call_id')==args.call_id for e in errors):
        errors.append(dict(id=slot['id'],call_id=args.call_id,reason=args.motivo,recorded_at=now()))
        write(path,wm)
    print('Erro tecnico registrado, sem contar imagem aprovada')


def fechar(args):
    root=Path(args.lote).resolve()
    m=read(root/'manifesto.json')
    slots,errors,sources=[],[],[]
    for path in sorted(root.glob('chats/chat_*/manifesto.json')):
        wm=read(path)
        slots.extend(wm['slots'])
        sources.extend(a for s in wm['slots'] for a in s['attempts'])
        errors.extend(wm.get('technical_errors',[]))
    if len(slots)!=m['target_images'] or len({s['id'] for s in slots})!=len(slots):
        raise ValueError('Slots ausentes ou IDs repetidos')
    unique,approved,issues={},[],[]
    for slot in slots:
        if slot['status']!='approved':
            continue
        path=root/slot['approved_path']
        meta=png(path)
        selected=next((a for a in reversed(slot['attempts']) if a['saved_path']==slot['approved_path'] and a['verdict']=='approved'),None)
        if not selected or selected['sha256']!=meta['sha256']:
            raise ValueError('Arquivo nao corresponde a aprovacao registrada')
        if meta['sha256'] in unique:
            issues.append(f"{slot['id']}: hash repetido de {unique[meta['sha256']]}")
            slot['status']='duplicate'
            continue
        unique[meta['sha256']]=slot['id']
        approved.append(slot)
    # Uma copia fisica por hash, mantendo paths antigos como aliases leves.
    complete_pairs = pair_results(m,slots) if m.get('pairs') else None
    files=[p for d in ('aprovadas','tentativas') for p in sorted((root/d).glob('*.png')) if not p.is_symlink() and not p.name.startswith('._')]
    canonical={}
    for path in files:
        sha=png(path)['sha256']
        if sha in canonical:
            temp=path.with_name(path.name+'.link')
            temp.symlink_to(os.path.relpath(canonical[sha],path.parent))
            os.replace(temp,path)
        else:
            canonical[sha]=path
    aliases=0
    if args.consolidar_cache:
        for a in sources:
            target=canonical.get(a['sha256'])
            if target and cache_alias(a['source_path'],target,a['sha256']):
                aliases+=1
    m.update(slots=slots,status='complete' if len(approved)==m['target_images'] else 'partial',approved_count=len(approved),recorded_calls=len(sources)+len(errors),technical_errors=errors,issues=issues,updated_at=now(),cache_aliases=aliases)
    if complete_pairs is not None:
        m['approved_pair_count']=complete_pairs
    write(root/'manifesto.json',m)
    cards=[]
    for s in sorted(approved,key=lambda x:x['id']):
        label=html.escape(s['id']+' '+s['slug'])
        src=html.escape(s['approved_path'],quote=True)
        gender=html.escape(s.get('gender',''),quote=True)
        detail=html.escape(('Mulher' if gender=='female' else 'Homem' if gender=='male' else '') + (f" | {s['min_age']}+" if s.get('min_age') else '') + ' | ' + s['family'])
        cards.append(f'<article data-gender="{gender}"><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt="{label}"></a><p>{label}</p><small>{detail}</small></article>')
    page='<!doctype html><html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Imagens de receita</title><style>body{font:16px system-ui;margin:30px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px}img{width:100%;height:auto}article{border:1px solid #ddd;padding:10px}</style>'
    filters=''
    if any(s.get('gender') for s in approved):
        filters='<p>Filtrar por maos: <select id="gender"><option value="">Todas</option><option value="female">Femininas</option><option value="male">Masculinas</option></select></p>'
    if m.get('pairs'):
        cards=[]
        by_id={s['id']:s for s in slots}
        for pair in m['pairs']:
            images=[]
            for kind,label in (('recipe','Receita'),('hook','Hook inicial')):
                s=by_id[pair[kind+'_image_id']]
                if s['status']=='approved':
                    src=html.escape(s['approved_path'],quote=True)
                    images.append(f'<div><b>{label}</b><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt="{label}"></a></div>')
            title=html.escape(pair['id']+' | '+pair['audio_binding'].get('audio_id',Path(pair['audio_binding']['audio_path']).name))
            opening=html.escape(pair['audio_binding']['opening_text'])
            cards.append(f'<article><p>{title}</p><p>{opening}</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">'+''.join(images)+'</div></article>')
        filters=''
        page+='<style>main{grid-template-columns:repeat(auto-fill,minmax(460px,1fr))}@media(max-width:520px){main{grid-template-columns:1fr}}</style>'
    heading=f'{complete_pairs}/{m["target_pairs"]} inicios completos, ' if complete_pairs is not None else ''
    page+=f'<h1>{heading}{len(approved)}/{m["target_images"]} imagens aprovadas</h1><p><a href="relatorios/relatorio.md">Relatorio</a></p>'+filters+'<main>'+''.join(cards)+'</main>'
    if filters:
        page+='<script>document.getElementById("gender").addEventListener("change",function(){document.querySelectorAll("article").forEach(a=>{a.style.display=(!this.value||a.dataset.gender===this.value)?"":"none"})})</script>'
    page+='</html>'
    (root/'galeria.html').write_text(page)
    report=f'# Lote {m["name"]}\n\nEstado: {m["status"]}. Aprovadas: {len(approved)}/{m["target_images"]}.\n\nChamadas registradas: {m["recorded_calls"]}, incluindo {len(errors)} erros tecnicos. Reconciliar com itens nativos do Codex antes de apresentar como contagem total real.\n\nModelo solicitado: {m["agent_model"]}, reasoning {m["reasoning"]}, Standard solicitado. Custo e tokens do gerador nao expostos. QA visual feito pelo agente; helper verifica arquivos/metadados.\n\nImagens finais: aprovadas/. Candidatos nao selecionados: tentativas/. Uma copia fisica por hash; aliases de cache deste lote: {aliases}.\n'
    if issues:
        report+='\n'+ '\n'.join(issues)+'\n'
    if complete_pairs is not None:
        report+=f'\nInicios completos: {complete_pairs}/{m["target_pairs"]}. Cada inicio tem receita e hook independentes, vinculados por pair_id e audio real/SHA256/duas primeiras frases. A galeria mostra pares. Manifesto de pares completos, sem iniciar videos.\n'
    (root/'relatorios'/'relatorio.md').write_text(report)
    print(json.dumps({'approved':len(approved),'target':m['target_images'],'issues':issues,'cache_aliases':aliases,'root':str(root)}))
    return 0 if m['status']=='complete' else 2


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('preparar');a.add_argument('--cenarios',required=True);a.add_argument('--nome');a.add_argument('--quantidade',type=int,default=100);a.add_argument('--chats',type=int,default=10);a.add_argument('--seed',type=int);a.add_argument('--modelo',default='gpt-6-luna');a.add_argument('--reasoning',default='medium');a.add_argument('--permitir_repetidos',action='store_true');a.set_defaults(fn=preparar)
    a=sub.add_parser('preparar-pares');a.add_argument('--pares',required=True);a.add_argument('--nome');a.add_argument('--chats',type=int,default=1);a.add_argument('--modelo',default='gpt-6-luna');a.add_argument('--reasoning',default='medium');a.set_defaults(fn=preparar_pares)
    a=sub.add_parser('registrar');a.add_argument('--job',required=True);a.add_argument('--id',required=True);a.add_argument('--source',required=True);a.add_argument('--veredito',choices=['approved','rejected','uncertain'],required=True);a.add_argument('--motivo',required=True);a.add_argument('--call-id');a.add_argument('--duracao',type=float);a.add_argument('--qa');a.set_defaults(fn=registrar)
    a=sub.add_parser('erro');a.add_argument('--job',required=True);a.add_argument('--id',required=True);a.add_argument('--call-id');a.add_argument('--motivo',required=True);a.set_defaults(fn=erro)
    a=sub.add_parser('fechar');a.add_argument('--lote',required=True);a.add_argument('--consolidar_cache',action='store_true');a.set_defaults(fn=fechar)
    args=p.parse_args()
    try:
        return args.fn(args) or 0
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:
        print(str(e),file=sys.stderr)
        return 1


if __name__=='__main__':
    sys.exit(main())
