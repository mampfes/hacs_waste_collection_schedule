# Ville de Québec

Support for waste collection schedule for [Ville de Québec](https://www.ville.quebec.qc.ca/services/info-collecte/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ville_quebec_qc_ca
      args:
        street_number_and_name: YOUR_STREET_NUMBER_AND_NAME
        unique_id: OPTIONAL_ADDRESS_UNIQUE_ID
```

## Configuration Variables

**street_number_and_name** _(string) (required)_: Your street number and name in Quebec City

**unique_id** _(string) (optional)_: If multiple addresses match your search, use this value to select a specific address. This value is provided after "Use unique_id:" in the address suggestions.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ville_quebec_qc_ca
      args:
        street_number_and_name: "1935, Boulevard Henri-Bourassa"
```

## Handling Multiple Addresses

If your search returns multiple addresses, you'll see an error message with suggested values. For example:

```
SourceArgAmbiguousWithSuggestions: Several addresses match "430 4e rue": ["430, 4e Rue. Use unique_id: 219232-134009", "430, 74e Rue Est. Use unique_id: 320428-66242"]. To select a specific address, add 'unique_id' parameter with the ID shown after 'Use unique_id:' for your desired address
```

To select a specific address, add the `unique_id` parameter with the value that appears after "Use unique_id:" for your preferred address:

```yaml
waste_collection_schedule:
  sources:
    - name: ville_quebec_qc_ca
      args:
        street_number_and_name: "430 4e rue"
        unique_id: "219232-134009"
```
