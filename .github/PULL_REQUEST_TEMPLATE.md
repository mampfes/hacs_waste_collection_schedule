## Summary

<!-- What does this PR do? -->

> **New source?** Development focus is currently on the upcoming v3.0.0 release — please target this PR at the `release/3.0.0` branch instead of `master`. Bug fixes for the current stable release still go against `master`.

## Type of change

- [ ] New source
- [ ] Bug fix / source fix
- [ ] Documentation update
- [ ] Other

## Checklist

- [ ] `python -m pytest tests/test_source_components.py -q` passes
- [ ] `ruff check --fix` and `ruff format` run on changed source files
- [ ] No generated files in diff (README.md, info.md, sources.json, translations/*.json — CI regenerates these post-merge)
- [ ] `doc/source/<name>.md` created for new sources
- [ ] TEST_CASES use real, publicly accessible addresses (not my own)
