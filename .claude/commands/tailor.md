---
description: Tailor the base resume to multiple job links in parallel
argument-hint: <job-url-or-txt-path> [more ...]
---
Job inputs: $ARGUMENTS

1. Split the inputs on whitespace. Each one is a job URL or a path to a .txt job description.
2. For EACH input, launch a separate resume-tailor subagent. Launch them ALL in parallel in a single step, not one after another.
3. When all subagents finish, run:
   python build_resume.py
4. Honesty check: for each output/*/resume.json, compare every bullet and the summary against base/resume.json. Flag any claim (metric, tool, responsibility) that isn't supported by the base. Don't fix silently; list them.
5. Reply with a table: company | role | docx path | top gaps | flags. Then list any FAILED inputs and tell me to paste those job descriptions into jobs/<name>.txt and rerun with the file path.
