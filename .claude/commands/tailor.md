---
description: Tailor the base resume to multiple job links in parallel
argument-hint: <job-url-or-txt-path> [more ...]
---
Job inputs: $ARGUMENTS

1. Split the inputs on whitespace (strip trailing commas). Each one is a job URL or a path to a .txt job description.
2. For every URL, first run (all URLs in one command):
   python3 fetch_job.py <url> [<url> ...]
   It saves each posting to jobs/<slug>.txt, using the job board's API or headless Chrome, since most job pages load the description with JavaScript and can't be read with a plain fetch. Replace each URL with the jobs/<slug>.txt path it printed. URLs it marks FAIL go straight to the FAILED list; don't send them to a subagent.
3. For EACH input (now all .txt paths), launch a separate resume-tailor subagent. Launch them ALL in parallel in a single step, not one after another.
4. When all subagents finish, run:
   python3 build_resume.py
   Resumes must be exactly one page. If any line says "FAIL ... longer than one page", send that resume's subagent a message to cut content (drop the least relevant bullets or shorten wording), then rebuild. Repeat until every resume builds.
5. Honesty check: for each output/*/resume.json, compare every bullet and the summary against base/resume.json. Flag any claim (metric, tool, responsibility) that isn't supported by the base. Don't fix silently; list them.
6. Reply with a table: company | role | pdf path | top gaps | flags. Then list any FAILED inputs and tell me to paste those job descriptions into jobs/<name>.txt and rerun with the file path.
