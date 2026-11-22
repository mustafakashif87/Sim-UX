# ruff: noqa: E501  (HTML and CSS string lines)
"""Generate the extension personas' seeded page pairs: P4, P5, P7, P8 (B13-B17,
B20-B25), P6 (B18, B19), P10 (B28, B29), P9 (B26, B27), P11 (B30, B31),
P12 (B32, B33), P13 (B34, B35) and P14 (B36).

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


# B18 cart: a 16 px "Remove item" 4 px from the 16 px "+", removal at once (P6)
def cart(bug):
    if bug:
        style = """    .qty button { min-width: 16px; min-height: 16px; width: 16px; height: 16px; padding: 0; font-size: 12px; }
    .qty { display: flex; gap: 4px; align-items: center; }
"""
        undo = ""
    else:
        style = """    .qty button { min-width: 44px; min-height: 44px; }
    .qty { display: flex; gap: 24px; align-items: center; }
"""
        undo = """        document.getElementById('undo').innerHTML =
          '<p role="status">Kettle removed. <button type="button" id="undo-btn" class="secondary">Undo</button></p>';
        document.getElementById('undo-btn').addEventListener('click', () => {
          removed = false; render(); document.getElementById('undo').innerHTML = '';
        });
"""
    body = """  <main>
    <h1>Your basket</h1>
    <div id="line">
      <p>Stainless steel kettle, $39.00 each</p>
      <div class="qty">
        <button type="button" id="minus" aria-label="Decrease quantity">-</button>
        <span id="count">1</span>
        <button type="button" id="plus" aria-label="Increase quantity">+</button>
        <button type="button" id="remove" aria-label="Remove item">x</button>
      </div>
    </div>
    <div id="undo"></div>
    <form id="form"><button type="submit">Go to checkout</button></form>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + f"""    let count = 1, removed = false;
    function render() {{
      document.getElementById('line').hidden = removed;
      document.getElementById('count').textContent = count;
    }}
    document.getElementById('plus').addEventListener('click', () => {{ count += 1; render(); }});
    document.getElementById('minus').addEventListener('click', () => {{ count = Math.max(1, count - 1); render(); }});
    document.getElementById('remove').addEventListener('click', async () => {{
      await fetch('api/cart/remove', {{ method: 'POST', body: 'kettle' }});
      removed = true; render();
{undo}    }});
    document.getElementById('form').addEventListener('submit', (e) => {{
      e.preventDefault();
      if (removed || count !== 2) {{
        document.getElementById('undo').innerHTML = '<p role="alert">Your basket needs 2 kettles for this task.</p>';
        return;
      }}
      submit('api/checkout', 'kettle x' + count, () => {{
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Ready to pay</h2>';
      }});
    }});
"""
    )
    return body, script, style, HEADER


# B19 shipping: 18 px radio rows that touch, and no summary before paying (P6)
def shipping(bug):
    if bug:
        style = """    .opt { display: block; height: 18px; line-height: 18px; margin: 0; font-size: 14px; }
    .opt input { width: 14px; height: 14px; margin: 2px 4px 0 0; }
"""
        summary = ""
    else:
        style = """    .opt { display: block; min-height: 48px; padding: 12px 0; margin: 4px 0; }
    .opt input { width: 24px; height: 24px; }
"""
        summary = """        <p role="status" id="summary"></p>
"""
    body = f"""  <main>
    <h1>Delivery</h1>
    <form id="form" novalidate>
      <fieldset class="field">
        <legend>Delivery speed</legend>
        <label class="opt"><input type="radio" name="speed" value="standard"> Standard (free)</label>
        <label class="opt"><input type="radio" name="speed" value="express"> Express ($9.99)</label>
      </fieldset>
{summary}      <p id="error" class="error" role="alert"></p>
      <button type="submit">Pay now</button>
    </form>
    <div id="result"></div>
  </main>
"""
    summary_js = (
        ""
        if bug
        else """    document.querySelectorAll('input[name=speed]').forEach((r) => r.addEventListener('change', () => {
      document.getElementById('summary').textContent = 'You chose ' + r.parentElement.textContent.trim() + '.';
    }));
"""
    )
    script = (
        SUBMIT.format()
        + summary_js
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const speed = document.querySelector('input[name=speed]:checked');
      if (!speed) {
        document.getElementById('error').textContent = 'Choose a delivery speed.';
        return;
      }
      submit('api/shipping', speed.value, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = speed.value === 'standard'
          ? '<h2>Paid with free delivery</h2>' : '<h2>Paid with express delivery</h2>';
      });
    });
