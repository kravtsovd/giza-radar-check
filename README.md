# Giza Radar Check

Can satellite radar find a known chamber on a second pass? We are testing that question with open data before applying the method to a larger claim beneath the pyramid of Khafre.

| Eight proposed shafts beneath Khafre | A spiral around one proposed shaft |
| :---: | :---: |
| [![Khafre Project rendering of two rows of cylinders wrapped in yellow spirals](https://opusmagnum.org/wp-content/uploads/2025/07/Screen-Shot-2025-03-15-at-3.30.06-PM-2.png)](https://opusmagnum.org/wp-content/uploads/2025/07/Screen-Shot-2025-03-15-at-3.30.06-PM-2.png) | [![Khafre Project close-up of a yellow helix around a dark cylinder](https://opusmagnum.org/wp-content/uploads/2025/07/Screen-Shot-2025-03-16-at-12.52.06-AM-2-1024x574.png)](https://opusmagnum.org/wp-content/uploads/2025/07/Screen-Shot-2025-03-16-at-12.52.06-AM-2-1024x574.png) |

*Both images are 3D models presented by the Khafre Project in March 2025. The team inferred this geometry from radar. The shafts and spiral paths remain unverified.* [Original presentation gallery](https://opusmagnum.org/khafre-project-gallery/)

We start with existing satellite passes over known rooms and surveyed tunnels. If the method passes a blind test, we will look beneath Khafre and publish how many signals repeat, including zero. The project uses existing records and involves no excavation.

**[Read the illustrated project brief](https://kravtsovd.github.io/giza-radar-check/)**

[Watch the one-minute film on YouTube Shorts](https://www.youtube.com/shorts/ntOvITR3Ux4) · [Download the video](assets/giza-radar-check.mp4) · [English captions](assets/en.vtt)

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
