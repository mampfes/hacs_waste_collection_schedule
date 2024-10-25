# Mölndal

This is a waste collection schedule integration for the Mölndal.
Mölndal is using EDPEvent but does not allow for address search.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: molndal_se
      args:
        facility_id: FACILITY_ID
```

### Configuration Variables

**facility_id**  
*(number) (required)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: molndal_se
      args:
        facility_id: 105000
```

## How to get the correct facility id

Your facility_id (Anläggning) can be found on invoices from Mölndals stad or
by the [Mölndals stad e-tjänst](https://etjanst.molndal.se/oversikt/overview/720).