# Giza Radar Check

Can satellite radar locate a known chamber inside a pyramid on two different dates?

**[Read the illustrated project brief](https://kravtsovd.github.io/giza-radar-check/)**

Two free Capella observations of Giza are available. We verified the files and recomputed the scores from Pietro Canini’s independent reconstruction. In the finer-resolution test, the Queen’s Chamber beat 23 of 24 nearby positions on one date and 6 of 24 on the other. Its contrast changed sign. The deep structures reported under Khafre remain unverified.

| Start here | What you get |
| --- | --- |
| [Project page](https://kravtsovd.github.io/giza-radar-check/) | The claim, evidence, sources and proposed blind test |
| [Scene manifest](data/scenes.json) | Direct downloads, exact sizes and SHA-256 fingerprints |
| [Scoring audit](tools/audit.py) | Recalculate the chamber ranks · [Expected output](data/score-audit.txt) |
| [Download tool](tools/fetch.py) | Fetch the public radar and metadata with integrity checks |

### Run locally

Use Python 3.11 or later. The scripts use only the standard library.

```sh
python3 tools/audit.py
python3 tools/fetch.py --metadata-only downloads
python3 tools/fetch.py downloads
```

The two full images total 6.77 GB. The audit downloads Canini’s result tables independently. It does not reconstruct the chambers from raw observations. For the next test, see the prospective protocol in the project brief.

### Sources and reuse

[Original paper](https://arxiv.org/abs/2208.00811) · [Retraction](https://doi.org/10.3390/rs18162679) · [November comparison](https://archaeologicalrescue.org/biondi-validation/) · [Canini’s protocol and data](https://www.accadradinuovo.com/Lab/giza_sar_verifica_en.html) · [Capella Open Data, CC BY 4.0](https://registry.opendata.aws/capella_opendata/). Third-party materials retain their respective terms. See [image credit](assets/CREDITS.md).
