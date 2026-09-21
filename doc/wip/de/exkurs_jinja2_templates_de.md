> **⚠️ Work in progress – nicht geprüft.** Dieses Dokument (nur auf Deutsch) wurde von der Community beigesteuert und vom Maintainer-Team noch nicht inhaltlich geprüft. Es ist bewusst nicht aus der offiziellen Dokumentation verlinkt; Angaben können unvollständig oder veraltet sein.

# Exkurs: Jinja2-Templates

Dieser kleine Exkurs behandelt *rudimentär* die Syntax und Semantik der Template-Engine. Da die Template-Engine sehr flexibel ist, kann die Konfiguration der Anwendung hinsichtlich der Trennzeichen und des Verhaltens undefinierter Werte geringfügig vom hier vorgestellten Code abweichen.

Ein `Jinja2`-Template ist einfach eine Textdatei. `Jinja2` kann jedes textbasierte Format (`HTML`, `XML`, `CSV`, `LATEX` und so weiter...) generieren. Ein `Jinja2`-Template benötigt keine bestimmte Erweiterung wie beispielsweise .html, .xml oder jede andere Erweiterung.

Ein Template enthält Variablen und/oder Ausdrücke, die beim Rendern des Templates durch Werte ersetzt werden, und enthält ebenso Tags, welche die Logik des Templates steuern. Die Syntax hierbei ist stark von Django und Python inspiriert.

Es gibt verschiedene Arten von Trennzeichen. Die standardmäßigen `Jinja2`-Trennzeichen sind wie folgt konfiguriert:

- `{% ... %}` → für (limitierte Python-) Anweisungen
- `{{ ... }}` → für Ausdrücke, die in der Template-Ausgabe angezeigt werden sollen
- `{# ... #}` → für Kommentare, die nicht in der Template-Ausgabe enthalten sind

Zeilenanweisungen und Kommentare sind zwar ebenfalls möglich, verfügen jedoch nicht über standardmäßige Präfix-Zeichen und können nur dann verwendet werden, wenn dies im System (HA) auch derart festgelegt worden ist.

***Template-Variablen*** werden durch das an das Template übergebene Dictionary definiert. Man kann mit den Variablen in Templates experimentieren, vorausgesetzt, sie werden von der Anwendung auch übergeben. Variablen können Attribute oder Elemente enthalten, auf die man ebenfalls zugreifen kann.
Welche Attribute eine Variable hat, hängt stark von der Anwendung ab, die diese Variable bereitstellen soll.

Man kann anstelle der *Standard*-Python-`__getitem__`-'subscript'-Syntax [ ] auch einen Punkt (`.`) verwenden, um Zugriff auf die Attribute einer Variablen zu bekommen.

Die folgenden Zeilen bewirken demnach dasselbe :

```yaml
{{ foo.bar }}  
{{ foo['bar'] }}
```

**Wichtig**:
die äußeren doppelten geschweiften Klammern `{{` sind nicht Teil der Variablen, sondern der print-Anweisung. Wenn man auf Variablen innerhalb von Tags zugreifen möchte, dann darf man diese nicht in geschweifte Klammern setzen.

Ein Minus-Zeichen (`-`) trimmt das entsprechende Objekt davor (`{{-`, `{%-`) oder danach (`-}}`, `-%}`).

Wenn eine Variable oder ein Attribut nicht existieren, dann erhält man als Resultat davon einen ***undefinierten*** Wert zurück. Was man mit dieser Art von Wert tun kann, hängt gänzlich von der Konfiguration der jeweiligen Anwendung ab:  
das Standard-Verhalten besteht darin, dass nach der Auswertung beim Drucken oder Iterieren einer leeren Zeichenfolge der Vorgang sofort abgebrochen und eine Fehlermeldung generiert wird.