# Sources — Flue-Cured Tobacco (Zimbabwe) Phase 1 Research

Bibliographic references for `research.md`. Citations are grouped by type and
tagged with the short inline key used in the research document
(e.g. `[FAO Tobacco Zimbabwe]`). Confidence on each source is noted where the
material was only available via search snippet (several primary PDFs returned
HTTP 403 to automated fetching and were used at abstract/snippet level — these
are flagged "snippet-level" and should be re-verified against the full text
before Phase 2 sign-off).

---

## 1. Internal / curated (treated as primary, already in codebase)

- **[Kutsaga Brochure 2023]** Tobacco Research Board (Kutsaga). *Kutsaga
  Tobacco Varieties 2023* (Variety brochure). Curated locally as
  `knowledge_data/tobacco_manual_kutsaga.json`. Original:
  https://www.kutsaga.co.zw/wp-content/uploads/2023/05/Variety-brochure-2023.pdf
  (PDF returned 403 to automated fetch; the curated JSON extract was used as the
  authoritative copy.) — Varieties K RK1, K30R, K35, KRK29 with ripening rate,
  yield class, quality style and disease-resistance codes.
- **[KurimaSense tobacco.py]** KurimaSense internal crop profile
  `crop_profiles/tobacco.py` (= `crop_knowledge.py` TOBACCO_PROFILE). Growth
  stages, fertiliser schedule, frog-eye disease profile, NR suitability,
  KRK26R/KRK75 style contrast.
- **[KurimaSense crop_constants.py]** KurimaSense `crop_constants.py` — tobacco
  base temp 10 °C, default yield 2.0 t/ha, water requirement 450 mm,
  transplanted-crop flag.
- **[KurimaSense yield_model.py]** KurimaSense `yield_model.py` —
  `NATURAL_REGION_MULTIPLIERS` (tobacco: I 1.15, II 1.0, IIa 1.0, IIb 0.95,
  III 0.8, IV 0.4, V 0.2) and the factor-based projection architecture this
  research must feed.

## 2. Government / parastatal

- **[TIMB]** Tobacco Industry and Marketing Board, Zimbabwe — official site and
  statistical/regulatory communications. https://www.timb.co.zw/ — grading
  system, contract registration, inspectorate, side-marketing enforcement.
- **[FAO Tobacco Zimbabwe]** FAO. *Issues in the Global Tobacco Economy —
  Selected Case Studies: 7. Tobacco in Zimbabwe* (y4997e).
  https://www.fao.org/4/y4997e/y4997e0k.htm — large-scale commercial vs
  communal yields, regional distribution, soils. (Snippet-level; full chapter to
  be re-read for Phase 2.)
- **[FAO Fertilizer Zimbabwe]** FAO. *Fertilizer use by crop in Zimbabwe*
  (a0395e). https://www.fao.org/4/a0395e/a0395e08.htm — national fertiliser-use
  context. (Snippet-level.)

## 3. Research station / industry technical

- **[Kutsaga Breeding]** Tobacco Research Board — Plant Breeding Division.
  https://www.kutsaga.co.zw/plant-breeding-division/ — variety development
  history; yield rise from ~600 kg/ha (1950s) to ~4,500 kg/ha hybrids
  (K RK66/K RK76). (Snippet-level via Newsday + Kutsaga site.)
- **[Newsday Kutsaga 2023]** Newsday Zimbabwe. *Kutsaga pushes for
  tobacco-resistant varieties* (2023).
  https://www.newsday.co.zw/business/article/200038141/ — KRK26 rapid ripening,
  KRK28 high yield, K RK66/K RK76 ~4,500 kg/ha, KE1 white-mould history.
- **[Magama 2016 / CORESTA AP39]** Magama et al. (2016). *A new Kutsaga tobacco
  variety (T75) acknowledged by growers as drought tolerant.* CORESTA Agronomy &
  Leaf Integrity AP39. https://www.coresta.org/abstracts/ (abstract 30126;
  PDF AP39) — T75 drought tolerance, yield stability across seasons/locations.
- **[Kutsaga TIPS / CORESTA]** Kutsaga. *Tobacco Improved Productivity Sites
  (TIPS): for improved productivity and leaf quality of the small-holder crop.*
  CORESTA abstract. https://www.coresta.org/abstracts/ — smallholder
  productivity/quality intervention context.
- **[Kutsaga Barns]** Tobacco Research Board. *Barns* technical sheet.
  https://www.kutsaga.co.zw/wp-content/uploads/2021/09/Barns.pdf (403 to fetch;
  referenced via curing literature below).
- **[Rocket/Counter-Current Barn]** CORESTA + African Journal of Agricultural
  Research / academia.edu: *In pursuit of greener curing methods: use of the
  rocket barn for tobacco curing in Zimbabwe* (CORESTA 27905);
  *Development of a low cost and energy efficient tobacco curing barn in
  Zimbabwe* (AJAR). Rocket barn ~50% wood saving vs conventional; Kutsaga
  Counter-Current 1 = 3.5 kg wood/kg cured vs 4.25 (rocket) / 5.32
  (conventional). (Snippet-level.)