"""
    )
    return body, script, style, HEADER


# B28 payment: "Pay now" stays enabled and silent while the payment is sent (P10)
def payment(bug):
    if bug:
        start = ""
    else:
        start = """      document.getElementById('pay').disabled = true;
      document.getElementById('busy').textContent = 'Processing payment…';
"""
    body = """  <main>
    <h1>Pay for your order</h1>
    <p>Total: $44.00, paid with your saved card ending 4242.</p>
    <form id="form"><button type="submit" id="pay">Pay now</button></form>
    <p id="busy" role="status"></p>
    <div id="result"></div>
  </main>
"""
    script = f"""    document.getElementById('form').addEventListener('submit', async (e) => {{
      e.preventDefault();
{start}      await fetch('api/payment', {{ method: 'POST', body: 'order-5512' }});
      document.getElementById('busy').textContent = '';
      document.getElementById('form').hidden = true;
      document.getElementById('result').innerHTML = '<h2>Payment received</h2>';
    }});
"""
    return body, script, "", HEADER


# B29 upload: a failed submission leaves the page as it was (P10)
def upload(bug):
    if bug:
        failed = "        // the error is ignored\n"
    else:
        failed = """        document.getElementById('error').innerHTML =
          "Couldn't send. Check your connection and try again.";
        send.disabled = false;
        send.textContent = 'Try again';
"""
    body = """  <main>
    <h1>Send a meter reading</h1>
    <form id="form" novalidate>
      <div class="field">
        <label for="reading">Meter reading</label>
        <input type="text" id="reading" inputmode="numeric">
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit" id="send">Send reading</button>
    </form>
    <div id="result"></div>
  </main>
"""
    script = f"""    const send = document.getElementById('send');
    document.getElementById('form').addEventListener('submit', async (e) => {{
      e.preventDefault();
      const reading = document.getElementById('reading').value.trim();
      if (!/^\\d+$/.test(reading)) {{
        document.getElementById('error').textContent = 'Enter the numbers on your meter.';
        return;
      }}
      document.getElementById('error').textContent = '';
      send.disabled = true;
      try {{
        const r = await fetch('api/reading', {{ method: 'POST', body: reading }});
        if (!r.ok) throw new Error(r.status);
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Reading sent</h2>';
      }} catch (err) {{
{failed}      }}
      if (send.textContent !== 'Try again') send.disabled = false;
    }});
"""
    return body, script, "", HEADER


# B26 application: a 10-minute inactivity timeout with no warning, answers lost (P9)
def application(bug):
    if bug:
        warn, ended, restore = "", "All your answers have been cleared.", ""
    else:
        warn = """      warnTimer = setTimeout(() => {
        document.getElementById('warn').innerHTML =
          '<div role="alertdialog" aria-label="Session ending"><p>Your session will end in 2 minutes.</p>' +
          '<button type="button" id="stay">Stay signed in</button></div>';
        document.getElementById('stay').addEventListener('click', () => {
          document.getElementById('warn').innerHTML = ''; arm();
        });
      }, 8 * 60 * 1000);
"""
        ended = "Your answers are saved."
        restore = """      for (const id of ['name', 'nid']) {
        document.getElementById(id).value = sessionStorage.getItem('app-' + id) || '';
      }
