# Expands <div class="strip" data-imgs="..."> into linked images with intrinsic sizes,
# and <div class="reviews"></div> into the Letterboxd reviews listed in reviews.json.
import html as h, json, os, re, urllib.request
from PIL import Image

USER = 'edvinjoseph'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'}
CACHE = 'letterboxd-cache.json'   # last good fetch, so the page still builds offline

src = open('src.html', encoding='utf-8').read()

def strip(m):
    names, phone, alt = m.group(1).split(), m.group(2), m.group(3)
    cap = 520 if phone else 180
    out = []
    for i, n in enumerate(names, 1):
        w, ht = Image.open('w/' + n).size
        if ht > cap or phone: w, ht = round(w * cap / ht), cap
        img = f'<img src="w/{n}" width="{w}" height="{ht}" style="width:{w}px" alt="{alt} {i}" loading="lazy">'
        if phone:
            top = '#%02x%02x%02x' % Image.open('w/' + n).convert('RGB').getpixel((4, 4))   # fills the band above the screenshot, so no seam shows
            out.append(f'<a class="phone{" pixel" if "pixel" in phone else ""}' + f'" href="w/{n}" target="_blank" rel="noopener"><span class="screen" style="--top:{top};--w:{w}px"><span class="shot">{img}</span></span></a>')
        else: out.append(f'<a href="w/{n}" target="_blank" rel="noopener">{img}</a>')
    return '<div class="strip">' + ''.join(out) + '</div>'

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()

def meta(page, prop):
    m = re.search(rf'<meta (?:property|name)="{prop}" content="([^"]*)"', page)
    return h.unescape(m.group(1)) if m else ''

def film(slug):
    """Title, year, poster and rating for one film, from its Letterboxd pages."""
    page = get(f'https://letterboxd.com/film/{slug}/').decode('utf-8', 'replace')
    ld = json.loads(re.search(r'<script type="application/ld\+json">\s*(?:/\*.*?\*/)?\s*(\{.*?\})\s*(?:/\*.*?\*/)?\s*</script>', page, re.S).group(1))
    m = re.match(r'(.*) \((\d{4})\)$', meta(page, 'og:title'))
    title, year = (m.group(1), m.group(2)) if m else (ld['name'], ld.get('dateCreated', '')[:4])
    review = get(f'https://letterboxd.com/{USER}/film/{slug}/').decode('utf-8', 'replace')
    stars = re.search(r'([★½]+)', meta(review, 'og:title'))
    rating = (stars.group(1).count('★') + 0.5 * stars.group(1).count('½')) if stars else None
    poster = f'w/posters/{slug}.jpg'
    if not os.path.exists(poster):
        os.makedirs('w/posters', exist_ok=True)
        url = re.sub(r'-0-\d+-0-\d+-crop', '-0-230-0-345-crop', ld['image'])
        open(poster, 'wb').write(get(url))
    return {'title': title, 'year': year, 'rating': rating, 'text': meta(review, 'og:description'), 'poster': poster}

def reviews(_):
    entries = json.load(open('reviews.json', encoding='utf-8'))
    cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    out = []
    for e in entries:
        slug = e['film']
        try:
            cache[slug] = film(slug)
        except Exception as err:
            if slug not in cache: raise
            print(f'{slug}: using cached details ({err})')
        f = cache[slug]
        quote = e.get('quote') or f['text']
        rating = f['rating']
        score = f', {rating:g}/5' if rating is not None else ''
        out.append(
            f'<article class="review"><img class="poster" src="{f["poster"]}" width="76" height="114" alt="Poster for {h.escape(f["title"])}" loading="lazy">'
            f'<div><h3><a href="https://letterboxd.com/{USER}/film/{slug}/" target="_blank" rel="noopener">{h.escape(f["title"])} ({f["year"]}){score}</a></h3>'
            f'<blockquote><p>{h.escape(quote)}</p></blockquote></div></article>')
    # forget films that are no longer listed, and their posters
    keep = {e['film'] for e in entries}
    cache = {k: v for k, v in cache.items() if k in keep}
    for name in os.listdir('w/posters'):
        if name[:-4] not in keep: os.remove('w/posters/' + name)
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return '\n  '.join(out)

