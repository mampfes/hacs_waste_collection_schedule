# Stadt Hilchenbach

Support for schedules provided by [Stadt Hilchenbach](https://www.hilchenbach.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hilchenbach_de
      args:
        strasse: STRASSE
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name or partial street name. Must match exactly one entry.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hilchenbach_de
      args:
        strasse: "Dammstr"
```

## How to get the source arguments

1. Go to [Abfallkalender online](https://www.hilchenbach.de/Bauen-Wohnen/Abfallbeseitigung/Abfallkalender/Abfallkalender-online/).
2. Select your district (Stadtteil) and enter your street name.
3. Use the street name (or a unique partial match) as the `strasse` value.

*Note:* The value must match exactly one street. If multiple streets match, use a more specific search term. Street names are followed by the district in parentheses, e.g. `Dammstraße (Hilchenbach)` — you can search by partial name such as `Dammstr`.