- **[Granville Wilt Zimbabwe]** CORESTA. *Current situation of bacterial
  (Granville) wilt in Zimbabwe* (abstract 4972). Ralstonia solanacearum race 1
  biovar 1; managed via resistant cultivars; persistent in
  Mvurwi-Concession, Macheke/Headlands/Marondera, Burma Valley. (Snippet-level.)
- **[Black Shank-Fusarium complex]** *The Black Shank–Fusarium Wilt disease
  complex: an emerging threat to tobacco production in Zimbabwe* (Academia/
  AcadBiol). Emerging complex disease. (Snippet-level.)
- **[Superfert Tobacco]** Superfert / Windmill (Zimbabwe). Tobacco fertiliser
  product pages. https://www.fertilizer.co.zw/tobacco/ (403 to fetch) and
  Compound C 6:15:12+6S+0.1B product listing (Esaja). **Product-spec use only**
  (NPK analyses), not yield claims.
- **[Agricura 1ha Tobacco]** Agricura. *Production guidelines for 1 hectare of
  tobacco lands 2017.*
  https://agricura.co.zw/wp-content/uploads/2017/11/AGRICURA-1HA-TOBACCO-LANDS-2017.pdf
  (403 to fetch). **Product/program-spec use only.**
- **[Farmitagro 1ha Tobacco]** Farmitagro. *Tobacco production guidelines for 1
  hectare.* http://farmitagro.co.zw/files/FARMITAGRO1HA-TOBACCO.pdf.
  **Product/program-spec use only.**
- **[SQM Nutrition]** SQM Specialty Plant Nutrition. *Changing Zimbabwean
  tobacco growers' application to potassium nitrate topdressing.*
  https://sqmnutrition.com/en/essays/ — Kutsaga AN-topdressing convention;
  KNO3 not advocated. **Industry source; directional.**

## 4. Peer-reviewed / academic

- **[Masvongo 2013]** Masvongo, J., Mutambara, J., Zvinavashe, A. (2013).
  *Viability of tobacco production under smallholder farming sector in Mount
  Darwin District, Zimbabwe.* Journal of Development and Agricultural Economics
  5(8): 295-301. DOI 10.5897/JDAE12.128 — smallholder average yield
  **2,052 kg/ha** (2010/11), NR III. (Full PDF on journal mirror.)
- **[Svotwa 2012]** Svotwa, E., Masuka, A.J., Maasdorp, B., Murwira, A.,
  Shamudzarira, M. (2012). *Selection of Optimum Vegetative Indices for the
  Assessment of Tobacco Float Seedlings Response to Fertilizer Management.* ISRN
  / International Scholarly Research Notices, Article 450473.
  https://www.hindawi.com/journals/isrn/2012/450473/ — SRI r²=0.905 vs NDVI
  r²=0.819 for seedling fertiliser response.
- **[Svotwa 2013a]** Svotwa, E. et al. (2013). *Remote Sensing Applications in
  Tobacco Yield Estimation and the Recommended Research in Zimbabwe.* ISRN,
  Article 941873. https://onlinelibrary.wiley.com/doi/10.1155/2013/941873 —
  review of RS for tobacco yield; explicit "recommended research" agenda
  (i.e., documents the research gap).
- **[Svotwa 2013b]** Svotwa, E. et al. (2013). *Tobacco canopy spectral
  characteristics and biomass* (ISRN 816767).
  https://www.hindawi.com/journals/isrn/2013/816767/ — NDVI vs biomass/total-N;
  staggered Sep/Oct/Nov/Dec plantings; max NDVI and NDVI-mass r² both decline
  with later planting.
- **[Svotwa 2017]** Svotwa, E. et al. (2017). *Assessing flue-cured tobacco crop
  growth and biomass response to nitrogen application levels using canopy
  reflectance.* (ResearchGate 319310295.) — canopy reflectance / NDVI rises with
  N rate. (Snippet-level; full PDF 403.)
- **[Tobacco Crop Area RS 2018]** *Estimating Tobacco Crop Area and Yield in
  Zimbabwe Using Operational Remote Sensing and Statistical Techniques* (2018,
  ResearchGate 325119890). — operational RS area+yield estimation for Zimbabwe
  tobacco. (Snippet-level.)
- **[Breeding Review]** *Breeding for Yield, Quality and Associated Traits in the
  Zimbabwean Flue-Cured Tobacco (Nicotiana tabacum L.): A Review* (Academia.edu
  70824032). — synthesis of TRB breeding objectives and trait genetics.
  (Snippet-level.)
