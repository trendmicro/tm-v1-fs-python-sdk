# Contributing Code

A good pull request:

- Is clear.
- Works across all supported versions of Python.
- Follows the existing style of the code base (see Codestyle section).
- Has comments included as needed.
- Must be appropriately licensed (MIT).

## Reporting An Issue/Feature

If you have a bugfix or new feature that you would like to contribute to SDK, please find or open an issue about it first.
Talk about what you would like to do.
It may be that somebody is already working on it, or that there are particular issues that you should know about before implementing the change.

## Contributing Code Changes

1. Run the linter and test suite to ensure your changes do not break existing code:

   ```bash
   # Install tox for task management
   $ python -m pip install tox
   
   # lint your changes and run the test suite
   $ tox
   ```
