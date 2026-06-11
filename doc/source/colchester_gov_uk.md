# Colchester Council

Support for schedules provided by [Colchester Council](https://www.colchester.gov.uk/your-recycling-calendar/), serving the borough of Colchester, Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new North East Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

The recommended setup uses your postcode and house number/name:

```yaml
waste_collection_schedule:
    sources:
    - name: colchester_gov_uk
      args:
        postcode: POSTCODE
        house: HOUSE_NUMBER_OR_NAME
```

Advanced users may instead provide the LLPG ID directly:

```yaml
waste_collection_schedule:
    sources:
    - name: colchester_gov_uk
      args:
        llpgid: LLPGID_CODE
```

### Configuration Variables

**postcode**  
*(string) (required when llpgid is not set)*  
UK postcode for the address, e.g. `CO5 8NT`. Whitespace and case are normalised.

**house**  
*(string) (required when llpgid is not set)*  
House number or name as it appears in the council's address picker, e.g. `16` or `The Old Forge`. Matched case-insensitively, falling back to a substring match when no exact match is found.

**llpgid**  
*(string) (advanced, optional)*  
LLPG GUID for the address. Provide this OR `postcode` + `house`. The LLPG ID can be found in the URL after entering your postcode and selecting your address on the [Colchester Your recycling calendar page](https://www.colchester.gov.uk/your-recycling-calendar/). The URL in your browser URL bar should look like `https://www.colchester.gov.uk/your-recycling-calendar/?start=true&step=1&llpgid=1197e725-3c27-e711-80fa-5065f38b5681`.

## Examples

Using postcode and house:

```yaml
waste_collection_schedule:
    sources:
    - name: colchester_gov_uk
      args:
        postcode: "CO5 8NT"
        house: "16"
```

Using LLPG ID:

```yaml
waste_collection_schedule:
    sources:
    - name: colchester_gov_uk
      args:
        llpgid: "1197e725-3c27-e711-80fa-5065f38b5681"
```