- **[Marowa 2015]** Marowa, P., Mtaita, T., Dzingai, T., Rukuni (2015). *Effect
  of Leaf Priming Removal Level and Fertilization Rate on Yield of Tobacco in
  Zimbabwe.* Greener Journal of Agricultural Sciences.
  https://gjournals.org/GJAS/Publication/2015/February/HTML/091614361%20Marowa%20et%20al.htm
  — priming x fertiliser x yield interaction.
- **[Land Reform Tobacco 2022]** *Tobacco Farming Following Land Reform in
  Zimbabwe: A New Dynamic of Social Differentiation and Accumulation.* Journal of
  Southern African Studies (2022).
  https://www.tandfonline.com/doi/full/10.1080/03057070.2022.2030954 — structure
  of contract farming, smallholderisation of the crop. (Snippet-level.)
- **[Manicaland Debt 2021]** *Tobacco farming and current debt status among
  smallholder farmers in Manicaland province in Zimbabwe.* PMC7611881.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7611881/ — contract debt dynamics
  (side-marketing incentive context). (Snippet-level.)

## 5. Industry / trade press (side-marketing & sector context)

- **[Newsday US$57m 2022]** Newsday Zimbabwe. *US$57m tobacco lost to side
  marketing* (July 2022). https://www.newsday.co.zw/2022/07/us57m-tobacco-lost-to-side-marketing/
  — TIMB estimate of ~US$57m lost (2021); exact annual loss not precisely
  ascertainable.
- **[Tobacco Reporter 2022]** Tobacco Reporter. *TIMB Vows Crackdown on Side
  Marketing in Zimbabwe* (July 2022).
  https://tobaccoreporter.com/2022/07/12/timb-vows-crackdown-on-side-marketing-in-zimbabwe/
- **[Newsday Contract Fuelling]** Newsday Zimbabwe. *How contracted farmers are
  fuelling side marketing.* https://www.newsday.co.zw/agriculture/article/200036052/
- **[EquityAxis SideMkt 2023]** EquityAxis. *Zimbabwe's Tobacco Industry Under
  Threat: Growers Suspected of Side Marketing* (2023).
  https://equityaxis.net/index.php/post/17365/ — ~95% of crop under contract;
  inspectorate (2021); GIS field-marking; ~550 grower numbers suspended.
- **[EquityAxis Season 2025]** EquityAxis. *Tobacco Marketing Season Kicks Off…*
  (2025). https://equityaxis.net/post/18300/ — current marketing-season figures.
- **[allAfrica 2009]** allAfrica. *Zimbabwe: Side-Marketing Threatens Contract
  Farming's Future* (2009). https://allafrica.com/stories/200907200048.html —
  long-standing nature of the problem.
- **[Newsday NCV Matabeleland]** Newsday. *NCV tobacco sparks agricultural
  transformation in Matabeleland.*
  https://www.newsday.co.zw/local-news/article/200051719/ — tobacco expansion
  into NR IV.

## 5b. Agronomic spacing / population (added Phase 2, gap-(a) amendment)

- **[Kutsaga Spacing Trial]** Kutsaga Research Station field experiments using
  **1.2 m between rows × 0.56 m in-row** spacing for flue-cured tobacco (≈14,881
  plants/ha). Referenced via Marowa et al. and CORESTA/Kutsaga trial methodology.
  Used to ground variety plant-population ranges.
- **[Britannica Tobacco]** Encyclopædia Britannica, *common tobacco (Nicotiana
  tabacum)* — Orinoco flue-cured strains grown in rows ~1.2 m apart, plants
  50–60 cm in-row (≈14,800–16,700 plants/ha).
  https://www.britannica.com/plant/common-tobacco — general spacing corroboration
  (tertiary source; used only for the spacing/population standard, not yields).

## 6. Classification reference

- **[Vincent & Thomas 1960]** Vincent, V. & Thomas, R.G. (1960). *An Agricultural
  Survey of Southern Rhodesia: Part I Agro-Ecological Survey.* — the original
  Natural Regions I–V definition still used by Zimbabwe (rainfall bands and
  farming-system suitability). Standard reference; reflected in
  `crop_profiles/_base.py` NaturalRegion enum.

---

### Source-quality summary

| Tier | Use | Examples |
|------|-----|----------|
| Strong (peer-reviewed / parastatal) | Quantitative claims | Masvongo 2013, Svotwa 2012/2013, FAO, TIMB |
| Solid (research station / CORESTA) | Variety & agronomy | Kutsaga brochure, CORESTA abstracts |
| Directional (trade press) | Sector dynamics, side-marketing | Newsday, Tobacco Reporter, EquityAxis |
| Spec-only (input suppliers) | Product NPK/rates ONLY | Superfert, Agricura, Farmitagro, SQM |

Snippet-level sources (full text returned 403 to automated retrieval) are
flagged above and listed again in `research.md` Section 9 for full-text
verification before Phase 2.
