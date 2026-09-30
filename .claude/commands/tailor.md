---
description: Tailor the base resume to multiple job links in parallel
argument-hint: <job-url-or-txt-path> [more ...]
---
Job inputs: $ARGUMENTS

1. Run `python3 tailor.py prepare`. It finds the base resume in base/ (any file type) and writes base/.work/info.json (plus base/.work/content.json for binary formats). If it fails, show me the error and stop.
2. Split the inputs on whitespace. Each one is a job URL or a path to a .txt job description.
3. For EACH input, launch a separate resume-tailor subagent. Launch them ALL in parallel in a single step, not one after another.
4. When all subagents finish, run:
   python3 tailor.py build
   It writes output/<slug>/carter_lee_<company>_resume.<ext>, the same file type and formatting as the base resume.
5. Honesty check: for each output folder, compare the tailored text against the base resume (base/.work/content.json for binary formats, where the new text is in edits.json under "replace"; otherwise compare the tailored resume file against the base file). Flag any claim (metric, tool, responsibility) that isn't supported by the base. Don't fix silently; list them.
6. Reply with a table: company | role | resume path | top gaps | flags. Then list any FAILED inputs (from subagents or the build) and tell me to paste those job descriptions into jobs/<name>.txt and rerun with the file path.
