# bulder-context

Nettsiden for Bulder designsystem, publisert med GitHub Pages fra `index.html`.

## Bygge

Generatoren ligger i `kilde/` og henter ikoner, farger og fonter fra Bulder-prosjektmappen.

Offentlig versjon (uten Aeonik, som er lisensiert):

```bash
cd kilde && python3 build.py "<Bulder-prosjektmappe>" ../index.html --no-aeonik
```

Intern versjon med Aeonik (skal ikke deles utenfor Bulder, ligger i `.gitignore`):

```bash
cd kilde && python3 build.py "<Bulder-prosjektmappe>" ../bulder-ikoner.html
```
