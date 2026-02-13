# Mid Sussex District Council (Whitespace WRP)

This source retrieves collection schedules for the Mid Sussex District Council, which uses the Whitespace Waste & Recycling Portal (WRP) system.

The source performs a multi-step web scraping process to correctly identify the property address and retrieve the schedule.

## Supported Inputs

This source requires three mandatory arguments to identify the property:

| Parameter | Required | Type | Description |
| :--- | :--- | :--- | :--- |
| **`postcode`** | Yes | `string` | The property's postcode (e.g., `RH17 6TB`). |
| **`number`** | Yes | `string` | The house number, house name, or business name (e.g., `11` or `HAPSTEAD HALL`). |
| **`street`** | Yes | `string` | The street name (e.g., `HIGH STREET`). |

## Example Configuration

The following example uses the named property 'Hapstead Hall' on High Street:

```yaml
waste_collection_schedule:
  sources:
    - name: midsussex_gov_uk
      args:
        postcode: RH17 6TB
        number: HAPSTEAD HALL
        street: HIGH STREET

## How to get the source arguments

Search for your collection schedule on the address on the [Mid-Sussex District Council](https://www.midsussex.gov.uk/waste-recycling/bin-collection/) site to see how they format your address. Preferred approach is to copy the address as displayed. HOUSE_NAME or HOUSE_NUMBER, STREET, POSTCODE are required but it can vary for multi-occupancy buildings etc, so you may need to adjust which parts of the address are used for each argument.
