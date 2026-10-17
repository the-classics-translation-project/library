"""Deterministic, deliberately limited US/Japan admission rules for Gutenberg TXT.

This records a project eligibility decision from provider evidence, not legal or
human review. Unknown cases are held. No source prose is executed or sent to AI.
"""
from datetime import date, timedelta
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from legacy_v1 import check, digest

LEGACY_RULE_VERSION = 'gutenberg-us-jp-v1'
RULE_VERSION = 'gutenberg-us-jp-v2'
WARTIME_DAYS = 4180  # Maximum in the cited JASRAC country table; applied to everyone.
EXTENSION_DATE = date(2018, 12, 30)
REFERENCES = [
    'https://www.gutenberg.org/help/bibliographic_record.html',
    'https://www.gutenberg.org/policy/license',
    'https://www.bunka.go.jp/seisaku/chosakuken/hokaisei/kantaiheiyo_chosakuken/1411890.html',
    'https://www.jasrac.or.jp/aboutus/wartime/pdf/wartime.pdf',
]
NS = {'pg': 'http://www.gutenberg.org/2009/pgterms/',
      'dc': 'http://purl.org/dc/terms/', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
RDF = NS['rdf']
LITERARY_ROLES = {'creator', 'aut', 'trl', 'edt', 'ill', 'aui', 'aft', 'ctb', 'cmm', 'ann', 'adp'}


def official_url(url: str) -> bool:
    parsed = urlparse(url)
    return (parsed.scheme == 'https' and parsed.hostname in {'www.gutenberg.org', 'gutenberg.org'}
            and parsed.port in (None, 443) and not parsed.username and not parsed.password)


def fetch_metadata(ebook_id: int) -> tuple[bytes, dict]:
    check(type(ebook_id) is int and 0 < ebook_id < 10_000_000, 'Invalid Gutenberg ID')
    url = f'https://www.gutenberg.org/ebooks/{ebook_id}.rdf'
    request = Request(url, headers={'User-Agent': 'ClassicsTranslationProject/0.1 (requested book metadata)'})
    with urlopen(request, timeout=45) as response:
        check(official_url(response.geturl()), 'Metadata redirected outside the official HTTPS provider')
        raw = response.read(2 * 1024 * 1024 + 1)
        resolved = response.geturl()
    check(len(raw) <= 2 * 1024 * 1024, 'Metadata exceeds 2 MiB limit')
    return raw, {'requested_url': url, 'resolved_url': resolved, 'sha256': digest(raw)}


def parse_metadata(raw: bytes, ebook_id: int) -> dict:
    check(len(raw) <= 2 * 1024 * 1024, 'Metadata exceeds 2 MiB limit')
    text = raw.decode('utf-8-sig')
    check('\x00' not in text and not re.search(r'<!\s*(?:DOCTYPE|ENTITY)', text, re.I), 'XML DTDs/entities are not accepted')
    root = ET.fromstring(text)
    books = root.findall('pg:ebook', NS)
    check(len(books) == 1 and books[0].get(f'{{{RDF}}}about') in
          {f'ebooks/{ebook_id}', f'http://www.gutenberg.org/ebooks/{ebook_id}',
           f'https://www.gutenberg.org/ebooks/{ebook_id}'}, 'Metadata Gutenberg ID mismatch')
    book = books[0]
    def texts(path):
        return [e.text.strip() for e in book.findall(path, NS) if e.text and e.text.strip()]
    people = []
    for relation in book:
        agents = relation.findall('pg:agent', NS)
        if agents or relation.tag in {f'{{{NS["dc"]}}}creator', f'{{{NS["dc"]}}}contributor'} or relation.tag.startswith('{http://id.loc.gov/vocabulary/relators/'):
            role = relation.tag.rsplit('}', 1)[-1]
            if relation.tag not in {f'{{{NS["dc"]}}}creator', f'{{{NS["dc"]}}}contributor'} and not relation.tag.startswith('{http://id.loc.gov/vocabulary/relators/'):
                role = relation.tag
            # Unresolved references are retained as missing evidence, not dropped.
            for agent in agents or [None]:
                def vals(name):
                    return [] if agent is None else [(e.text or '').strip() for e in agent.findall('pg:'+name, NS)]
                people.append({'role': role, 'names': vals('name'), 'death_dates': vals('deathdate')})
    return {'ebook_id': ebook_id, 'titles': texts('dc:title'), 'rights': texts('dc:rights'),
            'languages': texts('dc:language/rdf:Description/rdf:value'),
            'types': texts('dc:type/rdf:Description/rdf:value'),
            'contributors': people, 'publication_statements': texts('pg:marc260'),
            'credits': texts('pg:marc508'), 'notes': texts('dc:description')}


def japan_expiry_bound(death_year: int) -> tuple[date, str]:
    """An upper bound for supported lifetime-published, named literary works.

    Always include the longest listed wartime addition, even when not applicable.
    Pre-2018 expiry remains expired; never revive it by applying life+70 blindly.
    """
    old = date(death_year + 50, 12, 31) + timedelta(days=WARTIME_DAYS)
    if old < EXTENSION_DATE:
        return old, 'life+50+4180 days expired before 2018 extension; no revival'
    return date(death_year + 70, 12, 31) + timedelta(days=WARTIME_DAYS), 'life+70+4180 days'



def validate_supplement(supplement: dict, ebook_id: int) -> dict:
    """Validate version-controlled, per-book cited evidence (not an Issue waiver)."""
    keys = {'schema_version', 'ebook_id', 'publication', 'production_credit', 'transcriber_note'}
    check(isinstance(supplement, dict) and set(supplement) <= keys and
          supplement.get('schema_version') == 1 and supplement.get('ebook_id') == ebook_id,
          'Invalid source admission evidence identity or fields')
    check(any(k in supplement for k in ('publication', 'production_credit', 'transcriber_note')),
          'Empty source admission evidence')
    def cited(item, fields, provider=False):
        check(isinstance(item, dict) and set(item) == fields, 'Invalid admission evidence fields')
        check(all(isinstance(v, str) and 0 < len(v.strip()) <= 1000
                  for k, v in item.items() if k != 'year'),
              'Source admission evidence requires bounded nonempty text')
        url = urlparse(item['url'])
        check(url.scheme == 'https' and bool(url.hostname) and url.port in (None, 443)
              and not url.username and not url.password
              and url.hostname not in {'localhost', '127.0.0.1'},
              'Evidence citation must be HTTPS')
        if provider:
            check(url.hostname in {'www.gutenberg.org', 'gutenberg.org'} and
                  url.path == f'/ebooks/{ebook_id}',
                  'Production evidence must cite the matching official Gutenberg ebook')
    if 'publication' in supplement:
        item = supplement['publication']
        cited(item, {'year', 'title', 'publisher', 'authority', 'url', 'basis'})
        check(type(item['year']) is int and 1000 <= item['year'] <= 1970,
              'External publication year outside supported scope')
    if 'production_credit' in supplement:
        item = supplement['production_credit']
        cited(item, {'text', 'url', 'basis'}, provider=True)
        check(bool(re.fullmatch(r'Revised by [A-Za-z .-]{3,100}\\.', item['text'])),
              'Only a named, exact Gutenberg revision credit can be assessed')
    if 'transcriber_note' in supplement:
        item = supplement['transcriber_note']
        cited(item, {'text', 'url', 'basis'}, provider=True)
        check(item['text'].startswith(("[Transcriber's Note:", "[Transcriber’s Note:")) and
              item['text'].endswith(']') and 'photo-reprint' in item['text'],
              'Only an exact Gutenberg photo-reprint transcription note is supported')
    return supplement


def _without_credit_line(text: str, exact: str) -> tuple[str, int]:
    """Ignore one complete, explicitly assessed credit line only while checking."""
    pattern = re.compile(r'(?m)^[ \t]*' +
                         r'[ \t]+'.join(re.escape(w) for w in exact.split()) +
                         r'[ \t]*$')
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        return text, len(matches)
    match = matches[0]
    return text[:match.start()] + text[match.end():], 1


def assess_metadata(facts: dict, as_of: date, supplement: dict | None = None) -> dict:
    reasons = []
    def hold(country, code, detail):
        reasons.append({'country': country, 'code': code, 'detail': detail})
    us = facts['rights'] == ['Public domain in the USA.']
    if not us:
        hold('US', 'us_public_domain_not_confirmed', 'Gutenberg does not give one explicit US public-domain designation; permission-only or ambiguous records are held.')
    if len(facts['titles']) != 1:
        hold('JP', 'title_missing_or_ambiguous', 'One identifiable title is required.')
    if facts['types'] != ['Text'] or facts['languages'] != ['en']:
        hold('JP', 'unsupported_source_type_or_language', 'This rule supports English plain-text literary packages only.')
    years = []
    if supplement is not None:
        validate_supplement(supplement, facts['ebook_id'])
    extra_pub = supplement.get('publication') if supplement else None
    if not facts['publication_statements'] and extra_pub is None:
        hold('JP', 'source_publication_missing', 'No original source-publication statement is supplied; Gutenberg release dates are not print publication dates.')
    if extra_pub:
        if len(facts['titles']) != 1 or extra_pub['title'].casefold() != facts['titles'][0].casefold():
            hold('JP', 'publication_evidence_title_mismatch', 'Cited historical title differs from Gutenberg metadata.')
        elif not facts['publication_statements']:
            years.append(extra_pub['year'])
    for statement in facts['publication_statements']:
        # Only an unqualified MARC publication-year subfield is understood.
        matches = re.findall(r'\$c([^$]+)', statement)
        if len(matches) != 1 or not re.fullmatch(r'[1-9][0-9]{3}\.?', matches[0].strip()):
            hold('JP', 'source_publication_ambiguous', 'The source publication year is absent, qualified, or outside the supported MARC format.')
        else:
            years.append(int(matches[0].strip().rstrip('.')))
    if extra_pub and facts['publication_statements'] and years and extra_pub['year'] not in years:
        hold('JP', 'publication_evidence_conflict', 'Cited historical and Gutenberg publication years disagree.')
    contributors = facts['contributors']
    if not any(p['role'] in {'creator', 'aut'} for p in contributors):
        hold('JP', 'author_missing', 'No named author is recorded.')
    bounds = []
    for person in contributors:
        names, deaths = person['names'], person['death_dates']
        name = names[0] if names else '(unnamed contributor)'
        if person['role'] not in LITERARY_ROLES:
            hold('JP', 'unsupported_contributor_role', f'Unresolved contributor role for {name}: {person["role"]}.')
        if (len(names) != 1 or re.search(r'\b(anonymous|unknown|various|unidentified|pseudonym)\b', name, re.I)
                or len(deaths) != 1 or not re.fullmatch(r'[1-9][0-9]{3}', deaths[0])
                or not 1000 <= int(deaths[0]) <= as_of.year):
            hold('JP', 'contributor_identity_or_death_missing', f'An identified contributor and exact death year are required: {name}.')
            continue
        death = int(deaths[0])
        if any(year > death or year > 1970 for year in years):
            hold('JP', 'posthumous_or_later_edition', f'Source publication is later than {name}\u2019s death or outside the supported pre-1971 lifetime-publication scope.')
        expiry, basis = japan_expiry_bound(death)
        bounds.append({'name': name, 'role': person['role'], 'death_year': death,
                       'expiry_upper_bound': expiry.isoformat(), 'basis': basis})
        if expiry >= as_of:
            hold('JP', 'japan_term_not_cleared', f'The conservative Japanese term bound for {name} has not elapsed ({expiry.isoformat()}).')
    # Production/transcription credits alone are not literary coauthorship. Signals
    # of revision, translation or added matter require clearer contributor evidence.
    credits = '\n'.join(facts['credits'])
    approved = supplement.get('production_credit') if supplement else None
    if approved:
        credits, count = _without_credit_line(credits, approved['text'])
        if count != 1:
            hold('JP', 'production_credit_evidence_mismatch',
                 'Exact cited Gutenberg revision credit missing or duplicated.')
    contextual = '\n'.join([credits] + [n for n in facts['notes'] if not n.startswith('Wikipedia page about this book:')])
    signal = re.search(r'\b(revis(?:ed|ion)|translat\w*|edit(?:ed|ion with)|adapt\w*|introduction|foreword|afterword|annotat\w*|copyright|permission|posthum\w*|unpublished|anonymous)\b', contextual, re.I)
    if signal:
        line = contextual[contextual.rfind('\n', 0, signal.start()) + 1:].split('\n', 1)[0]
        hold('JP', 'edition_contributions_uncertain', 'Unresolved edition contribution or rights statement in provider metadata: '+line[:240])
    jp = not any(r['country'] == 'JP' for r in reasons)
    return {'countries': {'US': {'status': 'pass' if us else 'hold', 'basis': 'Gutenberg explicit rights designation'},
                          'JP': {'status': 'pass' if jp else 'hold', 'wartime_days_upper_bound': WARTIME_DAYS,
                                 'contributor_terms': bounds}},
            'eligible': us and jp, 'reasons': reasons}


def check_package(raw: bytes, ebook_id: int, facts: dict, supplement: dict | None = None) -> list[dict]:
    """Reject identity mismatches or unaccounted literary contribution signals."""
    text = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    reasons = []
    def hold(code, detail):
        reasons.append({'country': 'package', 'code': code, 'detail': detail})
    starts = list(re.finditer(r'^\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .+? \*\*\*\s*$', text, re.M | re.I))
    ends = list(re.finditer(r'^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK .+? \*\*\*\s*$', text, re.M | re.I))
    if len(starts) != 1 or len(ends) != 1 or starts[0].end() >= ends[0].start():
        hold('package_boundaries_uncertain', 'Expected one ordered pair of Gutenberg START/END markers.')
        return reasons
    header = text[:starts[0].start()]
    body = text[starts[0].end():ends[0].start()]
    if supplement:
        validate_supplement(supplement, ebook_id)
        credit = supplement.get('production_credit')
        if credit:
            pos = header.find('Credits:')
            tail = header[pos:] if pos >= 0 else ''
            cleaned, count = _without_credit_line(tail, credit['text'])
            if count != 1:
                hold('package_evidence_mismatch', 'Approved production-credit line absent or duplicated in header.')
            else:
                header = header[:pos] + cleaned
        note = supplement.get('transcriber_note')
        if note:
            pattern = re.compile(r'\s+'.join(re.escape(word) for word in note['text'].split()))
            matches = list(pattern.finditer(body))
            if len(matches) != 1 or body[:matches[0].start()].strip():
                hold('package_evidence_mismatch', 'Approved historical photo-reprint note missing from body opening.')
            else:
                match = matches[0]
                body = body[:match.start()] + body[match.end():]
    if not body.strip():
        hold('package_body_missing', 'The package contains no literary body.')
    ids = re.findall(r'\[EBook\s*#\s*(\d+)\]', header, re.I)
    if ids != [str(ebook_id)]:
        hold('package_id_mismatch', 'The package header does not identify exactly the requested Gutenberg number.')
    def folded(value):
        import unicodedata
        value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
        value = re.sub(r'\([^)]*\)', '', value)
        return re.findall(r'[a-z0-9]+', value.lower())
    titles = re.findall(r'^Title:\s*(.+)$', header, re.M)
    if len(titles) != 1 or folded(titles[0]) != folded(facts['titles'][0]):
        hold('package_title_mismatch', 'The header title does not match the assessed metadata.')
    authors = re.findall(r'^Author:\s*(.+)$', header, re.M)
    declared = [p['names'][0] for p in facts['contributors'] if p['role'] in {'creator', 'aut'} and len(p['names']) == 1]
    if len(authors) != 1 or len(declared) != 1 or sorted(folded(authors[0])) != sorted(folded(declared[0])):
        hold('package_author_unresolved', 'The header author cannot be matched unambiguously to one assessed author.')
    if not re.search(r'^Language:\s*English\s*$', header, re.M | re.I):
        hold('package_language_unresolved', 'The package does not confirm the supported English language.')
    # Reject unstructured extra contributions, including those missing from RDF.
    if re.search(r'^\s*(?:Translator|Editor|Illustrator|Contributor):|\b(?:translated|edited|illustrated|revised|adapted|annotated)\s+by\b|\b(?:introduction|foreword|afterword|preface|notes)\s+by\b|\bwith\s+(?:a|an)\s+(?:new\s+)?(?:introduction|foreword|afterword)\b', header + '\n' + body, re.M | re.I):
        hold('package_contributions_uncertain', 'The package identifies additional or revised contributions not resolved by this rule.')
    if re.search(r'^\s*(?:INTRODUCTION|FOREWORD|AFTERWORD)\s*$|\btranscriber[’\']?s?\s+note\b', body, re.M | re.I):
        hold('package_added_matter_uncertain', 'The package contains introductory or transcription notes whose separate rights are unresolved.')
    if re.search(r'\bcopyright\b|©|all rights reserved', header + '\n' + body, re.I):
        hold('package_rights_notice', 'The package header or literary body contains a rights notice requiring a more specific rule.')
    return reasons
