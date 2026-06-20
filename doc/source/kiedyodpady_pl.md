# Kiedy Odpady (kiedyodpady.pl)

Support for schedules provided by [kiedyodpady.pl](https://kiedyodpady.pl) (also known as mOdpady / mMieszkaniec), a Polish waste collection platform used by multiple municipalities.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kiedyodpady_pl
      args:
        municipality: pabianice       # subdomain slug, e.g. "pabianice" for pabianice.kiedyodpady.pl
        city: "Pabianice (miasto)"
        street: 'ul. 15 Pułku Piechoty "Wilków"'   # optional for some localities
        number: "pozostałe"                          # optional for some localities
```

### Configuration Variables

**municipality**
*(String) (required)* The subdomain slug for your municipality. Everything before `.kiedyodpady.pl` — for example, if your URL is `pabianice.kiedyodpady.pl` the value is `pabianice`.

**city**
*(String) (required)* City/locality name exactly as shown in the dropdown on the kiedyodpady.pl website for your municipality.

**street**
*(String) (optional)* Street name exactly as shown in the UI. Not required for all localities.

**number**
*(String) (optional)* House number / address entry exactly as shown in the UI. Not required for all localities.

## How to get the source arguments

1. Open `https://{municipality}.kiedyodpady.pl` in your browser (e.g. `https://pabianice.kiedyodpady.pl`).
2. Step through the address selection UI — choose your city, then street, then house number.
3. The `municipality` value is the subdomain prefix shown in the URL.
4. Copy city, street, and number values **exactly** as displayed in the dropdown lists (including prefixes like `ul.`).

## Confirmed municipalities

| Municipality | URL |
|---|---|
| Wieliczka | https://wieliczka.kiedyodpady.pl |
| Pabianice | https://pabianice.kiedyodpady.pl |

Other municipalities using the kiedyodpady.pl platform should also work — use the subdomain as the `municipality` value.

## Example — Wieliczka

```yaml
waste_collection_schedule:
  sources:
    - name: kiedyodpady_pl
      args:
        municipality: wieliczka
        city: "Wieliczka (miasto)"
        street: "ul. Adama Asnyka"
        number: "pozostałe"
```
