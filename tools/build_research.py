"""Build the public research ledger from the checked replay and public evidence summaries."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "tools" / "replay"
EXPECTED = json.loads((REPLAY/"expected.json").read_text())
CONTROLS = json.loads((REPLAY/"controls.json").read_text())
DATES = list(EXPECTED["acquisitions"])
SCENES = ["capella-20240916","capella-20241004","iceye-20250602","umbra-20230207","umbra-20230208","umbra-20230308"]
C = SCENES[:2]
LONG = SCENES[:3]
U = SCENES[3:]
PAPER = "https://doi.org/10.3390/rs14205231"
RETRACTION = "https://doi.org/10.3390/rs18162679"
PATENT = "https://patents.google.com/patent/WO2024008365A1/en"
SEY = "https://archaeologicalrescue.org/biondi-validation/"
CANINI = "https://www.accadradinuovo.com/Lab/giza_sar/prova_camere/file/PROTOCOLLO.md"
SURVEY = "https://pdfs.petrieproject.com/cu31924012038927.pdf"
SIX = "tools/replay/expected.json"
CONTROL = "tools/replay/controls.json"
GA = "https://registry.opendata.aws/capella_opendata/"
IG = "https://www.iceye.com/open-data-initiative"
UG = "https://registry.opendata.aws/umbra-open-data/"
GROUND = "https://www.ngdc.noaa.gov/mgg/gravity/1999/document/html/egypt.html"
DEEP = "https://www.youtube.com/watch?v=bM8vzUUZdVM&t=10960s"
CEM = "https://archaeologicalrescue.org/wp-content/uploads/2026/11/Yoshimura_Y27_Y34_P8_Interactive_3D.html"
FIELD = "https://doi.org/10.1109/ACCESS.2026.3652346"
TUNNEL = "https://www.lngs.infn.it/en/lngs-overview/"
CT = "https://iceye-open-data-catalog.s3.amazonaws.com/stac-items/2023/12/ICEYE_D59J8T_20231225T040435Z_3175275_X31_SLEDF.json"
TEO = "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/sar-data/task-data/44f7aae4-0ca5-4a27-b733-12965da9f458/2024-02-14-16-11-33_UMBRA-04/2024-02-14-16-11-33_UMBRA-04.stac.v2.json"

def bilingual(value, name):
    en, ru = value.split(" | ")
    return {name:en, "ru_"+name:ru}

def stage(uid,title,known,unknown,operation,url):
    row={"id":uid,"url":url}
    for k,v in (("title",title),("known",known),("unknown",unknown),("test",operation)):
        row.update(bilingual(v,k))
    row["ru"]=row["ru_title"]
    return row

def trial(uid,title,claim,stages,scenes,result,decision,next_test,sources,url=CONTROL):
    row=dict(id=uid,stage_ids=stages.split(),scene_ids=scenes,sources=sources,url=url)
    for k,v in (("title",title),("claim",claim),("result",result),("decision",decision),("next_test",next_test)):
        row.update(bilingual(v,k))
    row["ru"]=row["ru_title"]
    return row

stages=[
stage("inputs","Identify the observation | Установить источник измерений",
"Six public complex images include amplitude, phase and acquisition geometry. | У шести открытых комплексных снимков есть амплитуда, фаза и геометрия съёмки.",
"The exact acquisition and pre-color numerical section behind the 648 m drawing remain unknown. | Для чертежа на 648 м неизвестны точная съёмка и численный разрез до раскраски.",
"Match products by identifier and SHA-256. Use survey coordinates fixed independently of chamber brightness. | Сверить файлы по идентификаторам и SHA-256. Взять координаты из наземной съёмки до анализа яркости.","tools/replay/inputs.json"),
stage("looks","Split the aperture | Разделить апертуру",
"Biondi describes using half the Doppler band. Seyfzadeh also describes a fixed master. | Бионди говорит о половине доплеровской полосы. Сейфзаде описывает вариант с постоянным опорным изображением.",
"Original mask edges, time mapping and pair spacing for each published section remain unspecified. | Границы фильтров, привязка времени и шаг пар для конкретного разреза не опубликованы.",
"Build 193 half-band looks. Pair adjacent centers, centers eight steps apart, or each look with one fixed master. | Построить 193 изображения из половины полосы. Сравнить соседние, со сдвигом на восемь шагов и с постоянным опорным.","tools/replay/measure.py"),
stage("track","Track apparent shifts | Измерить видимые сдвиги",
"Seyfzadeh describes coarse 128 × 128 sampling followed by 24 azimuth × 32 range samples. | Сейфзаде называет грубое окно 128 × 128 пикселей и точное окно 24 по азимуту на 32 по дальности.",
"Product spacing changes the physical footprint. Fine image shifts lack a colocated ground-motion record at Giza. | В метрах окно различается по спутникам. Синхронного измерения движения поверхности в Гизе нет.",
"Correlate complex patches, refine the peak, then subtract common motion measured on 32 reference positions. | Совместить комплексные фрагменты, уточнить максимум и вычесть общий сдвиг по 32 опорным точкам.","tools/replay/measure.py"),
stage("steer","Set the height scale | Задать шкалу высоты",
"Equations 20-24 link paired image offsets to complex steering vectors under an assumed wavelength. | Формулы 20-24 связывают сдвиги с комплексными векторами при выбранной длине волны.",
"The baseline convention, extra phase factor, seismic wavelength and subsurface transfer are not calibrated for these scenes. | Для этих сцен не откалиброваны проекция базы, множитель фазы, сейсмическая длина волны и передача сигнала из породы.",
"Compare along-track and elevation-plane baselines. Test the published 0.24, 0.30 and 0.48 m examples separately. | Сравнить базы вдоль траектории и в плоскости высоты. Раздельно проверить примеры 0,24, 0,30 и 0,48 м.",PAPER),
stage("focus","Focus the signal | Рассчитать отклик",
"The paper describes a Fourier-like inverse. Seyfzadeh says he used an adjoint. | В статье описано фурье-подобное обращение. Сейфзаде говорит о сопряжённом операторе.",
"The exact regularization and numerical scores before filtering the published authors' images are missing. | Отсутствуют точная регуляризация и численные значения, из которых получены исходные авторские изображения.",
"Score normalized complex correlation with and without noise weighting from separate reference patches. Lock on September King alone. | Сравнить комплексную корреляцию с поправкой на шум и без неё. Выбрать правило только по камере царя в сентябре.","tools/replay/score.py"),
stage("shape","Test position and shape | Проверить положение и контур",
"The surveyed plan and approximate signed floor heights supply independent comparison coordinates. | Геодезический план и примерные отметки полов задают независимые координаты сравнения.",
"A high value at one supplied height does not identify the walls or free height maximum. | Высокая оценка на заданной отметке сама по себе не определяет стены или высоту.",
"Score translated plans, a 90° rotation, a signed wall-minus-center contrast, and a free height scan. | Сопоставить сдвинутые планы, поворот на 90°, разность между стеной и центром и свободный поиск высоты.",SURVEY),
stage("validate","Test outside the training case | Проверить за пределами калибровки",
"Separate acquisitions, a driven reflector and two independently surveyed underground directions provide distinct tests. | Есть отдельные съёмки, вибрирующий отражатель и два независимых измерения направления подземных объектов.",
"The checked archives contain no unused surveyed target with all inputs for blind shaft depth validation. | Среди проверенных материалов нет неиспользованного объекта со всеми данными для слепой проверки глубины шахты.",
"Seal predicted coordinates, depth, uncertainty and a failure rule before opening a survey. Include matched empty-rock labels. | Зафиксировать координаты, глубину, погрешность и критерий неудачи до вскрытия плана. Включить проверенные участки сплошной породы.",TUNNEL)
]

tests=[
trial("six-scene-location","One fixed room position across six scenes | Одна известная точка на шести съёмках",
"A rule chosen at the supplied King's floor should rank the same location highly on other passes. | Правило, выбранное по известной отметке камеры царя, должно снова выделить её положение.",
"inputs looks track steer focus shape validate",SCENES,
"At +43 m the King's location beat 31, 32 and 31 of 32 neighbors on the long passes, then 26, 17 and 21 on Umbra. Only October beat all 32. | При +43 м точка камеры царя превзошла 31, 32 и 31 из 32 соседей на длинных съёмках, затем 26, 17 и 21 на Umbra. Все 32 она превзошла только в октябре.",
"The locked rule passed two of five transfer scenes at King's. No scene passed for all three chambers. | После калибровки правило прошло на двух из пяти съёмок для камеры царя. Ни одна съёмка не прошла сразу по трём камерам.",
"Forecast an unseen surveyed location before seeing any labels. | Предсказать положение нового обследованного объекта до знакомства с разметкой.",[PAPER,PATENT,SEY,SURVEY],SIX),
trial("free-height","Release the supplied floor height | Убрать известную высоту пола",
"If the signal measures the King's floor, let the peak select its own height. | Если сигнал измеряет высоту пола, максимум должен сам указать на него.",
"steer focus shape validate",SCENES,
"Over -44 to +44 m the King's peaks were +1, +1, -1.5, -29, -0.5 and -5.5 m. The supplied floor was +43 m. | На сетке от -44 до +44 м максимумы пришлись на +1, +1, -1,5, -29, -0,5 и -5,5 м. Заданная отметка пола была +43 м.",
"None recovered the floor. A location comparison at a supplied height and an unrestricted height estimate answer different questions. | Ни один максимум не восстановил пол. Сравнение мест на заданной высоте и независимая оценка высоты дают разные ответы.",
"Predict two unseen depth marks with a fixed vertical scale and benchmark. | Предсказать две закрытые отметки глубины с заранее заданной шкалой.",[PAPER,SURVEY],SIX),
trial("wall-test","Dark interior and bright borders | Тёмная полость и яркие границы",
"Biondi describes a dark room interior bounded by bright edges. | Бионди описывает тёмную полость с яркими краями.",
"track focus shape validate",LONG,
"At the King's room, wall-minus-center was negative on all three passes. Ranks were 1, 0 and 1 of 32. Queen ranks were 3, 23 and 27. Zero of six met the signed, rotated and baseline gates. | В камере царя стены на трёх съёмках были темнее центра. Ранги 1, 0 и 1 из 32. У камеры царицы 3, 23 и 27. Ни один из шести случаев не прошёл все критерии.",
"This planned-outline approximation failed. The author's original vertical cross-section was unavailable for direct comparison. | Этот тест горизонтального контура не прошёл. Исходного вертикального разреза автора для прямого сравнения нет.",
"Compare walls in the native numerical section against a registered independent survey. | Сопоставить стены на исходном численном разрезе с независимой геодезической привязкой.",["https://youtu.be/OK3bjfxLM9s?t=2056",SURVEY]),
trial("placebo","Let each neighbor train | Повторить подбор для каждого соседа",
"Could a nearby location achieve two transfers with the same training freedom? | Может ли соседняя точка пройти обе проверки при том же подборе параметров?",
"focus shape validate",LONG,
"Each of the 32 shifted King locations tried the same 36 recipes. Zero passed on both later long scenes. The survey position passed both. None of 12 randomized-phase images passed there. | Каждая из 32 соседних точек получила те же 36 вариантов. Ни одна не прошла обе длинные проверочные съёмки. Геодезическая точка прошла. На ней не прошёл ни один из 12 вариантов со случайной фазой.",
"The contrast depends on complex image structure. Surface scattering could produce such structure. The positions overlap. | Контраст зависит от комплексной структуры изображения. Её может создавать и поверхность. Соседние области перекрываются.",
"Repeat on independent sites with surveyed positives and negatives. | Повторить на других площадках с проверенными полостями и сплошной породой.",[GA,IG,SURVEY]),
trial("two-view-surface","Repeat visible surface locations | Найти повторяющиеся точки на поверхности",
"Two Capella views might select surface details that persist better than one view. | Два ракурса Capella могут лучше выделять устойчивые детали поверхности.",
"inputs shape validate",SCENES,
"Two-view picks matched ICEYE and at least one Umbra image within 8 m in 16/162 blocks. Single-view prominence and brightness gave 14/162 and 10/162. | Выбранные по двум ракурсам точки совпали с ICEYE и хотя бы одной Umbra в пределах 8 м в 16 из 162 блоков. По одному ракурсу получили 14 и 10 совпадений.",
"Some surface features repeated. The paired comparison did not establish an advantage over either single-view baseline. | Часть наземных деталей повторилась. Парное сравнение не подтвердило преимущества перед каждым из двух простых способов.",
"Evaluate the fixed selector in another landscape. This endpoint measures the surface. | Проверить выбранное правило на другом ландшафте. Этот критерий относится к поверхности.",[GA,UG,IG]),
trial("pulse-motion","Measure motion from individual pulses | Проверить движение по отдельным импульсам",
"Raw pulse phase should supply a stable Khafre motion series before assigning depth. | До перехода к глубине фаза импульсов должна дать устойчивый сигнал движения у Хафры.",
"inputs looks track validate",C+U[:2],
"Zero of eight Capella blocks passed the target phase gate. Zero of four short Umbra blocks passed. All 12 injected moving-point controls passed. | Ни один из восьми блоков Capella и четырёх коротких блоков Umbra не прошёл проверку фазы цели. Все 12 искусственно добавленных движущихся точек прошли.",
"Natural motion remained unresolved at Khafre in these blocks. Complete Capella phase-history files were verified; these fits used declared pulse subsets. | Естественное движение у Хафры в этих блоках не удалось выделить. Полные файлы истории фазы Capella проверены. Расчёт использовал указанные подмножества импульсов.",
"Measure a surveyed stable target and synchronize a surface-motion sensor during the pass. | Измерить известную устойчивую цель и синхронно записать наземные колебания.",[GA,UG,PATENT]),
trial("driven-motion","Recover a known surface tone | Восстановить известную наземную частоту",
"A radar spectral centroid should recover motion of an instrumented driven reflector. | По доплеровскому центроиду можно восстановить движение отражателя на вибростенде.",
"looks track validate",[],
"The primary seven-sample window gave 2.01 Hz for a 2 Hz drive and beat eight comparison locations. Ideal-response correction gave 5.98 mm/s RMS versus the 6.66 mm/s ground reference. | Основное окно из семи отсчётов дало 2,01 Гц при заданных 2 Гц и опередило восемь контрольных точек. После модельной поправки получилось 5,98 мм/с против наземных 6,66 мм/с.",
"A driven surface reflector supplies a positive motion check. No underground target was involved. | Испытание подтверждает измерение движения наземного отражателя. Подземной цели в опыте не было.",
"Run the same estimator against independently instrumented weaker targets. | Проверить тот же измеритель на более слабых целях с независимой записью движения.",[FIELD,"https://youtu.be/sQNjse68IM4?t=4338"]),
trial("directions","Withhold two archaeological directions | Скрыть направления двух подземных объектов",
"Radar imagery might predict known underground axes before the survey labels are opened. | Спутниковые данные могут предсказать направление подземного объекта до вскрытия плана.",
"inputs shape validate",[],
"El Osario cave missed its surveyed axis by 61.72°. Teotihuacan tunnel missed by 88°. Both exceeded the fixed 15° tolerance. Simple brightness missed by 35.84° and 89°. | Ошибка для пещеры Эль-Осарио составила 61,72°, для тоннеля Теотиуакана 88°. Обе больше допуска 15°. По обычной яркости ошибки были 35,84° и 89°.",
"Both orientation tests failed. Locations and monument names were known. El Osario used complex ICEYE, Teotihuacan a processed Umbra image. | Обе проверки направления провалены. Площадки и названия были известны. Для Эль-Осарио использовали комплексные данные ICEYE, для Теотиуакана обработанное изображение Umbra.",
"Use the same complex-image estimator at a new site and seal the survey before analysis. | Применить единый алгоритм к комплексным данным нового объекта и закрыть план до расчёта.",[CT,"https://doi.org/10.34946/D6J30S",TEO,"https://doi.org/10.1017/RDC.2016.77"]),
trial("older-location","Earlier 24-neighbor score | Более ранняя проверка по 24 соседям",
"Can a harmonic-window setting selected on the October King's position transfer to September? | Переносится ли выбранная по октябрьской точке камеры царя настройка гармонического окна на сентябрь?",
"looks track focus validate",C,
"The October P2/W25 winner beat 24/24 neighbors in training and 13/24 in September. This was a different 300-setting search, with different sites and controls. | Октябрьский вариант P2/W25 опередил 24 из 24 соседей при подборе и 13 из 24 в сентябре. Это другой поиск по 300 настройкам со своими точками и контролями.",
"The tuned October result failed to transfer at its original gate. Keep it distinct from the September-trained 36-recipe test. | Октябрьский результат не подтвердился по своему исходному критерию. Это отдельный тест от 36 вариантов с сентябрьской калибровкой.",
"Compare algorithms on one common predeclared unseen target. | Сопоставить методы на одной заранее зафиксированной новой цели.",[CANINI],"data/replication.json"),
trial("earlier-iceye","Earlier three-room ICEYE transfer | Ранняя проверка трёх комнат на ICEYE",
"Can the previously fixed harmonic score separate each room from every translation on X50? | Выделит ли ранее фиксированный гармонический показатель каждую комнату среди всех сдвигов на X50?",
"track focus validate",["iceye-20250602"],
"King, Queen and Subterranean beat 0, 27 and 9 of 32 positions. The exterior square beat 47/48. | Камеры царя, царицы и подземная превзошли 0, 27 и 9 из 32 соседей. Наружный контур превзошёл 47 из 48 сдвигов.",
"The three chamber locations missed that protocol's strict 32/32 gate. Its harmonic statistic differs from the new weighted complex filter. | Ни одна камера не прошла тот прежний порог 32 из 32. Гармонический показатель отличается от нового взвешенного комплексного фильтра.",
"Compare scores on further acquisitions under one fixed set of labels. | Сопоставить показатели на новых съёмках с единым набором меток.",[IG,CANINI,SURVEY]),
trial("quadratic","One oscillator versus smooth drift | Одна гармоника и плавный дрейф",
"A frozen depth-to-wavelength ratio should explain the second date better than ordinary smooth drift. | Фиксированное отношение глубины к длине волны должно описать второй пролёт лучше плавного дрейфа.",
"steer focus validate",C,
"The chosen oscillator reduced October residual power by 47.91%. A quadratic trend with the same count of fitted coefficients reduced it by 63.23%. Both compare with linear drift. | Выбранная гармоника уменьшила мощность октябрьского остатка на 47,91%. Квадратичный тренд с тем же числом коэффициентов дал 63,23%. Оба сравнивались с линейным дрейфом.",
"Smooth drift explains more of this observed trace. This single-component test used 24 neighbors and allowed a new complex amplitude per date. | Плавный дрейф лучше объясняет этот ряд. В одночастотной модели брали 24 соседние точки и свою комплексную амплитуду на каждый пролёт.",
"Predict a calibrated response without fitting a separate excitation for each observation. | Предсказать калиброванный отклик без отдельного подбора возбуждения для каждого пролёта.",[PAPER,CANINI]),
trial("line-average","Average adjacent section lines | Усреднить соседние линии разреза",
"Biondi says averaging adjacent lines reduces noise. Does that improve the repeated fit? | По словам Бионди, усреднение соседних линий уменьшает шум. Улучшает ли оно повторяемость?",
"track focus shape validate",C,
"One, three and five parallel-line choices produced no two-date chamber pass at the preset rule. On published cemetery lines, only one of three withheld lines had a nonzero value at the selected cell. | При одной, трёх и пяти линиях ни одна камера не прошла заданный критерий на обеих датах. На опубликованных линиях кладбища ненулевое значение прогнозной ячейки было в одной из трёх скрытых линий.",
"These two tests apply to different inputs. The cemetery values are already filtered output, with a supplied relative coordinate system. | Это два опыта на разных данных. Для кладбища имелся уже отфильтрованный результат с заданной относительной системой координат.",
"Request original unfiltered parallel lines with their physical spacing, direction and selection rule. | Получить исходные линии до фильтрации с расстояниями, направлениями и правилом отбора.",["https://youtu.be/NvQXmtcwHA8?t=10570",CEM]),
trial("depth-identifiability","Can the traces select deep over shallow? | Различают ли измерения малую и большую глубину?",
"The same hundred tracked observations might distinguish shallow from deep support. | Одни и те же сто измерений могли бы отличить малую глубину от большой.",
"steer focus validate",C,
"At 0.24 m wavelength, both a 0-200 m model and a disjoint 520-800 m model fit to relative residual below 5 × 10⁻¹⁴. Fitting either profile on one date predicted the other worse than zero. | При длине волны 0,24 м модели с диапазонами 0-200 м и 520-800 м обе дали относительную невязку ниже 5 × 10⁻¹⁴. При переносе с одной даты на другую обе уступили нулевому прогнозу.",
"The unrestricted complex profile is underdetermined in this model. A constrained, independently calibrated physical model may behave differently. | В этой модели свободный комплексный профиль недоопределён. Для ограниченной физической модели с независимой калибровкой результат может отличаться.",
"Use independently measured wave speed, mode and phase, then predict a depth withheld from fitting. | Независимо измерить скорость, тип волны и фазу, затем предсказать скрытую глубину.",[PAPER,PATENT]),
trial("gravity","Can measured gravity resolve the 648 m bracket? | Проверяют ли гравиметрические данные отметку 648 м?",
"The proposed missing rock should have a gravity signature measurable near Khafre. | Объём отсутствующей породы должен влиять на измеряемое поле тяжести у Хафры.",
"inputs steer validate",[],
"The nearest of 71 checked Egyptian gravity records was 5.83 km away. The benchmark shaft model predicts 0.044 µGal there, versus a 10 µGal reporting increment. | Ближайшая из 71 проверенной египетской гравиметрической точки находится в 5,83 км. Расчётный эффект модели шахт там 0,044 мкГал при шаге записи 10 мкГал.",
"This published sample cannot determine the shaft bottoms. The signed 648 m label is a published drawing dimension. | По этим опубликованным данным глубину шахт определить нельзя. Число 648 м нанесено на авторский чертёж.",
"Test a surveyed vertical return with an identifiable endpoint and an independent velocity measurement. | Проверить вертикальное отражение с привязанной конечной точкой и независимо измеренной скоростью.",[GROUND,DEEP])
]

def make_report():
    pairs = ["adjacent","lag8","fixed"]
    baselines = ["along","elevation"]
    wavelengths = [0.24,0.30,0.48]
    estimators = ["ordinary","whitened"]
    variants=[]
    for pairing,geometry,wavelength,estimator in itertools.product(pairs,baselines,wavelengths,estimators):
        recipe=[pairing,geometry,wavelength,estimator]
        key="/".join(map(str,recipe))
        variants.append(dict(id=key,pairing=pairing,geometry=geometry,wavelength_m=wavelength,estimator=estimator,
            selected=recipe==EXPECTED["selected"], ranks_against_32={SCENES[i]:EXPECTED["acquisitions"][day]["scores"][key] for i,day in enumerate(DATES[:3])}))
    assert len(variants)==36 and sum(int(r["selected"]) for r in variants)==1
    rows={x["id"]:dict(x) for x in tests}
    def mount(uid, asset_ids):
        rows[uid]["evidence_ids"]=asset_ids
    mount("directions",["osario-lidar","osario-iceye","teotihuacan-excavation","teotihuacan-umbra"])
    mount("gravity",["egypt-gravity","khafre-dimension"])
    mount("driven-motion",["glasgow-reflector"])
    mount("line-average",["published-yoshimura-lines"])
    mount("pulse-motion",["capella-cphd-sep","capella-cphd-oct","umbra-cphd-feb7","umbra-cphd-feb8"])
    companion={
        "wall-test":["line-average/border-20240916.json","line-average/border-20241004.json","line-average/border-20250602.json"],
        "placebo":["line-average/placebo.json"],"two-view-surface":["method-retest/scenes/results.json"],
        "pulse-motion":["method-retest/pulse/interpretation.json","method-retest/pulse/surface-check.json"],
        "driven-motion":["centroid/result.json"],"directions":["blind-cavity/osario/result.json","blind-cavity/teotihuacan/result.json"],
        "earlier-iceye":["blind-cavity/giza_transfer.json"],"depth-identifiability":["depth-audit/result.json"],
        "gravity":["ground-constraint/result.json"],"line-average":["line-average/result.json","line-average/published_result.json"]}
    for row in rows.values():
        row.setdefault("evidence_ids",[])
        row["receipts"]=["data/evidence/"+name for name in companion.get(row["id"],[])]
        if row["receipts"]:
            row["url"]=row["receipts"][0]
        for relative in [row["url"],*row["receipts"]]:
            assert (ROOT/relative).is_file(),relative
    external=[
       ("osario-lidar","El Osario cave scan","https://doi.org/10.34946/D6J30S"),
       ("osario-iceye","El Osario X31 complex radar scene",CT),
       ("teotihuacan-excavation","Teotihuacan independent tunnel survey","https://doi.org/10.1017/RDC.2016.77"),
       ("teotihuacan-umbra","Teotihuacan Umbra three-look image",TEO),
       ("egypt-gravity","NOAA Egypt gravity station table",GROUND),
       ("khafre-dimension","Khafre project dimensioned section",DEEP),
       ("glasgow-reflector","Driven reflector and instrument reference",FIELD),
       ("published-yoshimura-lines","Published filtered cemetery lines",CEM)]
    manifest=json.loads((REPLAY/"inputs.json").read_text())
    for uid,needle in [("capella-cphd-sep","20240916"),("capella-cphd-oct","20241004"),("umbra-cphd-feb7","2023-02-07"),("umbra-cphd-feb8","2023-02-08")]:
        src=next(x["url"] for x in manifest if needle in x["url"] and x["url"].endswith((".tif",".nitf")))
        if uid.startswith("capella"):
            src=src.replace("SLC_HH","CPHD_HH").replace(".tif",".cphd")
        else:
            src=src.replace("_SICD.nitf","_CPHD.cphd")
        external.append((uid,"Phase history "+needle,src))
    check_external={x[0] for x in external}
    for row in rows.values():
        assert set(row["stage_ids"])<=set(x["id"] for x in stages)
        assert set(row["scene_ids"])<=set(SCENES) and set(row["evidence_ids"])<=check_external
    stage_rows=[]
    for row in stages:
        refs=[x for x in rows.values() if row["id"] in x["stage_ids"]]
        stage_rows.append(dict(row,related=[x["id"] for x in refs],scene_ids=[i for i in SCENES if any(i in x["scene_ids"] for x in refs)]))
    quotes={
        "inputs":[PAPER,RETRACTION,GA,IG,UG],
        "looks":["https://youtu.be/ioRDPMeOymc?t=1529","https://opusmagnum.org/cracking-the-biondi-code-with-ai/",PATENT],
        "track":["https://youtu.be/SjJTRVgr9Mw?t=3397","https://youtu.be/SjJTRVgr9Mw?t=3324",CANINI],
        "steer":[PAPER,PATENT,"https://arxiv.org/abs/2208.00811","https://youtu.be/SjJTRVgr9Mw?t=4904"],
        "focus":["https://youtu.be/SjJTRVgr9Mw?t=2129",PAPER],
        "shape":[SURVEY,"https://youtu.be/OK3bjfxLM9s?t=2056"],"validate":[FIELD,TUNNEL,DEEP]}
    for row in stage_rows:
        row["sources"]=quotes[row["id"]]
    return dict(version=1,as_of="2026-11-27",stages=stage_rows,tests=list(rows.values()),
        independent_evidence=[dict(id=i,title=t,url=u) for i,t,u in external],
        execution=dict(source_level="Provider focused complex imagery",look_count=193,look_center_fraction=[0.25,0.75],
            look_width_fraction=0.5,look_taper="Hamming",pair_counts={"adjacent":192,"lag8":185,"fixed":192},
            coarse_patch_azimuth_range_px=[128,128],fine_patch_azimuth_range_px=[24,32],
            observable="Y = apparent azimuth shift in metres + i × apparent range shift in metres",
            steering="a = exp(i × 4π × B_perp × signed_height / (range × sin(incidence) × assumed_wavelength))",
            mean_removal="Subtract componentwise reference-ring median per pair, then center the time series and the steering vector.",
            normalized_score="abs(aᴴY)² / ((aᴴa) × (YᴴY)) after optional reference-covariance whitening",
            covariance_isotropic_shrinkage=0.25,reference_ring_radius_m=48,reference_ring_count=32,
            translated_radii_m=[8,16,24,32],bearings_per_radius=8,training_tie_break="largest rank, then largest median-absolute-deviation margin, then fixed enumeration",
            gate="At least 31 of 32 translated plans beaten and rank strictly greater than both apparent-motion RMS and full-image-power ranks.",
            free_height_search=dict(min_m=-44,max_m=44,step_m=.5,excluded_m=[0],reason="Zero gives a constant steering vector removed by centering."),
            chronological_analysis_order=[dict(step=1,role="select",scenes=[SCENES[0]],target="King +43 m"),
                dict(step=2,role="frozen across dates and chamber labels",scenes=SCENES[1:3],target="King / Queen / Subterranean"),
                dict(step=3,role="additional frozen short-aperture transfer after the first result",scenes=U,target="King / Queen / Subterranean")]),
        candidate_family=dict(count=len(variants),pairing=pairs,geometry=baselines,wavelength_m=wavelengths,estimator=estimators,
            selected=EXPECTED["selected"],train_scene=SCENES[0],train_site="King",assumed_floor_height_m=43,
            first_transfer_scenes=SCENES[1:3],followup_scenes=U,variants=variants),
        numerical_replay=dict(command="python tools/replay/run.py",guide="tools/replay/README.md",code="tools/replay/run.py",inputs="tools/replay/inputs.json",
            expected=SIX,companion_results=CONTROL,protocol="tools/replay/protocol.json",followup="tools/replay/umbra-protocol.json",
            source_paper=PAPER,retraction=RETRACTION,scene_order=SCENES,full_raw_remeasurement=True),
        next_test=dict(title="Predict a surveyed object before the reveal",ru_title="Дать прогноз до вскрытия геодезического плана",
            rule="Seal coordinates, signed depth, benchmark and uncertainty. Score once against the independent survey and matched intact material. Proposed tolerances are 10 m horizontally and the larger of 10 m or 10% vertically.",
            ru_rule="Зафиксировать координаты, знаковую глубину, высотный репер и погрешность. Сверить с независимым планом и проверенными участками сплошной породы. Предложенные допуски: 10 м по горизонтали и большее из 10 м или 10% по вертикали.",
            status="Proposed; no blind site and depth result is available.",ru_status="Предложено. Результата слепой проверки одновременно места и глубины пока нет.",
            necessary_inputs=["identified complex acquisition","metric pre-color section","registered line endpoints","ground benchmark","independent velocity or wavelength","untouched surveyed labels"]))
if __name__=="__main__":
    out=ROOT/"data"/"research.json"
    report=make_report()
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(f"{len(report['stages'])} stages, {len(report['tests'])} tests, {len(report['candidate_family']['variants'])} candidates")
