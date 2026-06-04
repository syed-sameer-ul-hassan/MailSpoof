name: Feature Request
description: Suggest a new feature or enhancement.
labels: [enhancement]
body:
  - type: textarea
    id: description
    attributes:
      label: Description
      description: What feature would you like to see?
      placeholder: Describe the feature...
    validations:
      required: true
  - type: textarea
    id: use_case
    attributes:
      label: Use Case
      description: Why do you need this feature?
      placeholder: How would you use it?
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives
      description: Any alternative solutions you've considered.
