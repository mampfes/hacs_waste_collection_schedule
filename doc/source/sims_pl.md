# SISMS.pl / BLISKO

Support for schedules provided by [SISMS.pl / BLISKO](https://sisms.pl), serving multiple, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sims_pl
      args:
        owner_id: "OWNER ID"
        town: TOWN
        street: STREET
        house_number: "HOUSE NUMBER"
        
```

### Configuration Variables

**owner**  
*(String | Integer) (optional)*

Name of the owner of the schedule. Hard coded to a owner_id.

Not required if you use owner_id.

**owner_id**  
*(String | Integer) (optional)*

You can see the owner_id in the URL of the website. For example, in the URL `https://gospodarkakomunalna.strefamieszkanca.pl/?ownerId=188` the owner_id is `188`.

Not required if you use owner.

**town**  
*(String) (required)*

Miejscowość

**street**  
*(String) (optional)*

Ulica (not required if you use town_address, which is the same as selecting a house number without selecting a street)

**street_address**  
*(String | Integer) (optional)*

House nunmber in the street.

Not required if you use town_address.

**town_address**  
*(String | Integer) (optional)*

Like street_address, but if you don't select a street.

Not required if you use street_address.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sims_pl
      args:
        owner_id: "188"
        town: Bobrza
        street: ul. St. Staszica
        street_address: "23"
```

same as

```yaml
waste_collection_schedule:
    sources:
    - name: sims_pl
      args:
        owner: "Gmina Miedziana Góra"
        town: Bobrza
        street: ul. St. Staszica
        street_address: "23"
```

usgin town_address

```yaml
waste_collection_schedule:
    sources:
    - name: sims_pl
      args:
        owner: "Jeżewo"
        town: Ciemniki
        town_address: "2a"
```
        
## How to get the source argument

Find the parameter of your address using [https://sisms.pl](https://sisms.pl) and write them exactly like on the web page.
