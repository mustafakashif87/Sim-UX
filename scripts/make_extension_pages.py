# ruff: noqa: E501  (HTML and CSS string lines)
"""Generate the P4, P5, P7 and P8 seeded page pairs (B13-B17, B20-B25).

Each pair comes from one template with a BUG marker, so the two files
differ only in the seeded bug. Run from the repo root:
    python scripts/make_extension_pages.py test-app
"""

import sys
from pathlib import Path

OUT = Path(sys.argv[1])

HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} – SimShop</title>
  <link rel="stylesheet" href="styles.css">
{style}</head>
<body>
{header}"""
HEADER = """  <header>
    <span class="brand">SimShop</span>
    <nav aria-label="Site"><a href="index.html">All pages</a></nav>
  </header>
"""
FOOT = """</body>
</html>
"""


def page(name, title, body, script, style="", header=HEADER):
    style_block = f"  <style>\n{style}  </style>\n" if style else ""
    html = HEAD.format(title=title, style=style_block, header=header) + body
    html += f"  <script>\n{script}  </script>\n" + FOOT
    (OUT / name).write_text(html, encoding="utf-8", newline="\n")


def pair(stem, title, make):
    for version in ("a", "b"):
        body, script, style, header = make(version == "a")
        page(f"{stem}-{version}.html", title, body, script, style, header)


# Every final button is disabled once the submission passes validation, so a
# double press sends one request (SEEDED_BUGS.md, B4 note).
SUBMIT = """    let sent = false;
    async function submit(url, body, done) {{
      if (sent) return;  // links cannot be disabled
      sent = true;
      document.querySelectorAll('button').forEach((b) => {{ b.disabled = true; }});
      await fetch(url, {{ method: 'POST', body }});
      done();
    }}
"""


# B13 feedback: confirmation outside a live region (P4 status_not_announced)
def feedback(bug):
    msg = '<p id="msg" class="ok"></p>' if bug else '<p id="msg" role="status"></p>'
    body = f"""  <main>
    <h1>Send us feedback</h1>
    <form id="form" novalidate>
      <div class="field">
        <label for="text">Your feedback</label>
        <textarea id="text"></textarea>
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Send feedback</button>
    </form>
    {msg}
    <div id="again"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    const form = document.getElementById('form');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = document.getElementById('text').value.trim();
      if (!text) {
        document.getElementById('error').textContent = 'Write your feedback first.';
        return;
      }
      submit('api/feedback', text, () => {
        form.hidden = true;
        document.getElementById('msg').textContent = 'Thanks, your feedback was sent.';
        document.getElementById('again').innerHTML =
          '<button type="button" class="secondary">Send more feedback</button>';
      });
    });
"""
    )
    return body, script, "", HEADER


# B14 size: a div-based picker (P4 non_semantic_control)
SIZES = ["UK 6", "UK 7", "UK 8", "UK 9"]


def size(bug):
    if bug:
        picker = "\n".join(f'        <div class="size" data-size="{s}">{s}</div>' for s in SIZES)
        picker = f'      <div class="field">\n        <span>Size</span>\n{picker}\n      </div>'
        chosen = "document.querySelector('.size.on')?.dataset.size"
        extra = """    document.querySelectorAll('.size').forEach((el) => el.addEventListener('click', () => {
      document.querySelectorAll('.size').forEach((o) => o.classList.remove('on'));
      el.classList.add('on');
    }));
"""
    else:
        radios = "\n".join(
            f'        <label class="size-row"><input type="radio" name="size" value="{s}"> {s}</label>'
            for s in SIZES
        )
        picker = f'      <fieldset class="field">\n        <legend>Size</legend>\n{radios}\n      </fieldset>'
        chosen = "document.querySelector('input[name=size]:checked')?.value"
        extra = ""
    body = f"""  <main>
    <h1>Running trainers</h1>
    <p>Light trainers for road running, $65.00</p>
    <form id="form" novalidate>
{picker}
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Add to basket</button>
    </form>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + extra
        + f"""    document.getElementById('form').addEventListener('submit', (e) => {{
      e.preventDefault();
      const chosen = {chosen};
      if (!chosen) {{
        document.getElementById('error').textContent = 'Choose a size.';
        return;
      }}
      submit('api/basket', chosen, () => {{
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Added to basket</h2>';
      }});
    }});
"""
    )
    style = """    .size { display: inline-block; min-width: 56px; padding: 10px; margin: 4px;
            border: 1px solid #888; border-radius: 4px; text-align: center; cursor: pointer; }
    .size.on { background: #1f5f3f; color: #fff; }
    .size-row { display: inline-block; min-width: 72px; padding: 10px; }
"""
    return body, script, style, HEADER


