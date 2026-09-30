# Resume Tailor (Claude Code)

## Setup
1. `pip3 install reportlab playwright && python3 -m playwright install chromium` (fonts/ holds Carlito, the font base/Resume.pdf uses)
2. Fill in `base/resume.json` with your real resume. Include MORE bullets than fit on a page; the agent picks and rewords, it never invents.
3. Test the renderer: `python3 build_resume.py base/resume.json` (creates base/base-resume.pdf). It should look identical to base/Resume.pdf.

## Use
From this folder, start Claude Code (`claude`) and run:

    /tailor https://jobs.ashbyhq.com/... https://boards.greenhouse.io/... jobs/sap.txt

Each input gets its own subagent, all running in parallel. Results land in:

    output/<company-role>/resume.json
    output/<company-role>/notes.md        # changes + skill gaps
    output/<company-role>/<company-role>-resume.pdf

## If a link fails
`/tailor` first runs `fetch_job.py` on every URL, which saves the posting to `jobs/<slug>.txt` (via the job board's API, or headless Chrome for other sites). You can also run it yourself: `python3 fetch_job.py <url>`. LinkedIn/Indeed may still block it or require a login; if so, paste the job description into `jobs/<name>.txt` and pass that path instead.
