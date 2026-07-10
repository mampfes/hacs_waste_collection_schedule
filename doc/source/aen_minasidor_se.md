# Aneby Miljö & Vatten

Support for waste collection schedules provided through [AEN Mina
Sidor](https://aen.minasidor.info/), serving Aneby, Eksjö and Nässjö,
Sweden.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: aen_minasidor_se
      args:
        email: EMAIL
        password: PASSWORD
        address: ADDRESS
```

### Configuration Variables

**email**
*(String) (required)*

The email address used to log in to AEN Mina Sidor.

**password**
*(String) (required)*

The password used to log in to AEN Mina Sidor.

**address**
*(String) (optional)*

The address of the property. It is detected automatically when the account has
only one property. If the account has multiple properties, leave this field
empty initially; the configuration flow will offer the available addresses.

Store the login details in Home Assistant's `secrets.yaml`.

```yaml
aen_minasidor_se_email: YOUR_EMAIL
aen_minasidor_se_password: YOUR_PASSWORD
aen_minasidor_se_address: YOUR_ADDRESS
```

### Example

```yaml
waste_collection_schedule:
  sources:
    - name: aen_minasidor_se
      args:
        email: !secret aen_minasidor_se_email
        password: !secret aen_minasidor_se_password
```
