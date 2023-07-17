# Renosyd i/s

Support for schedules provided by [Renosyd i/s](https://renosyd.dk/), serving Odder and Skanderborg kommuner, Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: renosyd_dk
      args:
        kommune: "odder" OR "skanderborg"
        husnummer: See description
        
```

### Configuration Variables

**kommune**  
*(String) (required)*

**husnummer**  
*(Int) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: renosyd_dk
      args:
        kommune: skanderborg
        husnummer: 123000
        
```

## How to get the house number / husnummer

Go to the page for either [Odder](https://odder.netdialog.renosyd.dk/citizen/) or [Skanderborg](https://skanderborg.netdialog.renosyd.dk/citizen/). Select your street and then house/apartment number. Select "husk min adresse", and then select "Næste...".

Now the house number is saved as a cookie. Open developer tools (right-click-> inspect in Firefox/Chrome), and look at the cookies (in Storage in Firefox, Application->Storage->Cookies in Chrome). There should be a single cookie storing a "StoredAddress" value - the house id number - and a session id which you can ignore.

### Filtering Example

hiding `Storskrald`

```yaml
waste_collection_schedule:
    sources:
    - name: renosyd_dk
      args:
        kommune: skanderborg
        husnummer: 123001
      customize:
        - type: Storskrald
          show: false
        
```
