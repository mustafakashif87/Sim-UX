# test-app

Seeded-bug test pages, each in a buggy (`-a`) and a clean (`-b`) version, plus
the ground-truth file naming every bug: [`SEEDED_BUGS.md`](SEEDED_BUGS.md).

Owner: Person A. Spec: The three personas, Evaluation protocol.

```bash
python -m http.server 8000 -d test-app   # browse at http://localhost:8000/
python test-app/check_seeds.py           # every bug present on -a, absent on -b
```

`check_seeds.py` needs the browser extra (`pip install -e ".[browser]"`). CI's
`seeds` job runs it and fails on any mismatch with `SEEDED_BUGS.md`.
