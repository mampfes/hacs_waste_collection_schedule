# bonnorange AöR

Support for schedules provided by [bonnorange AöR](https://www.bonnorange.de), the waste management company of Bonn, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bonnorange_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
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
    - name: bonnorange_de
      args:
        street: "Markt"
        house_number: 1
```

## How to get the source arguments

Look up your address in the official collection-date search at
`https://www5.bonn.de/WasteManagementBonnOrange/WasteManagementServlet?SubmitAction=wasteDisposalServices`.

Pick the first letter of your street, then select the street from the drop-down list. Use the street name **exactly** as it is spelled there — for example `Markt`, `Berliner Platz` or `Münsterstr.` (abbreviated, not `Straße`). If the street cannot be found, the error message lists the available street names for that letter.

`house_number` expects a numeric value. Any suffix, such as `A` or `1/2`, has to be passed separately via `address_suffix`.