"""
    save = "" if bug else "        sessionStorage.setItem('app-' + e.target.id, e.target.value);\n"
    body = """  <main>
    <h1>Apply for a parking permit</h1>
    <form id="form" novalidate>
      <div class="field">
        <label for="name">Full name</label>
        <input type="text" id="name">
      </div>
      <div class="field">
        <label for="nid">National ID number</label>
        <input type="text" id="nid">
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Submit application</button>
    </form>
    <div id="warn"></div>
    <div id="ended"></div>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + f"""    let timer, warnTimer;
    function arm() {{
      clearTimeout(timer); clearTimeout(warnTimer);
{warn}      timer = setTimeout(endSession, 10 * 60 * 1000);
    }}
    function endSession() {{
      document.getElementById('warn').innerHTML = '';
      document.getElementById('form').hidden = true;
      document.getElementById('ended').innerHTML =
        '<div role="alert"><h2>Your session has ended</h2><p>{ended}</p></div>' +
        '<button type="button" id="again">Sign in again</button>';
      document.getElementById('again').addEventListener('click', () => {{
        document.getElementById('ended').innerHTML = '';
        document.getElementById('form').reset();
{restore}        document.getElementById('form').hidden = false;
        arm();
      }});
    }}
    document.getElementById('form').addEventListener('input', (e) => {{
{save}        arm();
    }});
    arm();
    document.getElementById('form').addEventListener('submit', (e) => {{
      e.preventDefault();
      const name = document.getElementById('name').value.trim();
      const nid = document.getElementById('nid').value.trim();
      if (!name || !nid) {{
        document.getElementById('error').textContent = 'Enter your full name and national ID number.';
        return;
      }}
      submit('api/application', name + ' ' + nid, () => {{
        clearTimeout(timer); clearTimeout(warnTimer);
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Application sent</h2>';
      }});
    }});
"""
    )
    return body, script, "", HEADER


# B27 survey: answers kept only in memory; a reload starts again (P9)
QUESTIONS = [
    ("How often do you shop with us?", ["Every week", "Every month"]),
    ("How do you usually pay?", ["Card", "Cash on delivery"]),
    ("How was your last delivery?", ["Good", "Poor"]),
    ("Would you recommend SimShop?", ["Yes", "No"]),
]


def survey(bug):
    screens = []
    for i, (q, opts) in enumerate(QUESTIONS, 1):
        radios = "\n".join(
            f'          <label class="opt"><input type="radio" name="q{i}" value="{o}"> {o}</label>'
            for o in opts
        )
        last = i == len(QUESTIONS)
        screens.append(f"""      <fieldset class="step field" id="s{i}" hidden>
        <legend>Question {i} of 4: {q}</legend>
{radios}
        <button type="button" class="next">{"Finish" if last else "Next"}</button>
      </fieldset>""")
    body = f"""  <main>
    <h1>Customer survey</h1>
    <form id="form" novalidate>
{chr(10).join(screens)}
      <p id="error" class="error" role="alert"></p>
    </form>
    <div id="result"></div>
  </main>
"""
    if bug:
        load = "    let step = 1; const answers = {};\n"
        keep = ""
    else:
        load = """    let step = Number(sessionStorage.getItem('survey-step') || 1);
    const answers = JSON.parse(sessionStorage.getItem('survey-answers') || '{}');
"""
        keep = """      sessionStorage.setItem('survey-step', step);
      sessionStorage.setItem('survey-answers', JSON.stringify(answers));
"""
    script = (
        SUBMIT.format()
        + load
        + f"""    function show() {{
      document.querySelectorAll('.step').forEach((s) => {{ s.hidden = s.id !== 's' + step; }});
    }}
    document.querySelectorAll('.next').forEach((b) => b.addEventListener('click', () => {{
      const chosen = document.querySelector(`input[name=q${{step}}]:checked`);
      if (!chosen) {{
        document.getElementById('error').textContent = 'Choose an answer.';
        return;
      }}
      document.getElementById('error').textContent = '';
      answers['q' + step] = chosen.value;
      if (step < 4) {{
        step += 1;
{keep}        show();
        return;
      }}
      submit('api/survey', JSON.stringify(answers), () => {{
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Thanks for your answers</h2>';
      }});
    }}));
    show();
"""
    )
    return body, script, "    .opt { display: block; padding: 8px 0; }\n", HEADER


