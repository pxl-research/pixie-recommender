# PiXie Core: het hart van de aanbevelingsflow

PiXie Core zorgt ervoor dat mensen met een aankoopvraag snel de juiste producten en vervolgstappen krijgen. Het is de schakel tussen de gebruiksvriendelijke chatinterface en de slimme diensten die tabellen doorzoeken, follow-upvragen bedenken en resultaten presenteren.

## Wat doet deze service?

- Begrijpt waar een vraag over gaat en kiest de juiste productcategorie.
- Houdt korte gesprekken bij zodat vervolgvragen logisch op elkaar aansluiten.
- Stelt extra vragen als er meer informatie nodig is om tot een passende selectie te komen.
- Vertaalt antwoorden naar filters voor de tabellendatabase, die de echte productgegevens bevat.
- Geeft een helder overzicht terug van de best passende opties of licht toe dat er niets gevonden is.

## Hoe past het in het PiXie-landschap?

| Rol | Uitleg |
| --- | --- |
| Bron van vragen | De `chat_ui` vraagt raad aan PiXie Core zodra een gebruiker een aanbeveling wil. |
| Databron | De service gebruikt de `pixie-tabular-db` voor de productgegevens. |
| LLM-ondersteuning | Andere PiXie-componenten leveren taalinzichten (zoals het bedenken van vervolgvragen). |
| Resultaat | Een makkelijk leesbaar antwoord dat de chat direct aan de gebruiker laat zien. |

PiXie Core werkt dus samen met de andere bouwstenen van PiXie om een vloeiende klantervaring te bieden, zonder dat gebruikers iets hoeven te weten over de achterliggende techniek.

## Waarom is dit belangrijk?

- **Rust in de flow:** gebruikers krijgen één aanspreekpunt voor hun keuzevraag.
- **Slim doorvragen:** vervolgvragen verschijnen alleen als dat waarde toevoegt.
- **Consistente antwoorden:** productfilters worden altijd op dezelfde manier toegepast.
- **Snelle integratie:** andere teams kunnen PiXie Core aanroepen zonder technische details te hoeven kennen.

## Een typische gebruikersreis

1. Een bezoeker van de chat vraagt bijvoorbeeld: “Welke laptop past bij thuiswerken en een beperkt budget?”
2. PiXie Core herkent dat dit een productaanvraag is en pakt de categorie “laptops”.
3. Er zijn nog te veel mogelijkheden, dus er volgt een gerichte vraag over het gewenste prijsniveau.
4. De gebruiker antwoordt met een bedrag; PiXie Core vertaalt dat naar een filter en zoekt opnieuw.
5. Er blijft een handvol laptops over. PiXie Core bouwt een duidelijk overzicht en stuurt dat naar de chat.

Het resultaat is een persoonlijke aanbeveling zonder dat iemand door tabellen of filters hoeft te klikken.
