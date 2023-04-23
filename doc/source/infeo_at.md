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

AND

**zone**  
*(string) (required)*

OR

**city**
*(string) (required)*

**street**
*(string) (required)*

**housenumber**
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

Approved list of customers (2023-04-23):

- `bogenschütz`: Bogenschuetz-Entsorgung.de
- `ikb`: ikb.at
- `salzburg`: Stadt-Salzburg.at

If your provider is also using infeo.at you can just try to use the name of your provider as customer. If you have any troubles please file an issue [here](https://github.com/mampfes/hacs_waste_collection_schedule/issues/new) and mention `@dm82m`.

### zone

#### Bogenschuetz-Entsorgung.de

- Go to your [calendar](https://www.bogenschuetz-entsorgung.de/blaue-tonne-tuebingen/abfuhrtermine.html) and select "Zonenkalender".
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

### city, street and housenumber 

#### Bogenschuetz-Entsorgung.de

- Go to your [calendar](https://www.bogenschuetz-entsorgung.de/blaue-tonne-tuebingen/abfuhrtermine.html) and select "Adresskalender".
- Select the city, street and housenumber.
- Put exactly these city, street and housenumber into your configuration here.

##### Example 1: Dettenhausen, Kirchstraße 32

- Use `Dettenhausen` as city
- Use `Kirchstraße` as street
- Use `32` as housenumber

#### ikb.at

- Go to your [calendar](https://www.ikb.at/abfall/abfallkalender-innsbruck).
- Select the city, street and housenumber.
- Ignore the fraction as we get all fraction available and you can later on filter in this integration, see [here](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/faq.md).
- Put exactly these city, street and housenumber into your configuration here.

##### Example 1: Innsbruck, Achselkopfweg 1

- Use `Innsbruck` as city
- Use `Achselkopfweg` as street
- Use `1` as housenumber

#### Stadt-Salzburg.at

- Go to your [calendar](https://services.infeo.at/WasteCalendar/salzburg/wastecal-address.html).
- Select the city, street and housenumber.
- Ignore the fraction as we get all fraction available and you can later on filter in this integration, see [here](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/faq.md).
- Put exactly these city, street and housenumber into your configuration here.

##### Example 1: Salzburg, Adolf-Schemel-Straße 13

- Use `Salzburg` as city
- Use `Adolf-Schemel-Straße` as street
- Use `13` as housenumber
