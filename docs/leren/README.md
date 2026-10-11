# Leer je Mobility ETL-project begrijpen

**Doel:** zelf kunnen uitleggen hoe brondata een dashboard worden, een kleine
wijziging kunnen controleren en een fout kunnen onderzoeken. Je hoeft vooraf
geen programmeerexpert te zijn. Begin met één record en breid van daaruit uit.

Dit materiaal is op 11 oktober 2026 op de repositorycode afgestemd. Het is geen
bevestiging dat jij de vaardigheden al beheerst of dat een cloudrun actief is.

## Begin hier

| Stap | Lees of doe | Wat je daarna moet kunnen |
|---|---|---|
| 1 | [Codewandeling](codewandeling.md) | Een weersrecord en stationsrecord volgen |
| 2 | [Begrippen](begrippen.md) | ETL, keys, snapshots, KPI's en kwaliteit uitleggen |
| 3 | [Oefeningen met uitklapbare antwoorden](oefeningen.md) | Zelf rekenen, SQL lezen en fouten onderzoeken |
| 4 | [Onthouden en leren met AI](onthouden.md) | Dagelijks oefenen en jezelf overhoren |
| 5 | [Leerlogboek](leerlogboek.md) | Bewijs en eigen vooruitgang bijhouden |

## Wat bestaat al en wat niet?

- **Aanwezig:** API-extractie, Python-transformaties, PostgreSQL-loads,
  stationskwaliteitscontroles, dashboard, tests en workflowbestanden.
- **Afzonderlijk aanwezig:** dbt-SQL-modellen. De Python-flow roept dbt niet aan;
  het dashboard leest de basistabellen rechtstreeks. Aanwezige SQL is niet per
  definitie gevalideerd op de gekozen database.
- **Voorwaardelijk:** de geplande workflow voert de ETL alleen uit als zijn
  `DATABASE_URL`-secret is ingesteld. Deze leermap heeft de live configuratie
  niet gecontroleerd.
- **Niet aanwezig als volledige implementatie:** Power BI/Fabric, één atomaire
  transactie over de hele flow, historische versies van stationsattributen,
  volledig lineagebeheer en vulling van de gereserveerde audittabel.

## Vaardighedenkaart

| Vaardigheid uit een BI-vacature | Waar je ze bestudeert | Wat je zelf moet aantonen |
|---|---|---|
| Python | [transform.py](../../src/mobility_etl/transform.py) | Voorspel en wijzig een transformatie |
| API's en extractie | [extract.py](../../src/mobility_etl/extract.py) | Leg bronvelden en foutafhandeling uit |
| SQL en database | [load.py](../../src/mobility_etl/load.py) | Leg keys, upsert en transactiegrenzen uit |
| ETL-automatisering | [flow.py](../../src/mobility_etl/flow.py) | Volg de volgorde en vind een gedeeltelijk falen |
| Datamodellering | Stationsdimensie en snapshotfeit in `load.py` | Formuleer de grain van beide tabellen |
| Datakwaliteit | [quality.py](../../src/mobility_etl/quality.py) | Herken wat een controle wel/niet vangt |
| KPI-logica | `estimated_mobility_demand` in `transform.py` | Reken de score na en benoem de beperking |
| Rapportering | [dashboard/app.py](../../dashboard/app.py) | Leg selectie van laatste snapshot en caching uit |
| Testen | [test_transform.py](../../tests/test_transform.py) | Voeg in een oefenbranch een zinvol randgeval toe |
| CI en scheduling | [.github/workflows](../../.github/workflows) | Onderscheid codechecks, planning en echte dataload |
| Governance/performance | Verbeterpunten in de codewandeling | Maak een meetbaar verbeterplan |
| Power BI/Fabric | Nog niet in deze repo | Aanvullende praktijk nodig; zie het Fabric-leerproject |

Een bestand met een technologie bewijst wat er gebouwd is, niet wat jij al kunt.
Vul je eigen niveau pas na een oefening in het leerlogboek in.

## Andere leerroutes

- [Sales Analytics: KPI's en dashboards](https://github.com/phlppgdfry/python-data-analytics-project/tree/main/docs/leren)
- [Sensorplatform: normaliseren, kwaliteit en integraties](https://github.com/phlppgdfry/environmental-sensor-data-platform/tree/main/docs/leren)
- [Fabric Lottery: datamodellen en de nog te bouwen Fabric-route](https://github.com/phlppgdfry/fabric-lottery-data-platform/tree/main/docs/leren)

[Terug naar de project-README](../../README.md)
