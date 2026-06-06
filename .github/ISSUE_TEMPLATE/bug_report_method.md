name: Bug Report Method
description: Detailed bug reporting methods and debug tools.
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
  - type: textarea
    id: reproduction
    attributes:
      label: Reproduction Steps
      description: Steps to reproduce the issue.
      placeholder: |
        1. Run mailspoof start
        2. Choose template 1
        3. Target email: user@example.com
        4. See error
  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      placeholder: What should have happened?
  - type: input
    id: version
    attributes:
      label: Version
      placeholder: e.g. v1.1.0
  - type: input
    id: os
    attributes:
      label: Operating System
      placeholder: e.g. Ubuntu 22.04, macOS 14
