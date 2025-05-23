# Sjöbo

This is a waste collection schedule integration for Sjöbo kommun in Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sjobo_se
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**city**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: sjobo_se
      args:
        address: Gamla torg 10
        city: Sjöbo
```

## How to get the correct address

Visit the municipality page [Hämtningskalender sopkärl](https://www.sjobo.se/bygga-bo-och-miljo/min-bostad/avfall/hamtningskalender-sopkarl.html) and follow the directions on the page. 
