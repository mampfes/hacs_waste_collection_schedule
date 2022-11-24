# INFEO based services 

INFEO is a platform for waste schedules, which has several German, Austrian and Swiss cities and districts as customers. The homepage of the company is https://www.infeo.at/.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: CUSTOMER
        zone: ZONE
```

### Configuration Variables

**customer**<br>
*(string) (required)*

**zone**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: bogenschütz
        zone: "Rottenburg (Bezirk 2; Baisingen; Ergenzingen)"
```

## How to get the source arguments

### customer

Approved list of customers (2022-11-13):

- `bogenschütz`: Bogenschuetz-Entsorgung.de

If your provider is also using infeo.at you can just try to use the name of your provider as customer. If you have any troubles please file an issue [here](https://github.com/mampfes/hacs_waste_collection_schedule/issues/new) and mention `@dm82m`.

### zone

#### Bogenschuetz-Entsorgung.de
- Go to your calendar at `https://www.bogenschuetz-entsorgung.de/images/wastecal/index-zone.html`.
- Leave the year as it is and select the zone of your choice.
- Copy the whole zone name and put it into `zone` of your configuration.

### city, street, house number

This is currently not implemented, as it is not needed for customer `bogenschütz`. If you need it, don't hesitate to file an issue [here](https://github.com/mampfes/hacs_waste_collection_schedule/issues/new) and mention `@dm82m`.
