name: Bug Report
description: Report a bug or unexpected behavior.
labels: [bug]
body:
  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear description of the bug.
      placeholder: Describe what went wrong...
    validations:
      required: true
  - type: markdown
    attributes:
      value: |
        ## Bug Reporting Methods

        You can report bugs through any of the following channels:

        - **GitHub Issues**: [Open an Issue](https://github.com/syed-sameer-ul-hassan/MailSpoof/issues)
        - **Site / Docs**: [mailspoof.orildo.sbs](https://mailspoof.orildo.sbs)
        - **Email**: security.mailspoof@orildo.sbs
        - **Security Vulnerabilities**: Do NOT open public issues. Email security.mailspoof@orildo.sbs directly.

        ## Environment Info to Include

        Please run the following commands and paste the output:

        ```bash
        mailspoof --version
        python3 --version
        uname -a
        pip show mailspoof
        ```

        ## Log Files

        If applicable, include relevant log output from:

        ```bash
        cat ~/.mailspoof/audit.log | tail -n 50
        ```

        ## Screenshot / Code Snippet

        If possible, attach:
        - Screenshot of the error
        - Relevant code snippet
        - Stack trace (if any)

        ---

        **Thank you for helping improve MailSpoof!**

  - type: textarea
    id: logs
    attributes:
      label: Logs / Stack Trace
      description: Paste any error logs, stack traces, or terminal output.
      placeholder: |
        Paste logs here...
      render: shell
  - type: textarea
    id: screenshot
    attributes:
      label: Screenshot / Additional Context
      description: Drag and drop screenshots or provide additional context.
      placeholder: Any additional information...

---

## Reporting via Code

You can also report bugs programmatically using the MailSpoof debug module:

```python
# debug_report.py
from lib.core import Config
from lib.audit import generate_report

config = Config()

# Collect system info for bug report
import platform
import sys

bug_info = {
    "tool_version": config.data.get("version", "unknown"),
    "python_version": sys.version,
    "platform": platform.platform(),
    "config": str(Config.CONFIG_DIR),
    "logs": "~/.mailspoof/audit.log",
}

for key, value in bug_info.items():
    print(f"{key}: {value}")
```

Save as `debug_report.py` and run:

```bash
python3 debug_report.py
```

Include this output in your bug report.

## Quick Checklist

- [ ] I am using the latest version (`mailspoof --version`)
- [ ] I have checked existing issues for duplicates
- [ ] I have included reproduction steps
- [ ] I have included my OS and Python version
- [ ] I have attached logs if applicable
- [ ] This is NOT a security vulnerability (email security.mailspoof@orildo.sbs for those)

---

**Note**: For critical security vulnerabilities, please email **security.mailspoof@orildo.sbs** directly instead of opening a public issue. We will respond within 48 hours.
