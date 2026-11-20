---
description: Tailor the base resume to multiple job links in parallel
argument-hint: <job-url-or-txt-path> [more ...]
---
Job inputs: $ARGUMENTS

1. Split the inputs on whitespace (strip trailing commas). Each one is a job URL or a path to a .txt job description.
2. Turn every URL into a jobs/<slug>.txt file:
   a. URLs on jobs.ashbyhq.com, jobs.lever.co, or greenhouse.io (or with a gh_jid= query param) go straight to the script in step c. It reads those boards' APIs, which return the exact posting text.
   b. For all other URLs, WebFetch each one (all in parallel) and ask for the full posting verbatim: company, title, location, salary, responsibilities, and all qualifications. If the result has a real description, write it to jobs/<company>-<role>.txt (lowercase, hyphenated) in this format:
      Company: <company>
      Role: <role>
      Source: <url>

      <full description>
      If the result is empty, a loading page, a login wall, or missing the responsibilities or qualifications, send that URL to step c.
   c. Run every remaining URL through the script in one command:
      python3 fetch_job.py <url> [<url> ...]
      It saves each posting to jobs/<slug>.txt using the board's API or headless Chrome, for pages that load the description with JavaScript. URLs it marks FAIL go straight to the FAILED list; don't send them to a subagent.
   Replace each URL with its jobs/*.txt path.
3. For EACH input (now all .txt paths), launch a separate resume-tailor subagent. Launch them ALL in parallel in a single step, not one after another.
4. When all subagents finish, run:
   python3 build_resume.py
   It saves each PDF as output/<slug>/carter-lee-<company>.pdf (company name from the "Company:" line in notes.md).
   Resumes must be exactly one page. If any line says "FAIL ... longer than one page", send that resume's subagent a message to cut content (drop the least relevant bullets or shorten wording), then rebuild. Repeat until every resume builds.
5. Reply with a table: company | role | pdf path | top gaps. Then list any FAILED inputs and tell me to paste those job descriptions into jobs/<name>.txt and rerun with the file path.
