# Resume Tailor (Claude Code)

## Setup
1. `pip install python-docx`
2. Fill in `base/resume.json` with your real resume. Include MORE bullets than fit on a page; the agent picks and rewords, it never invents.
3. Test the renderer: `python build_resume.py base/resume.json` (creates base/base-resume.docx). Adjust styling in build_resume.py until it looks right.

## Use
From this folder, start Claude Code (`claude`) and run:

    /tailor https://jobs.ashbyhq.com/... https://boards.greenhouse.io/... jobs/sap.txt

Each input gets its own subagent, all running in parallel. Results land in:

    output/<company-role>/resume.json
    output/<company-role>/notes.md        # changes + skill gaps
    output/<company-role>/<company-role>-resume.docx

## If a link fails
LinkedIn/Indeed often block fetching. Paste the job description into `jobs/<name>.txt` and pass that path instead.
