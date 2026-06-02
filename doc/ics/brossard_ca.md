# Brossard, Québec

Brossard, Québec is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit https://brossard.ca/calendrier-des-collectes/ and select your sector (A, B, C, E, I, J, L, M, N, O, P, R, S, T, V, X, or Y).
- Scroll to the "Collection schedule for your residence" section.
- Right-click on "Add the 2026 collection schedule to my calendar (ICS)" and select `Copy link address`.
- Use this copied URL as the `url` parameter.

## Examples

### Secteur A (English)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://brossard.ca/app/uploads/2026/01/bciti-collections-BROSSARD-66c692504abe45198c3041f1-2025-09-12-2025-en-A-B-E-Sectors.ics
```
### Secteur A (Français)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://brossard.ca/app/uploads/2025/12/bciti-collections-BROSSARD-66c692504abe45198c3041f1-2025-05-12-2025-fr-Secteurs-A-B-E.ics
```
