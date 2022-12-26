# Umweltbetrieb Stadt Bielefeld

Support for schedules provided by [Umweltbetrieb Stadt Bielefeld](https://www.bielefeld.de/umweltbetrieb) located in Bielefeld, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bielefeld_de
      args:
        street: STREET
        house_number: HNR
        address_suffix: HNR_SUFFIX
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(integer) (required)*

**address_suffix**  
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bielefeld_de
      args:
        street: "Eckendorfer Straße"
        house_number: 57
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on `https://anwendungen.bielefeld.de/WasteManagementBielefeld/WasteManagementServlet?SubmitAction=wasteDisposalServices]`. Typos will result in an parsing error which is printed in the log. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.
`address_suffix` could be for example a alpha-numeric character "A" or a additional house number like "/1".