page = re.sub(r'<div class="strip" data-imgs="([^"]+)"( data-frame="(?:phone|pixel)")? data-alt="([^"]+)"></div>', strip, src)
page = re.sub(r'<div class="reviews"></div>', reviews, page)

# Every picture is served as WebP at the size it is shown, and twice that for sharp screens. The originals stay in w/
# for the links that open them. Variants live in w/opt/ and are only remade when their source changes.
FIXED = {'gate': 186, 'seal': 63, 'poster': 76}                 # shown at a set width by the stylesheet
BOARD = {'moon': (640, '92vw'), 'alerts': (430, '92vw'), 'hud': (210, '92vw')}   # the Daac board: desktop width, phone width
used = set()

def variant(path, width):
    name = path[2:].replace('/', '-').rsplit('.', 1)[0]
    out = f'w/opt/{name}-{width}.webp'
    used.add(out)
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(path):
        im = Image.open(path)
        im = im.convert('RGBA' if 'A' in im.getbands() or 'transparency' in im.info else 'RGB')
        if width < im.width: im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(out, 'WEBP', quality=84, method=6)
        if im.mode == 'RGBA':                                   # flat line art is often smaller lossless, and exact
            alt = out + '.tmp'
            im.save(alt, 'WEBP', lossless=True, quality=100, method=6)
            if os.path.getsize(alt) < os.path.getsize(out): os.replace(alt, out)
            else: os.remove(alt)
    return out

def optimise(m):
    tag = m.group(0)
    src = re.search(r'src="(w/[^"]+\.(?:png|jpe?g))"', tag)
    if not src or 'vwm-1' in src.group(1): return tag           # the 3D Mac's screen draws from the original
    path = src.group(1)
    nat = Image.open(path).width
    shown = re.search(r' data-show="(\d+)" data-phone="([^"]+)"', tag)
    if shown:
        wide, phone = int(shown.group(1)), shown.group(2)
        sizes = sorted({min(nat, s) for s in (wide // 2, wide, wide * 2)})
        srcset = ', '.join(f'{variant(path, s)} {s}w' for s in sizes)
        return tag.replace(shown.group(0), '').replace(f'src="{path}"', f'src="{variant(path, min(nat, wide))}" srcset="{srcset}" sizes="(max-width: 860px) {phone}, {wide}px"')
    if path.startswith('w/daac/'):
        wide, phone = BOARD.get(path.split('/')[-1].split('.')[0], (250, '46vw'))
        sizes = sorted({min(nat, s) for s in (wide // 2, wide, wide * 2)})
        srcset = ', '.join(f'{variant(path, s)} {s}w' for s in sizes)
        mid = variant(path, min(nat, wide))
        return tag.replace(f'src="{path}"', f'src="{mid}" srcset="{srcset}" sizes="(max-width: 860px) {phone}, {wide}px"')
    fixed = re.search(r'style="width:(\d+)px', tag)
    cls = re.search(r'class="(\w+)', tag)
    shown = int(fixed.group(1)) if fixed else FIXED.get(cls.group(1) if cls else '', nat)
    one, two = min(nat, shown), min(nat, shown * 2)
    srcset = f'{variant(path, one)} 1x' + (f', {variant(path, two)} 2x' if two > one else '')
    return tag.replace(f'src="{path}"', f'src="{variant(path, one)}" srcset="{srcset}"')

os.makedirs('w/opt', exist_ok=True)
page = re.sub(r'<img [^>]+>', optimise, page)
page = page.replace(' loading="lazy"', '')                       # everything loads up front, so nothing appears late
for name in os.listdir('w/opt'):
    if 'w/opt/' + name not in used: os.remove('w/opt/' + name)
open('index.html', 'w', encoding='utf-8').write(page)
print(page.count('<img'), 'images')