# B15 policy: long text with no headings or landmarks (P4 no_structure)
CLAUSES = [
    "We collect the details you give us when you order, such as your name and address.",
    "We use your address only to deliver orders and to send invoices you ask for.",
    "We keep order records for six years, as the law on accounts requires.",
    "We do not sell your details to anyone.",
    "Payment details are handled by our payment provider and never stored by us.",
    "You can ask for a copy of the details we hold about you at any time.",
    "You can ask us to correct details that are wrong.",
    "You can ask us to delete your account; order records stay for six years.",
    "We use cookies to keep you signed in and to remember your basket.",
    "We do not use cookies for advertising.",
    "We may email you about your orders; we email offers only if you agree.",
    "You can stop offer emails with the link at the end of each email.",
    "Our staff can see your details only when they need them to help you.",
    "We check who can see your details every three months.",
    "If we lose any of your details, we will tell you within three days.",
    "We store your details on servers in Pakistan.",
    "We send details abroad only to deliver an order you asked to send abroad.",
    "Children under thirteen may not open an account.",
    "We change this policy when the law or our service changes.",
    "We tell you about every change by email before it starts.",
]
SECTIONS = [
    "What we collect",
    "How we use it",
    "Your rights",
    "Cookies and email",
    "Security",
    "Changes",
]


def policy(bug):
    paras = []
    for i, clause in enumerate(CLAUSES * 2):
        if not bug and i % 7 == 0:
            paras.append(f"      <h2>{SECTIONS[(i // 7) % len(SECTIONS)]}</h2>")
        paras.append(f"      <p>{clause}</p>")
    text = "\n".join(paras)
    if bug:
        body = f"""  <div class="page">
    <div class="title">Privacy policy</div>
    <div>
{text}
    </div>
    <form id="form"><a href="#" id="accept">Accept the policy</a></form>
    <div id="result"></div>
  </div>
"""
        header = '  <div class="top"><span class="brand">SimShop</span></div>\n'
    else:
        body = f"""  <a class="skip" href="#form">Skip to accepting the policy</a>
  <main>
    <h1>Privacy policy</h1>
    <section>
{text}
    </section>
    <form id="form"><a href="#" id="accept">Accept the policy</a></form>
    <div id="result"></div>
  </main>
"""
        header = HEADER
    script = (
        SUBMIT.format()
        + """    document.getElementById('accept').addEventListener('click', (e) => {
      e.preventDefault();
      submit('api/policy', 'accepted', () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Policy accepted</h2>';
      });
    });
"""
    )
    style = """    .title { font-size: 1.6rem; font-weight: 700; margin: 16px 0; }
    .page, .top { max-width: 640px; margin: 0 auto; padding: 0 16px; }
    .skip { position: absolute; left: -999px; }
    .skip:focus { left: 8px; top: 8px; }
"""
    return body, script, style, header


# B16 filters: positive tabindex sends focus to the footer and back (P5 focus_order_illogical)
def filters(bug):
    t = (lambda n: f' tabindex="{n}"') if bug else (lambda n: "")
    body = f"""  <main>
    <h1>Kettles</h1>
    <form id="form" novalidate>
      <div class="row">
        <div class="field grow">
          <label for="min">Lowest price</label>
          <input type="text" id="min" inputmode="numeric"{t(1)}>
        </div>
        <div class="field grow">
          <label for="max">Highest price</label>
          <input type="text" id="max" inputmode="numeric"{t(3)}>
        </div>
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit"{t(4)}>Apply filters</button>
    </form>
    <div id="result"></div>
  </main>
  <footer><a href="index.html"{t(2)}>Help with filters</a></footer>
"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const min = Number(document.getElementById('min').value);
      const max = Number(document.getElementById('max').value);
      if (!min || !max || min > max) {
        document.getElementById('error').textContent = 'Enter a lowest and a highest price.';
        return;
      }
      submit('api/filters', min + '-' + max, () => {
        document.getElementById('result').innerHTML = '<h2>Filters applied</h2>';
      });
    });
"""
    )
    return (
        body,
        script,
        "    footer { max-width: 640px; margin: 24px auto; padding: 0 16px; }\n",
        HEADER,
    )


