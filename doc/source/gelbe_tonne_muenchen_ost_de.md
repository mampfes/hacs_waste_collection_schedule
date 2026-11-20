# Gelbe Tonne München-Ost (Knettenbrech + Gurdulic)

Support for the Gelbe Tonne (yellow packaging bin) collection schedules provided by [Gelbe Tonne München-Ost](https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender), Germany. Knettenbrech + Gurdulic collects the bin in the eastern part of Munich on behalf of the Dual Systems, starting 2027-01-01.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gelbe_tonne_muenchen_ost_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**
*(string) (required)*

Street name exactly as listed on the provider website, e.g. `Balanstr.`.

**house_number**
*(string) (optional)*

Only needed for streets that are split between collection districts. It can be a house number or a range exactly as shown on the website (`53-Ende, 48-Ende`). If it is missing for a split street, the configuration form offers the valid ranges.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gelbe_tonne_muenchen_ost_de
      args:
        street: "Balanstr."
        house_number: "53-Ende, 48-Ende"
```

## How to get the source arguments

Open <https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender> and select your street. If the website then asks for a house number, your street is split between collection districts: enter your house number or the shown range as `house_number`. Otherwise leave it empty.
