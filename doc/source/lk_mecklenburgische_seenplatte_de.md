# Landkreis Mecklenburgische Seenplatte

Support for schedules provided by [Landkreis Mecklenburgische Seenplatte](https://www.lk-mecklenburgische-seenplatte.de) located in Mecklenburg-Vorpommern, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lk_mecklenburgische_seenplatte_de
      args:
        city: Neubrandenburg
        street: Atelierstraße
```

### Configuration Variables

**city**
*(string) (required)*

Name of the municipality, as shown in the dropdown on the [Abfallkalender](https://www.lk-mecklenburgische-seenplatte.de/Abfallkalender) page.

**street**
*(string) (required)*

Street or district name. See the note below on how to find the correct value.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lk_mecklenburgische_seenplatte_de
      args:
        city: Altentreptow
        street: Ahornweg
```

## How to get the source arguments

1. Open the [Abfallkalender](https://www.lk-mecklenburgische-seenplatte.de/Abfallkalender) page.
2. Select your municipality from the **Ort** dropdown. The value to use for `city` is the name shown in the list (e.g. `Neubrandenburg`, `Dargun`, `Altentreptow`).
3. Start typing your street name in the **Straße** field and note the matching suggestion.

**Note on parentheses in street names:** The autocomplete API does not handle search terms containing parentheses. Many entries are displayed as "StreetName (CityName)" (e.g. "Dargun (Dargun)"), but you should use only the part before the parenthesis as the `street` value (e.g. `Dargun`). The source will still find the correct match.