# B17 login: no visible focus (P5 focus_not_visible)
def login(bug):
    style = (
        "    *:focus { outline: none; }\n"
        if bug
        else "    *:focus { outline: 3px solid #1f5f3f; outline-offset: 2px; }\n"
    )
    body = """  <main>
    <h1>Log in</h1>
    <form id="form" novalidate>
      <div class="field">
        <label for="email">Email address</label>
        <input type="text" id="email" autocomplete="username">
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input type="password" id="password" autocomplete="current-password">
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Log in</button>
    </form>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      if (!email || !password) {
        document.getElementById('error').textContent = 'Enter your email address and password.';
        return;
      }
      submit('api/login', email, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Welcome back</h2>';
      });
    });
"""
    )
    return body, script, style, HEADER


# B20 invoice: fixed 1000 px layout, "Pay invoice" at the far right (P7 reflow_failure)
def invoice(bug):
    style = (
        "    .invoice { display: flex; width: 1000px; justify-content: space-between; }\n"
        if bug
        else "    .invoice { display: flex; flex-direction: column; gap: 8px; }\n"
    )
    body = """  <main>
    <h1>Invoice INV-2207</h1>
    <form id="form" class="invoice" novalidate>
      <dl>
        <dt>Amount due</dt><dd>$120.00</dd>
        <dt>Due by</dt><dd>30 November 2026</dd>
      </dl>
      <button type="submit">Pay invoice</button>
    </form>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      submit('api/invoice', 'INV-2207', () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Invoice paid</h2>';
      });
    });
"""
    )
    return body, script, style, HEADER


# B21 profile: a fixed cookie banner covers the lower 40% (P7 focus_obscured)
def profile(bug):
    if bug:
        banner = """    <div class="cookies">We use cookies to keep you signed in and to remember your basket.
      By using SimShop you agree to this.</div>
"""
        style = "    .cookies { position: fixed; left: 0; right: 0; bottom: 0; height: 70vh; background: #222; color: #fff; padding: 12px; }\n"
    else:
        banner = """    <div class="cookies">We use cookies to keep you signed in and to remember your basket.
      By using SimShop you agree to this.</div>
"""
        style = "    .cookies { background: #222; color: #fff; padding: 12px; margin-top: 16px; }\n"
    body = f"""  <main>
    <h1>Your profile</h1>
    <p>This name is shown on your reviews and on parcels.</p>
    <form id="form" novalidate>
      <div class="field">
        <label for="name">Display name</label>
        <input type="text" id="name" value="Sam Khan">
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Save changes</button>
    </form>
    <div id="result"></div>
  </main>
{banner}"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('name').value.trim();
      if (!name) {
        document.getElementById('error').textContent = 'Enter a display name.';
        return;
      }
      submit('api/profile', name, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Profile saved</h2>';
      });
    });
"""
    )
    return body, script, style, HEADER


# B22 notice: fixed-height box clips the deadline at 200% text (P7 text_clipped)
def notice(bug):
    box = "height: 72px; overflow: hidden;" if bug else "min-height: 72px;"
    style = f"    .notice {{ {box} border: 1px solid #888; padding: 8px; line-height: 1.5; }}\n"
    body = """  <main>
    <h1>Parking permit</h1>
    <div class="notice">Your parking permit for Canal Road ends soon.
      To keep parking there, renew it online.
      Renew by 15 December 2026, or the permit stops.</div>
    <form id="form" novalidate>
      <div class="field">
        <label for="date">Renew by date</label>
        <input type="text" id="date" placeholder="for example 1 January 2027">
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Request renewal</button>
    </form>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const date = document.getElementById('date').value.trim().toLowerCase();
      if (date !== '15 december 2026') {
        document.getElementById('error').textContent = 'Enter the renew-by date from the notice.';
        return;
      }
      submit('api/permit', date, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Renewal requested</h2>';
      });
    });
"""
    )
    return body, script, style, HEADER


