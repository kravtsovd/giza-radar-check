# Replay the six-scene Giza test

This package measures how a known plan position ranks among 32 nearby positions. A separate height scan asks whether the strongest response recovers a known floor. September Capella selected the processing recipe. The October Capella and ICEYE acquisitions tested it. Three earlier Umbra acquisitions provided a further test after the first results were seen.

| Acquisition | King's rank at +43 m | Strongest King's height | Queen / Subterranean ranks |
| --- | ---: | ---: | ---: |
| Capella, 16 Sep 2024, training | 31/32 | +1.0 m | 27 / 8 |
| Capella, 4 Oct 2024 | 32/32 | +1.0 m | 15 / 9 |
| ICEYE, 2 Jun 2025 | 31/32 | -1.5 m | 11 / 24 |
| Umbra, 7 Feb 2023 | 26/32 | -29.0 m | 28 / 8 |
| Umbra, 8 Feb 2023 | 17/32 | -0.5 m | 21 / 17 |
| Umbra, 8 Mar 2023 | 21/32 | -5.5 m | 26 / 17 |

The primary gate required at least 31/32 and a better rank than both comparison scores. Those scores used apparent motion amplitude and full-image brightness. The King's supplied position passed on two of five transfer scenes. It never recovered its +43 m floor in the free search. The six acquisitions were previously studied, and the chamber labels were known. Neighboring views share surface texture, look windows and reference patches. [Expected numbers](expected.json) · [Original design](protocol.json) · [Umbra follow-up](umbra-protocol.json)

## Run from the measured arrays

Download or clone the complete repository. From its root, use Python 3.11 or 3.12 with NumPy and SciPy.

```sh
python -m pip install numpy==2.0.2 scipy==1.13.1
python tools/replay/run.py
```

The check runs every combination of three pairings, two orbit-baseline projections, three wavelengths and two estimators. It trains only on the September King's rank. It compares the resulting 324 three-room ranks with the saved table. It also checks the fixed recipe's local ranks, two baselines and free height peaks on all six acquisitions. To keep the full numerical output, run the following command. [Analysis code](score.py) · [Verification entry point](run.py)

```sh
python tools/replay/run.py --out results
```

The six NPZ archives contain arrays of ordinary numbers. Each file holds the measured offsets, timing, orbital factors, power, and fixed station coordinates. It can be opened with NumPy using `allow_pickle=False`. Each source record contains the input and archive checksums. The three Umbra archives retain the selected pair design for the separate transfer. [Public input filenames, URLs and SHA-256](inputs.json)

## Rebuild the measurements from public satellite products

Use the nine URLs in the manifest. Keep their relative paths under a directory named `downloads`. The following commands begin at the repository root. The first three scenes require NumPy and SciPy. Umbra additionally requires Sarpy.

```sh
python -m pip install sarpy
for day in 20240916 20241004 20250602
do
  python tools/replay/measure.py downloads "$day" --out measured
done
for day in 2023-02-07 2023-02-08 2023-03-08
do
  python tools/replay/umbra.py --data downloads/Umbra --date "$day" --out measured
done
python tools/replay/run.py --inputs measured --out results-from-images
```

The reader starts from the provider's focused complex image. Capella uses polar-format geometry. ICEYE uses an approximate linear mapping from processed Doppler position to time. Umbra uses the native SICD polar-angle polynomial and orbit. These paths produce half-aperture looks, then register 128 × 128 sample patches followed by 24 azimuth × 32 range samples. The fixed native-pixel window has a different physical footprint on each product. Adjacent looks in the three longer acquisitions had median patch correlations around 0.99977. They do not provide 192 independent observations. [Image measurements](measure.py) · [Umbra measurements](umbra.py)

Depth or signed height appears in the steering function divided by an assumed wavelength. We tested 0.24, 0.30 and 0.48 m as separate published examples. Seyfzadeh describes his own choice and says he did not use the journal value. Our wavelength choices do not identify his Khufu implementation. Uniform phase-randomized controls preserve full-image brightness but destroy spatial phase. This comparison cannot distinguish a cavity from stable surface scattering. The public results ledger keeps the geometric, pulse, surface, control-site and ground-gravity tests separate. [Study ledger](../../data/research.json) · [Control measurements](controls.json)

## Attribution and method sources

Derived numerical measurements were prepared by the Giza Radar Check project from the open datasets of Capella Space, ICEYE and Umbra. The project cropped, filtered, registered and scored the source imagery. The providers' archives identify the source imagery as CC BY 4.0. The manifest provides a direct link and checksum for each input. [Capella Space](https://registry.opendata.aws/capella_opendata/) · [ICEYE](https://registry.opendata.aws/iceye-opendata/) · [Umbra](https://registry.opendata.aws/umbra-open-data/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Filippo Biondi and Corrado Malanga published the Khufu equations in 2022. The journal retracted the paper in 2026. Biondi's patent describes paired subbands and a depth operator. Manu Seyfzadeh described coarse and fine tracking and adjoint focusing. Pietro Canini published related open tests. The implementation here uses its own declared geometry, reference subtraction, covariance weighting and success rule. [Article](https://doi.org/10.3390/rs14205231) · [Retraction](https://doi.org/10.3390/rs18162679) · [Patent](https://patents.google.com/patent/WO2024008365A1/en) · [Tracking description](https://youtu.be/SjJTRVgr9Mw?t=3397) · [Adjoint description](https://youtu.be/SjJTRVgr9Mw?t=2129) · [Canini protocol](https://www.accadradinuovo.com/Lab/giza_sar/prova_camere/file/PROTOCOLLO.md)

The geographic center follows the AERA survey. The aboveground chamber positions and rounded floor labels follow historical survey plans. The subterranean point is approximate. Different surface heights and radar layover can change which scatterer enters a patch. [AERA survey](https://aeraweb.org/wp-content/uploads/2020/04/AR2018.pdf#page=5) · [Petrie survey](https://pdfs.petrieproject.com/cu31924012038927.pdf)