# B30 claim: the policy-number format is never explained, and no help (P11)
def claim(bug):
    help_link = (
        ""
        if bug
        else """
        <p><a href="#policy-help" id="help-link">Where do I find my policy number?</a></p>
        <p id="policy-help" class="hint" hidden>Your policy number is on your policy letter. It starts with POL-, for example POL-1234567.</p>"""
    )
    body = f"""  <main>
    <h1>Make an insurance claim</h1>
    <form id="form" novalidate>
      <div class="field">
        <label for="policy">Policy number</label>
        <input type="text" id="policy">{help_link}
      </div>
      <div class="field">
        <label for="what">What happened</label>
        <textarea id="what"></textarea>
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Make a claim</button>
    </form>
    <div id="result"></div>
  </main>
"""
    show_help = (
        ""
        if bug
        else """    document.getElementById('help-link').addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('policy-help').hidden = false;
    });
"""
    )
    script = (
        SUBMIT.format()
        + show_help
        + """    document.getElementById('form').addEventListener('submit', (e) => {
      e.preventDefault();
      const policy = document.getElementById('policy').value.trim().toUpperCase();
      const what = document.getElementById('what').value.trim();
      if (!/^POL-\\d{7}$/.test(policy) || !what) {
        document.getElementById('error').textContent = 'That policy number is not valid.';
        return;
      }
      submit('api/claim', policy, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Claim received</h2>';
      });
    });
"""
    )
    return body, script, "", HEADER


# B31 support: "Contact us" moves between screens and then disappears (P11)
def support(bug):
    top = '<p class="help"><a href="#contact">Contact us</a></p>'
    where = (
        {1: ("top", top), 2: ("bottom", top), 3: ("none", "")}
        if bug
        else {1: ("top", top), 2: ("top", top), 3: ("top", top)}
    )

    def place(n, inner):
        pos, link = where[n]
        before = link if pos == "top" else ""
        after = link if pos == "bottom" else ""
        return f"""      <section class="step" id="s{n}" hidden>
        {before}
{inner}
        {after}
      </section>"""

    s1 = """        <h2>Step 1 of 3: Your parcel</h2>
        <div class="field">
          <label for="track">Tracking number</label>
          <input type="text" id="track">
        </div>
        <button type="button" data-next="2">Next</button>"""
    s2 = """        <h2>Step 2 of 3: New delivery day</h2>
        <label class="opt"><input type="radio" name="day" value="Friday"> Friday</label>
        <label class="opt"><input type="radio" name="day" value="Saturday"> Saturday</label>
        <button type="button" data-next="3">Next</button>"""
    s3 = """        <h2>Step 3 of 3: Check and confirm</h2>
        <p id="check"></p>
        <button type="button" id="confirm">Confirm change</button>"""
    body = f"""  <main>
    <h1>Change a delivery</h1>
    <form id="form" novalidate>
{place(1, s1)}
{place(2, s2)}
{place(3, s3)}
      <p id="error" class="error" role="alert"></p>
    </form>
    <div id="contact" hidden><p>Call 0800 123 456, 9am to 5pm.</p></div>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    const show = (n) => document.querySelectorAll('.step').forEach((s) => { s.hidden = s.id !== 's' + n; });
    document.querySelectorAll('a[href="#contact"]').forEach((a) => a.addEventListener('click', (e) => {
      e.preventDefault(); document.getElementById('contact').hidden = false;
    }));
    document.querySelectorAll('[data-next]').forEach((b) => b.addEventListener('click', () => {
      const n = Number(b.dataset.next);
      const error = document.getElementById('error');
      if (n === 2 && !/^SP-\\d{5}$/.test(document.getElementById('track').value.trim())) {
        error.textContent = 'Enter a tracking number like SP-12345.'; return;
      }
      const day = document.querySelector('input[name=day]:checked');
      if (n === 3 && !day) { error.textContent = 'Choose a day.'; return; }
      error.textContent = '';
      if (n === 3) document.getElementById('check').textContent = 'New delivery day: ' + day.value + '.';
      show(n);
    }));
    document.getElementById('confirm').addEventListener('click', () => {
      const day = document.querySelector('input[name=day]:checked').value;
      submit('api/delivery', day, () => {
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Delivery changed</h2>';
      });
    });
    show(1);
"""
    )
    return body, script, "    .opt { display: block; padding: 8px 0; }\n", HEADER


