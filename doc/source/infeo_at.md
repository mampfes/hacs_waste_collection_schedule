# INFEO based services

INFEO is a platform for waste schedules, which has several German, Austrian and Swiss cities and districts as customers. The homepage of the company is [https://www.infeo.at/](https://www.infeo.at/).

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

**customer**  
*(string) (required)*

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: infeo_at
      args:
        customer: bogenschütz
        zone: "Dettenhausen"
```

## How to get the source arguments

### customer

Approved list of customers (2022-11-13):

- `bogenschütz`: Bogenschuetz-Entsorgung.de

If your provider is also using infeo.at you can just try to use the name of your provider as customer. If you have any troubles please file an issue [here](https://github.com/mampfes/hacs_waste_collection_schedule/issues/new) and mention `@dm82m`.

### zone

#### Bogenschuetz-Entsorgung.de

- Go to your [calendar](https://www.bogenschuetz-entsorgung.de/images/wastecal/index-zone.html).
- Browse through all the available years and check the naming of your desired zone and try to find what makes it unique.
- Put this unique string into `zone` of your configuration.
- It will just be checked if the calendar contains an entry that contains your keyword `zone`.

##### Example 1: Dettenhausen

- For 2022 it is: `Dettenhausen, Tübingen (Bebenhausen; Lustnau)`
- For 2023 it is: `Dettenhausen`
- Use `Dettenhausen` as zone

##### Example 2: Ofterdingen

- For 2022 it is: `Dußlingen, Ofterdingen`
- For 2023 it is: `Ofterdingen`
- Use `Ofterdingen` as zone

##### Example 3: Felldorf

- For 2022 it is: `Rottenburg (Bad Niedernau; Bieringen; Eckenweiler; Frommenhausen; Obernau; Schwalldorf), Starzach (Bierlingen; Börstingen; Felldorf; Sulzau; Wachendorf)`
- For 2023 it is: `Starzach (Bierlingen; Börstingen; Felldorf; Sulzau; Wachendorf)`
- Use `Felldorf` as zone

##### Example 4: Tübingen Innenstadt

- For 2022 it is: `Tübingen (Bezirk 4 - Innenstadt)`
- For 2023 it is: `Tübingen (Bezirk 4 - Innenstadt)`
- Use `Innenstadt` as zone
- Do NOT use `Tübingen` as it is used multiple times!

##### Example 5: Pfäffingen

- For 2022 it is: `Tübingen (Bühl; Hirschau; Kilchberg; Unterjesingen; Weilheim), Rottenburg (Kiebingen; Wurmlingen), Ammerbuch (Pfäffingen)`
- For 2023 it is: `Ammerbuch (Pfäffingen)`
- Use `Pfäffingen` as zone
- Do NOT use `Ammerbuch` as it is used multiple times!

### city, street, house number

This is currently not implemented, as it is not needed for customer `bogenschütz`. If you need it, don't hesitate to file an issue [here](https://github.com/mampfes/hacs_waste_collection_schedule/issues/new) and mention `@dm82m`.
