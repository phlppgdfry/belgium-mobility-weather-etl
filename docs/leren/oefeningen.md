# Mobility ETL: oefenen en jezelf testen

[Leerroute](README.md) · [Codewandeling](codewandeling.md)

Schrijf eerst je antwoord. Open pas daarna de oplossing. Alle rekenvoorbeelden
zijn synthetisch. Voer eventuele wijzigingen in een oefenbranch en lokale
testomgeving uit. Installatie en lokaal starten staan in de [project-README](../../README.md).

## 1. Bereken de score zonder Python

Bereken de score bij (a) 08:00 en 1 mm regen, (b) 12:00 en 0 mm, (c) 18:00 en
10 mm. Is de uitkomst een voorspeld aantal ritten?

<details><summary>Antwoord en redenering</summary>

a: 100 + 20 − 12 = **108**. b: 100 + 0 − 0 = **100**.
c: 100 + 20 − min(120, 55) = **65**. Het is een relatieve, zelfgedefinieerde
contextscore. Er is geen model op echte ritvraag getraind en geen eenheid “ritten”.

</details>

## 2. Welke rij blijft over?

De invoer bevat twee weersregels voor dezelfde stad en hetzelfde uur. De eerste
heeft `extracted_at=10:00`, de tweede `extracted_at=09:00`. Welke kiest de huidige
transformatie? Hoe zou je “meest recent opgehaald” betrouwbaar definiëren?

<details><summary>Antwoord en redenering</summary>

De tweede invoerrij blijft over, dus 09:00. `keep="last"` kiest volgorde, geen
maximumtijd. Sorteer eerst op de afgesproken versietijd en bepaal een tie-breaker
bij gelijke tijden. Voeg een test toe met bewust verkeerd geordende invoer.

</details>

## 3. Herhaling of nieuwe geschiedenis?

Station A wordt om 08:00 ingeladen. Je herlaadt exact dezelfde snapshot. Daarna
haal je om 09:00 opnieuw data op, met dezelfde aantallen. Hoeveel feitrijen verwacht
je voor A als er vooraf geen waren?

<details><summary>Antwoord en redenering</summary>

**Twee**. De herhaling van `(A, 08:00)` veroorzaakt geen extra rij; `(A, 09:00)`
is een nieuw moment. “Waarden gelijk” is niet hetzelfde als “zelfde gebeurtenis”.
De dimensie houdt één actuele stationsrij.

</details>

## 4. Schrijf of verklaar deze SQL

Hoe toon je de laatste bekende snapshot per station? Waarom is dat anders dan
alle rijen op het globaal nieuwste moment selecteren?

<details><summary>Mogelijke oplossing: alleen lezen</summary>

```sql
WITH ranked AS (
    SELECT station_id, snapshot_at, available_bikes,
           ROW_NUMBER() OVER (
               PARTITION BY station_id ORDER BY snapshot_at DESC
           ) AS rn
    FROM fact_station_status
)
SELECT station_id, snapshot_at, available_bikes
FROM ranked
WHERE rn = 1;
```

De query bewaart ook een station dat in de laatste batch ontbreekt. Dat kan
nuttig zijn, maar toont mogelijk oude data: voeg een versheidsindicatie toe.
Het bestaande dashboard kiest de laatste batch en doet deze query niet.

</details>

## 5. Zoek de verborgen versheidsfout

Van 300 stations hebben er 299 een brontijd van gisteren. Eén is net bijgewerkt.
De versheidsgrens staat aan. Waarom kan de huidige controle toch slagen?

<details><summary>Antwoord en verbetering</summary>

De code controleert de nieuwste bronwaarde van de hele set. Ontwerp bijvoorbeeld
een maximumleeftijd per station of een toegestane fractie oude stations, afhankelijk
van de zakelijke afspraak. Test ook een ontbrekende brontijd. Alleen de grens
verlagen lost deze aggregatiefout niet op.

</details>

## 6. Vertel een incidentverhaal

De weerload slaagt; daarna mislukt de stations-API. Is de hele run teruggedraaid?
Wat controleer je vóór je zegt dat het dashboard weer correct is?

<details><summary>Antwoord</summary>

Nee, de weerload heeft een eigen transactie. Controleer beide datasets afzonderlijk,
de stationsfout, laatste succesvolle snapshot en dashboardcache. Bepaal expliciet
of gemengde actualiteit acceptabel is. Een run-ID of publicatiepoort kan later
helpen, maar is hier nog geen complete implementatie.

</details>

## 7. Kleine wijziging met aantoonbaar begrip

Wijzig in een oefenbranch de spitsbonus van 20 naar 15. Noteer eerst de verwachte
score voor 08:00/1 mm. Zoek de bestaande test die hierdoor moet veranderen. Draai
na lokale setup de tests volgens de README. Bewaar de uitvoer in je leerlogboek.

<details><summary>Verwachte uitkomst en controle</summary>

De score wordt **103**. De test in `tests/test_transform.py` verwacht nu 108.
Pas de verwachting pas aan nadat je de nieuwe regel hebt nagerekend. Voeg een
voorbeeld buiten de spits toe om te controleren dat die score gelijk blijft.
Een groene test met blind meegewijzigde verwachting bewijst geen begrip.

</details>

## 8. Leg het aan een planner uit

Een planner vraagt: “Kunnen we met dit dashboard zeggen dat regen minder ritten
veroorzaakt?” Geef een antwoord van maximaal vier zinnen.

<details><summary>Voorbeeldantwoord</summary>

“Dit dashboard toont beschikbaarheid en weersvoorspellingen. De vraagscore daalt
bij regen omdat die regel zo geprogrammeerd is. Dat bewijst geen effect op echte
ritten. Daarvoor hebben we geschikte ritgegevens en een analyse van andere
invloeden nodig.”

</details>

## Eindproef

Teken de route zonder hulp, wijs de functies aan, reken één score na, verklaar
een dubbele load en benoem één beperking. Scoor ieder onderdeel 0–3 met de
rubriek in [onthouden](onthouden.md). Gebruik een ander voorbeeld dan hierboven
om te controleren of je het principe begrijpt.
