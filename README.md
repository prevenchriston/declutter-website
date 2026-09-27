# Declutter Junk Removal — website

Static site for thedeclutterteam.com. Hosted on Vercel; every push to `main` redeploys.

## Update the site
1. Edit content (phone, services, towns, FAQs, reviews) at the top of `build.py`.
2. Add photos to `photos/` — see `photos/README.md` for file names.
3. Rebuild: `pip3 install Pillow` (once), then `python3 build.py`.
4. Commit and push — Vercel publishes the new `site/` folder automatically.

## Quote form
Submissions are emailed to infodeclutterteam@gmail.com via FormSubmit (formsubmit.co).
The very first submission triggers a one-time activation email — click the link in it.
