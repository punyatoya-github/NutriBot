### **Contributing Guide**

Thank you for your interest in contributing to DocChat. This document explains how to report issues, propose changes, and submit code so we can collaborate efficiently and keep the project high quality.

---

### **✨ Getting started**

1. Fork the repository and clone your fork:  
   * git clone https://github.com/punyatoya-github/docchat.git  docchat
   * cd docchat  
2. Create a feature branch:  
   * git checkout \-b feat/my-feature  
3. Create a Python 3.11 virtual environment and install dependencies:  
   * python3.11 \-m venv venv  
   * source venv/bin/activate  
   * pip install \-r requirements.txt  
4. Copy .env.example → .env and fill in required credentials (never commit .env)

---

### **🧭 How to contribute**

* Bug reports: Open an Issue with a clear title, a concise description, steps to reproduce, expected vs actual behavior, and environment details.  
* Feature requests: Open an Issue describing the use case, expected behavior, and possible implementation notes.  
* Code contributions: Submit a Pull Request (PR) from your forked branch that targets the main repository’s development or release branch (e.g., 2-final). Keep PRs small and focused.

---

### **🧩 Branching & workflow**

* Create branches using the pattern:  
  * feat/\<short-description\>  
  * fix/\<short-description\>  
  * docs/\<short-description\>  
* Rebase or merge the latest upstream changes before opening a PR.  
* Each PR must include a clear description of what it changes and why.

---

### **✅ PR checklist**

Before requesting a review, ensure:

* Code follows existing style and patterns (read existing modules for guidance).  
* New functionality includes tests where appropriate.  
* All tests pass locally.  
* Static checks (linters, formatting) are run. Use black/isort/flake8 if configured.  
* Documentation updated (README, docs, or code comments) for user-facing changes.  
* No secrets or credentials were committed.

Suggested PR description sections:

* Summary: one-paragraph overview of the change  
* Motivation: why the change is needed  
* Implementation: key files changed and high-level approach  
* Tests: how this was tested locally  
* Backwards compatibility notes (if any)

---

### **🧪 Testing**

* Add unit/integration tests under a tests/ directory where applicable.  
* Use pytest for running tests:  
  * pytest tests/  
* Include small sample inputs/fixtures where useful.  
* For model or large-file dependent tests, use mocks or short fixtures; avoid committing large binaries.

---

### **📚 Style and documentation**

* Follow existing code structure and modularization.  
* Write clear docstrings for public functions and classes.  
* Update README.md, examples, or docs for any user-visible change.  
* Provide usage examples for new features.

---

### 

### **🔐 Security & secrets**

* Never commit credentials, API keys, or large datasets. Use .env and add it to .gitignore.  
* If you accidentally commit secrets, remove them and rotate the credentials immediately.

---

### **🐛 Reporting issues**

When filing an issue, include:

* A descriptive title and short summary  
* Steps to reproduce  
* Expected vs actual behavior  
* Environment (OS, Python version, package versions)  
* Attach logs, stack traces, or small sample files if helpful

---

### **👥 Code of Conduct**

Be respectful and professional. Contributions come from many people with different backgrounds and experience levels. Treat others with kindness and constructive feedback.

---

### **📬 Communication & support**

* Use GitHub Issues for bugs and feature requests.  
* Open a PR for code changes. Tag maintainers in PRs if you need a quick review.  
* If you need mentoring or help splitting a large task, open an Issue labeled "help-wanted".

---

### **📦 Release & packaging**

* Keep changes small per PR and reference the target release branch.  
* Document breaking changes clearly in PRs.  
* Tag maintainers for release approvals.

---

### 

### 

### **🧾 License**

By contributing, you agree that your contributions will be licensed under the project’s MIT License.

---

### **Templates**

Issue template (copy into new Issue body)

\#\#\# Summary  
Short summary of the problem/feature.

\#\#\# Steps to reproduce  
1\. Step one  
2\. Step two

\#\#\# Expected behavior  
Describe expected result.

\#\#\# Actual behavior  
Describe actual result and include logs/tracebacks.

\#\#\# Environment  
\- OS:  
\- Python:  
\- Requirements (pip freeze):

Pull Request template (copy into PR body)

\#\#\# Summary  
One-line summary of the PR.

\#\#\# Motivation  
Why is this change needed?

\#\#\# Implementation  
Files changed and key approach.

\#\#\# Tests  
How to run tests and what was covered.

\#\#\# Notes  
Backwards compatibility, potential follow-ups.

---

Thank you — your contributions make DocChat better. 