# B32 settings: the save button is renamed on each screen, and on the last
# one "Delete my settings" sits where Save was (P12)
SETTINGS = [
    ("Email", "Send me email receipts"),
    ("Privacy", "Hide my reviews from other shoppers"),
    ("Offers", "Tell me about offers by email"),
]


def settings(bug):
    names = ["Save", "Apply", "Update"] if bug else ["Save", "Save", "Save"]
    screens = []
    for i, (title, option) in enumerate(SETTINGS, 1):
        save = f'<button type="button" class="save">{names[i - 1]}</button>'
        if i < 3:
            left = '<button type="button" class="secondary cancel">Cancel</button>'
            right = save
        else:
            delete = (
                '<button type="button" class="secondary" id="delete">Delete my settings</button>'
            )
            left, right = (save, delete) if bug else (delete, save)
        screens.append(f"""      <section class="step" id="s{i}" hidden>
        <h2>{title} settings ({i} of 3)</h2>
        <label class="opt"><input type="checkbox" id="c{i}"> {option}</label>
        <div class="actions">{left}{right}</div>
      </section>""")
    body = f"""  <main>
    <h1>Account settings</h1>
{chr(10).join(screens)}
    <p id="error" class="error" role="alert"></p>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + """    let step = 1;
    const show = () => document.querySelectorAll('.step').forEach((s) => { s.hidden = s.id !== 's' + step; });
    document.querySelectorAll('.save').forEach((b) => b.addEventListener('click', () => {
      if (!document.getElementById('c' + step).checked) {
        document.getElementById('error').textContent = 'Tick the option first.'; return;
      }
      document.getElementById('error').textContent = '';
      if (step < 3) {
        fetch('api/settings', { method: 'POST', body: 'section ' + step });  // autosave, not awaited
        step += 1; show(); return;
      }
      submit('api/settings', 'section 3', () => {
        document.querySelectorAll('.step').forEach((s) => { s.hidden = true; });
        document.getElementById('result').innerHTML = '<h2>All settings saved</h2>';
      });
    }));
    document.getElementById('delete').addEventListener('click', () => {
      submit('api/settings/delete', 'all', () => {
        document.querySelectorAll('.step').forEach((s) => { s.hidden = true; });
        document.getElementById('result').innerHTML = '<h2>Settings deleted</h2>';
      });
    });
    show();
"""
    )
    style = """    .actions { display: flex; justify-content: space-between; margin-top: 16px; }
    .opt { display: block; padding: 8px 0; }
"""
    return body, script, style, HEADER


# B33 store: the shop navigation changes order between screens (P12)
def store(bug):
    orders = (
        [
            ["Home", "Kettles", "Toasters", "Basket"],
            ["Basket", "Toasters", "Home", "Kettles"],
            ["Toasters", "Home", "Basket", "Kettles"],
        ]
        if bug
        else [["Home", "Kettles", "Toasters", "Basket"]] * 3
    )
    content = {
        "Home": "<h2>Welcome to SimShop</h2><p>Kitchen goods delivered to your door.</p>",
        "Kettles": "<h2>Kettles</h2><p>Stainless steel kettle, $39.00</p>",
        "Toasters": "<h2>Toasters</h2><p>Two-slice toaster, $29.00, in your basket.</p>",
        "Basket": '<h2>Your basket</h2><p>Two-slice toaster, $29.00</p><button type="button" id="checkout">Check out</button>',
    }
    body = """  <main>
    <nav aria-label="Shop" id="shopnav"></nav>
    <div id="view"></div>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + f"""    const orders = {orders};
    const content = {content!r};
    let visits = 0;
    function open(name) {{
      const order = orders[Math.min(visits, orders.length - 1)];
      visits += 1;
      document.getElementById('shopnav').innerHTML =
        order.map((n) => `<a href="#" data-go="${{n}}">${{n}}</a>`).join(' · ');
      document.querySelectorAll('[data-go]').forEach((a) => a.addEventListener('click', (e) => {{
        e.preventDefault(); open(a.dataset.go);
      }}));
      document.getElementById('view').innerHTML = content[name];
      const checkout = document.getElementById('checkout');
      if (checkout) checkout.addEventListener('click', () => submit('api/store', 'toaster', () => {{
        document.getElementById('view').innerHTML = '';
        document.getElementById('result').innerHTML = '<h2>Checkout started</h2>';
      }}));
    }}
    open('Home');
"""
    )
    return body, script, "", HEADER


