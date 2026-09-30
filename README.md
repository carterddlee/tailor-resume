# Tailor Resume (Claude Code)

## Setup
1. `pip3 install -r requirements.txt`
2. Put your base resume in `base/`, in any of these formats. Keep exactly one file there.
   - Documents: `.docx` `.pdf` `.doc` `.rtf` `.odt` `.pages`
   - Text/markup: `.md` `.txt` `.tex` `.html` `.json` `.yaml` (and similar)

   Include MORE bullets than fit on a page. The agent picks and rewords them; it never invents.
3. Check it's detected: `python3 tailor.py prepare`

Each tailored resume comes back in the **same file type and formatting** as your base:
- Text/markup files are edited as a copy, so the markup stays the same.
- Documents are edited paragraph by paragraph on a copy of your file, so fonts, spacing, bullets and layout carry over.
- `.pdf` is converted to Word for editing and back to PDF (needs Microsoft Word or LibreOffice). If you have the original `.docx`, use that; it keeps the formatting more exactly.
- `.doc`/`.rtf` round-trip through Microsoft Word (macOS `textutil` if Word isn't installed). `.odt` uses `textutil`.
- `.pages` is driven through the Pages app. If Pages shows a dialog it can time out; export to `.docx` instead.
- `.json` uses the schema in `build_resume.py` and also gets a rendered `.docx`. To preview your base: `python3 build_resume.py base/resume.json`

## Use
From this folder, start Claude Code (`claude`) and run:

    /tailor https://jobs.ashbyhq.com/... https://boards.greenhouse.io/... jobs/sap.txt

Each input gets its own subagent, all running in parallel. Results land in:

    output/<company-role>/carter_lee_<company>_resume.<same ext as base>   # e.g. carter_lee_anthropic_resume.pdf
    output/<company-role>/job.json        # company + role (used for the file name)
    output/<company-role>/notes.md        # changes + skill gaps
    output/<company-role>/edits.json      # (document formats) the edits that were applied

To rebuild after hand-editing an `edits.json`: `python3 tailor.py build <company-role>`

## If a link fails
LinkedIn/Indeed often block fetching. Paste the job description into `jobs/<name>.txt` and pass that path instead.
