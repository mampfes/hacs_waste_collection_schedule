## Summary

<!-- What does this PR do? -->

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