# B34 quickadd: fields outside a form, so Enter does nothing (P13)
def quickadd(bug):
    fields = """        <div class="field">
          <label for="item">Item name</label>
          <input type="text" id="item">
        </div>
        <div class="field">
          <label for="qty">Quantity</label>
          <input type="text" id="qty" inputmode="numeric">
        </div>
        <p id="error" class="error" role="alert"></p>
        <button type="{t}" id="add">Add item</button>"""
    if bug:
        box = f'    <div id="form">\n{fields.format(t="button")}\n    </div>'
        hook = "document.getElementById('add').addEventListener('click', add);"
    else:
        box = f'    <form id="form" novalidate>\n{fields.format(t="submit")}\n    </form>'
        hook = "document.getElementById('form').addEventListener('submit', (e) => { e.preventDefault(); add(); });"
    body = f"""  <main>
    <h1>Stock list</h1>
{box}
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + f"""    function add() {{
      const item = document.getElementById('item').value.trim();
      const qty = Number(document.getElementById('qty').value);
      if (!item || !qty) {{
        document.getElementById('error').textContent = 'Enter an item and a quantity.'; return;
      }}
      submit('api/stock', item + ' x' + qty, () => {{
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Item added</h2>';
      }});
    }}
    {hook}
"""
    )
    return body, script, "", HEADER


# B35 bulk: archiving 10 tickets one by one, each with a confirmation (P13)
def bulk(bug):
    rows = []
    for i in range(1, 11):
        action = (
            f'<button type="button" class="archive" data-id="{i}">Archive ticket {i}</button>'
            if bug
            else f'<label><input type="checkbox" class="pick" value="{i}"> Select ticket {i}</label>'
        )
        rows.append(f'      <li id="t{i}">Ticket {i}: delivery question {action}</li>')
    select_all = (
        ""
        if bug
        else """    <label><input type="checkbox" id="all"> Select all</label>
    <button type="button" id="archive-selected">Archive selected</button>
"""
    )
    body = f"""  <main>
    <h1>Open tickets</h1>
{select_all}    <ul id="list">
{chr(10).join(rows)}
    </ul>
    <dialog id="confirm"><p>Archive these tickets?</p>
      <button type="button" id="yes">Yes, archive</button>
      <button type="button" class="secondary" id="no">Cancel</button></dialog>
    <div id="result"></div>
  </main>
"""
    if bug:
        logic = """    let pending = [];
    document.querySelectorAll('.archive').forEach((b) => b.addEventListener('click', () => {
      pending = [b.dataset.id]; dialog.showModal();
    }));
"""
    else:
        logic = """    let pending = [];
    document.getElementById('all').addEventListener('change', (e) => {
      document.querySelectorAll('.pick').forEach((c) => { c.checked = e.target.checked; });
    });
    document.getElementById('archive-selected').addEventListener('click', () => {
      pending = [...document.querySelectorAll('.pick:checked')].map((c) => c.value);
      if (pending.length) dialog.showModal();
    });
"""
    script = f"""    const dialog = document.getElementById('confirm');
    const archived = new Set();
{logic}    document.getElementById('no').addEventListener('click', () => dialog.close());
    document.getElementById('yes').addEventListener('click', () => {{
      dialog.close();
      if (!pending.length) return;
      fetch('api/tickets', {{ method: 'POST', body: pending.join(',') }});  // not awaited
      pending.forEach((id) => {{ archived.add(id); document.getElementById('t' + id).remove(); }});
      pending = [];
      if (archived.size === 10) document.getElementById('result').innerHTML = '<h2>All tickets archived</h2>';
    }});
