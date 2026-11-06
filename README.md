# optic5

Website for Optic5, Austin, TX: https://www.optic5.com

## Editing

Page content lives in `src/pages/`. Shared parts (header, contact form, footer, SEO tags and structured data) live in `tools/build.py`.

After any change, rebuild and check:

```bash
python tools/build.py
python tools/check.py
```

Commit the generated files too. Every push to `main` uploads the site to cPanel over FTPS.
