# Fermanagh and Omagh District Council

Support for schedules provided by [Fermanagh and Omagh District Council](https://www.fermanaghomagh.com/services/environment-and-waste/waste-collection-calendar/), serving the Fermanagh and Omagh district of Northern Ireland.

## Configuration via configuration.yaml

(recommended)

```yaml
waste_collection_schedule:
    sources:
    - name: fermanaghomagh_gov_uk
      args:
        property_id: "PROPERTY_ID"
```

or (not recommended)

```yaml
waste_collection_schedule:
    sources:
        - name: fermanaghomagh_gov_uk
          args:
            postcode: "BT78 1RG"
            house_number: "1"
```

### Configuration Variables

**property_id**  
*(string) (required if postcode not provided)*

**postcode**  
*(string) (required if property_id not provided)*

**house_number**  
*(string) (required if property_id not provided)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fermanaghomagh_gov_uk
      args:
        property_id: "GMtpf6Tk1glK57Zj"
```

## How to get the property_id argument

The property_id can be found in the URL when looking up your
bin collection days at [Fermanagh and Omagh bin collection days](https://fermanaghomagh.isl-fusion.com).

## Why property_id over postcode and house_number?

The code has to do a search by postcode and house number then look up the bin collection time using the property ID. Providing the property_id directly skips this lookup step.
