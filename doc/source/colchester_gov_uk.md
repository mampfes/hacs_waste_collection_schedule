# Colchester Council

Support for schedules provided by [Colchester Council](https://www.colchester.gov.uk/your-recycling-calendar/), serving the borough of Colchester, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: colchester_gov_uk
      args:
        llpgid: LLPDID_CODE
```

### Configuration Variables

**llpgid**<br>
*(string) (required)*

#### How to find your `llpgid` code
The LLPDID code can be found in the URL after entering your postcode and selecting your address on the [Colchester Your recycling calendar page](https://www.colchester.gov.uk/your-recycling-calendar/). The URL in your browser URL bar should look like `https://www.colchester.gov.uk/your-recycling-calendar/?start=true&step=1&llpgid=1197e725-3c27-e711-80fa-5065f38b5681`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: colchester_gov_uk
      args:
        llpgid: "1197e725-3c27-e711-80fa-5065f38b5681"
```