# B23 redeem: the key instruction is the fourth sentence (P8 key_info_buried)
def redeem(bug):
    intro = (
        "<p>Gift cards can be used on anything in the shop. They do not expire. "
        "You can use one card per order. Use the code from your email, not the one on your receipt.</p>"
        if bug
        else "<p>Gift cards can be used on anything in the shop. They do not expire. "
        "You can use one card per order.</p>"
    )
    hint = (
        ""
        if bug
        else '\n        <p class="hint" id="hint">Use the code from your email, not the one on your receipt.</p>'
    )
    body = f"""  <main>
    <h1>Redeem a gift card</h1>
    {intro}
    <form id="form" novalidate>
      <div class="field">
        <label for="code">Gift card code</label>
        <input type="text" id="code">{hint}
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Redeem</button>
    </form>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const code = document.getElementById('code').value.trim().toUpperCase();
      if (code !== 'GIFT-7731') {
        document.getElementById('error').textContent = 'That code cannot be redeemed.';
        return;
      }
      submit('api/redeem', code, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Gift card added</h2>';
      });
    });
"""
    )
    return body, script, "", HEADER


# B24 trial: the call to action is below a carousel and three promotions (P8 cta_below_fold)
PROMOS = [
    ("Kettles for every kitchen", "From $25, with free delivery on orders over $50."),
    ("New: smart toasters", "Brown your bread the same way every morning."),
    ("Spring sale", "Up to 30% off cookware this week."),
]


def trial(bug):
    blocks = "\n".join(
        f'    <section class="promo"><h2>{h}</h2><p>{t}</p></section>' for h, t in PROMOS
    )
    cta = '    <form id="form"><button type="submit">Start free trial</button></form>\n'
    hero = """    <section class="hero"><h1>SimShop Plus</h1>
      <p>Free next-day delivery and early access to sales, free for 30 days.</p>
"""
    if bug:
        main = (
            hero
            + "    </section>\n"
            + '    <div class="carousel">Photos of SimShop Plus members</div>\n'
            + blocks
            + "\n"
            + cta
        )
    else:
        main = (
            hero
            + cta.replace("    ", "      ", 1)
            + "    </section>\n"
            + '    <div class="carousel">Photos of SimShop Plus members</div>\n'
            + blocks
            + "\n"
        )
    body = f"""  <main>
{main}    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      submit('api/trial', 'plus', () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Trial started</h2>';
      });
    });
"""
    )
    style = """    .carousel { height: 320px; background: #ddd; display: grid; place-items: center; margin: 16px 0; }
    .promo { min-height: 260px; border: 1px solid #ccc; padding: 16px; margin: 16px 0; }
"""
    return body, script, style, HEADER


# B25 pricing: headings that do not say what each section is (P8 headings_not_descriptive)
def pricing(bug):
    names = (
        ["Section 1", "More info", "Other"]
        if bug
        else ["Monthly plans", "Annual plans", "Cancel anytime"]
    )
    body = f"""  <main>
    <h1>SimShop Plus plans</h1>
    <section><h2>{names[0]}</h2>
      <p>Pay every month.</p>
      <button type="button" data-plan="monthly-single">Choose Single, $4 a month</button>
      <button type="button" data-plan="monthly-family">Choose Family, $7 a month</button>
    </section>
    <section><h2>{names[1]}</h2>
      <p>Pay once a year and get two months free.</p>
      <button type="button" data-plan="annual-single">Choose Single, $40 a year</button>
      <button type="button" data-plan="annual-family">Choose Family, $70 a year</button>
    </section>
    <section><h2>{names[2]}</h2>
      <p>You can end any plan from your account page.</p>
    </section>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    document.querySelectorAll('[data-plan]').forEach((b) => b.addEventListener('click', () => {
      const plan = b.dataset.plan;
      submit('api/plan', plan, () => {
        document.querySelectorAll('section').forEach((s) => { s.hidden = true; });
        document.getElementById('result').innerHTML = plan === 'annual-family'
          ? '<h2>Annual Family plan chosen</h2>'
          : '<h2>Plan chosen</h2><p>You chose ' + b.textContent.replace('Choose ', '') + '.</p>';
      });
    }));
"""
    )
    return body, script, "", HEADER


for stem, title, make in [
    ("feedback", "Feedback", feedback),
    ("size", "Running trainers", size),
    ("policy", "Privacy policy", policy),
    ("filters", "Kettles", filters),
    ("login", "Log in", login),
    ("invoice", "Invoice", invoice),
    ("profile", "Your profile", profile),
    ("notice", "Parking permit", notice),
    ("redeem", "Gift cards", redeem),
    ("trial", "SimShop Plus", trial),
    ("pricing", "SimShop Plus plans", pricing),
]:
    pair(stem, title, make)
print("ok")