"""
    return body, script, "", HEADER


# B36 appointment: a 60 s limit; "Need more time?" has a 20 px button and goes
# after 10 s (P14). The clean page allows 20 minutes and its prompt stays.
def appointment(bug):
    if bug:
        limit, prompt_at, prompt_for = 60, 40, 10
        style = "    #more { min-width: 20px; min-height: 20px; height: 20px; padding: 0 4px; font-size: 11px; }\n"
    else:
        limit, prompt_at, prompt_for = 20 * 60, 18 * 60, 0
        style = "    #more { min-height: 48px; }\n"
    style += "    #prompt { position: fixed; top: 16px; right: 16px; background: #fff; }\n"
    hide = (
        f"      hideTimer = setTimeout(() => {{ document.getElementById('prompt').innerHTML = ''; }}, {prompt_for * 1000});\n"
        if prompt_for
        else ""
    )
    body = """  <main>
    <h1>Book a branch appointment</h1>
    <form id="form" novalidate>
      <div class="field">
        <label for="name">Full name</label>
        <input type="text" id="name">
      </div>
      <div class="field">
        <label for="phone">Phone number</label>
        <input type="text" id="phone">
      </div>
      <div class="field">
        <label for="date">Preferred date</label>
        <input type="text" id="date" placeholder="for example 2 December">
      </div>
      <p id="error" class="error" role="alert"></p>
      <button type="submit">Book appointment</button>
    </form>
    <div id="prompt"></div>
    <div id="ended"></div>
    <div id="result"></div>
  </main>
"""
    script = (
        SUBMIT.format()
        + f"""    let timer, promptTimer, hideTimer;
    function arm() {{
      clearTimeout(timer); clearTimeout(promptTimer); clearTimeout(hideTimer);
      promptTimer = setTimeout(() => {{
        document.getElementById('prompt').innerHTML =
          '<div role="alertdialog" aria-label="Need more time?"><p>Need more time?</p>' +
          '<button type="button" id="more">Yes, more time</button></div>';
        document.getElementById('more').addEventListener('click', () => {{
          document.getElementById('prompt').innerHTML = ''; arm();
        }});
{hide}      }}, {prompt_at * 1000});
      timer = setTimeout(() => {{
        document.getElementById('prompt').innerHTML = '';
        document.getElementById('form').reset();
        document.getElementById('ended').innerHTML =
          '<p role="alert">Your session has ended. Please start again.</p>';
        arm();
      }}, {limit * 1000});
    }}
    arm();
    document.getElementById('form').addEventListener('submit', (e) => {{
      e.preventDefault();
      const ok = ['name', 'phone', 'date'].every((id) => document.getElementById(id).value.trim());
      if (!ok) {{ document.getElementById('error').textContent = 'Fill in every field.'; return; }}
      submit('api/appointment', document.getElementById('date').value, () => {{
        clearTimeout(timer); clearTimeout(promptTimer); clearTimeout(hideTimer);
        document.getElementById('form').hidden = true;
        document.getElementById('result').innerHTML = '<h2>Appointment booked</h2>';
      }});
    }});
"""
    )
    return body, script, style, HEADER


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
    ("cart", "Your basket", cart),
    ("shipping", "Delivery", shipping),
    ("payment", "Payment", payment),
    ("upload", "Meter reading", upload),
    ("application", "Parking permit application", application),
    ("survey", "Customer survey", survey),
    ("claim", "Insurance claim", claim),
    ("support", "Change a delivery", support),
    ("settings", "Account settings", settings),
    ("store", "Shop", store),
    ("quickadd", "Stock list", quickadd),
    ("bulk", "Open tickets", bulk),
    ("appointment", "Book an appointment", appointment),
]:
    pair(stem, title, make)
print("ok")
