# Add research to Giza Radar Check

The public project node is [Giza Radar Check](https://dkravt.ai/giza-radar-check/). The research repository holds its records. The [linked evidence graph](https://kravtsovd.github.io/giza-radar-check/data/ontology.json) gives each item a stable address.

| What changed | Update | Link it to |
| --- | --- | --- |
| Interview, article, film, code release or timestamped statement | `data/library.json` | Public original, author, access and a stable record ID |
| Satellite pass, survey, missing product or comparison site | `data/datasets.json` | Platform, UTC or known precision, product, provider and access terms |
| Processing step or modelling assumption | `data/research.json`, under `stages` | Source, known operations, tested choices and unresolved choices |
| Experiment or changed conclusion | `data/research.json`, under `tests` | Claim, stage IDs, scene IDs or independent references, measured result, decision and next test |
| Code, figure or numerical output | The appropriate public repository folder | Library or test record with context and reuse terms |

Keep the ID when updating a record. Give a different experiment a new ID. Preserve earlier outcomes and label which settings were chosen before the test. The library, scene and research builders can also regenerate their records from a supplied research archive. Apply corresponding changes to a builder when it owns the record. Check each new source link. Link restricted data to its provider or describe its availability. Publish only project-owned material and third-party files with verified redistribution terms.

The project working copy runs the graph build on each commit. For another clone enable the included hook with `git config core.hooksPath .githooks`. The hook sees only staged files. You can also run `python3 tools/build_hub.py` after staging updates to a register or adding project files. Commit the regenerated graph together with the records. The public page reads these three registers and the GitHub file listing on each visit. If a network read fails it retains the included snapshot. The file listing follows every new visible public repository file. A new private file only enters the public research catalog after its public description is reviewed.

For a website design change, run `python3 tools/build_hub.py --site-output /path/to/public/giza-radar-check/index.html` and deploy that file on dkravt.ai. The original [zoomable decision map](https://kravtsovd.github.io/giza-radar-check/decision-map.html) and [earlier illustrated brief](https://kravtsovd.github.io/giza-radar-check/brief.html) remain linked. The [project issues](https://github.com/kravtsovd/giza-radar-check/issues) accept corrections.
