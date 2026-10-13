# Translation templates

Files in this directory are hand-maintained translations of the integration UI.
They do not contain generated `args_<source>` or `reconfigure_<source>` steps.
`update_docu_links.py` uses a template when present, adds the provider labels and
descriptions, and writes the corresponding generated
`custom_components/waste_collection_schedule/translations/<language>.json` file.
The post-merge documentation workflow runs this generation automatically.

To add a language, add its code to `LANGUAGES` in `update_docu_links.py`, translate
the common UI in a template, and add provider-specific translations where useful.
Retain every formatting placeholder such as `{type}`, `{index}`, `{docs_url}`
and `{howto}`. Existing languages without a template still use their current
translation files as input.

Finnish (`fi`) includes the common UI and Kiertokapula parameters. Other provider
labels can be translated incrementally via `PARAM_TRANSLATIONS` and
`PARAM_DESCRIPTIONS` (or the equivalent pipeline parameter metadata).

`ui_overrides.json` contains small common UI additions, keyed by language. The
generator recursively merges these into both existing translations and templates
before adding provider steps. Use it to update shared fields without copying a
whole language template or editing generated translation files.
