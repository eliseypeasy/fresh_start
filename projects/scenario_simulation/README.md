# Task Assignment Scenario Simulation — Methodology

This document explains the modelling choices behind the university inquiry
assignment scenario: what each model does, why it's built the way it is, what
the solver arguments mean, and what alternatives were considered and rejected.
It covers both the R (`ompr`/`ROI`/`glpk`) and Python (`PuLP`/`CBC`)
implementations.

*A Dutch translation follows the English section below.*

---

## English

### 1. The problem in plain terms

Ten university employees need to be assigned a week's worth of inquiries.
Each employee can only handle certain *types* of inquiry (their skill set),
some employees have a soft preference for particular types, and everyone has
a limited number of available hours once meetings, training, and research
commitments are subtracted. The question isn't just "who *can* do this task"
— it's "who *should*", given competing goals of honouring preference and
keeping workload fair.

This is a classic **assignment problem with side constraints**, and it's
solved here as a **Mixed Integer Linear Programming (MILP)** problem: every
employee–task pairing is a 0/1 decision, and the solver searches for the
combination of decisions that best satisfies an objective, subject to hard
constraints.

### 2. Model 1 — Preference-maximizing

**Goal:** assign every task to an eligible employee, maximizing the total
number of tasks that go to someone who prefers that task type.

**Decision variable:** `x[e,t] = 1` if employee `e` is assigned task `t`,
else `0`.

**Objective:** maximize `Σ pref[e,t] · x[e,t]` — sum the preference flag
over every assignment actually made. There's no reward for assigning
non-preferred tasks, so the solver will preferentially route tasks to
employees who want them, whenever that's still feasible.

**Constraints:**
- *Coverage*: every task is assigned to exactly one employee.
- *Eligibility*: an employee can only be assigned a task type they're
  qualified for (in Python this is enforced implicitly by only creating
  a variable for feasible pairs; in R it's enforced by an explicit
  `x[e,t] <= feasible_mat[e,t]` constraint).
- *Capacity*: an employee's total assigned hours can't exceed their
  available hours.

**What this model is good for:** understanding the *best case* for employee
satisfaction — if you only cared about preference, this is the ceiling.

**What it doesn't do:** say anything about fairness. It's entirely possible
for this model to load one popular, highly-preferred employee close to their
capacity limit while another sits comparatively idle, as long as coverage
and capacity constraints are still met.

### 3. Model 2 — Fairness (min-max)

**Goal:** assign every task to an eligible employee, minimizing the *most
loaded* employee's workload — i.e., flattening the peak rather than
optimizing any individual assignment.

**Decision variables:** the same `x[e,t]` binary as Model 1, plus a new
continuous variable `L`, representing "the workload of the busiest
employee."

**Objective:** minimize `L`.

**Constraints:** the same coverage, eligibility, and capacity constraints
as Model 1, *plus* one new constraint per employee: their assigned workload
must be `≤ L`. Because `L` is shared across everyone and the objective
pushes it down, the solver is forced to keep every employee's workload
below whatever the current best `L` is — which pushes the whole
distribution toward evenness.

**What this model is good for:** operational realism — this is closer to
what a manager actually wants on a busy week: no one buried, no one idle.

**What it doesn't do:** care about preference at all. Model 2 will happily
assign someone their least-favourite task type if it helps flatten the
workload curve.

### 4. Why two separate models instead of one

Preference-maximizing and workload-fairness are **competing objectives** —
improving one typically costs you some of the other. Running them
separately, rather than blending them into a single score, makes that
tension visible and *measurable*: the comparison charts show exactly how
much preference satisfaction you're trading for how much fairness, and vice
versa. That's a genuinely useful thing to be able to show a stakeholder:
"here is the cost of prioritizing fairness," in concrete numbers.

The alternative — combining both into one weighted objective — was
considered and rejected for now (see §6), because it hides that trade-off
behind an arbitrary weight instead of showing it directly.

### 5. Solver arguments explained

| Concept | R (`ompr` + `ROI.plugin.glpk`) | Python (`PuLP` + CBC) | What it controls |
|---|---|---|---|
| Solver choice | `with_ROI(solver = "glpk", ...)` | `PULP_CBC_CMD(...)` | Which underlying MILP solver actually does the branch-and-bound search. |
| Time limit | `tm_limit = 120000` (**milliseconds**) | `timeLimit = 120` (**seconds**) | Maximum wall-clock time before the solver stops and returns its best solution so far, even if not proven optimal. Units differ between the two — easy mistake to make when porting code. |
| Optimality gap | `mip_gap = 0.02` | `gapRel = 0.02` | Lets the solver stop once its current solution is provably within X% of the theoretical best, rather than grinding to exact optimality. Essential for the min-max fairness model, which has a weak LP relaxation and can otherwise run for a very long time. |
| Progress logging | `verbose = TRUE` | `msg = True` | Prints the solver's internal search progress to the console — useful for diagnosing a slow solve. |
| Variable type | `type = "binary"` | `cat = "Binary"` | Declares a 0/1 decision variable (an assignment either happens or it doesn't — no partial assignments). |
| Continuous variable | `type = "continuous", lb = 0` | `lowBound = 0, cat = "Continuous"` | Declares the `L` variable in Model 2 as a non-negative real number rather than an integer. |

### 6. Other approaches considered

These weren't used for this version of the project, but they're worth
knowing about — some are natural next steps if you want to extend this.

**Weighted single-objective model** (combine preference and fairness into
one objective, e.g. `maximize Σ pref·x − λ·L`). *Pro*: one solve instead of
two, and can land anywhere on the trade-off curve depending on `λ`. *Con*:
choosing `λ` is arbitrary — preference points and hours aren't naturally on
the same scale, so the "right" weight isn't obvious, and a stakeholder can't
easily audit what trade-off they're actually getting. Good next step once
you're comfortable with both models separately.

**Epsilon-constraint / Pareto frontier method** (systematically solve the
model many times, each time capping one objective at a different level and
optimizing the other). *Pro*: this is the mathematically rigorous way to
explore the full trade-off space, rather than picking one point on it or
one arbitrary weight. *Con*: requires many solver runs and more infrastructure
to manage and visualize — overkill for a first project, but a natural
extension once the two-model comparison here feels solid.

**Constraint Programming** (e.g. Google OR-Tools CP-SAT rather than MILP).
*Pro*: handles more complex, non-linear scheduling logic more naturally —
things like sequencing, time windows, or "employee A must finish before
employee B starts" are awkward to express as linear constraints but
straightforward in CP. Often faster on pure assignment problems too. *Con*:
a different modelling paradigm from the MILP/`lpSolve` tradition you already
know from R, so there's a learning cost. Worth trying once you want to add
scheduling logic (specific time slots, not just weekly totals).

**Greedy / rule-based heuristic assignment** (e.g., sort tasks by duration,
assign each to the least-loaded eligible employee). *Pro*: extremely fast,
transparent, and easy to explain to a non-technical audience with no solver
dependency at all. *Con*: no optimality guarantee — it can produce a clearly
worse outcome than either MILP model, and hard constraints (like capacity)
are easy to violate accidentally rather than enforced structurally. Useful
as a sanity-check baseline to compare the optimized models against, but not
a serious alternative on its own.

**Simulation / Monte Carlo stress-testing.** Not actually a competing
assignment method — this is complementary. Once you trust a chosen model,
running many randomized task-volume scenarios through it (varying the
`scenario_multiplier`) tells you how robust the assignment policy is to a
busier-than-usual week, rather than producing a single assignment itself.

### 7. Which tool each approach actually needs

Most of the alternatives above don't require new libraries at all — they
reuse the existing MILP solver stack with a different objective or a loop
wrapped around it. Only constraint programming genuinely steps outside the
current toolkit.

| Approach | What kind of tool it needs | R | Python | Relationship to the current models |
|---|---|---|---|---|
| **Preference-max / Fairness (min-max)** — current models | MILP solver | `ompr` + `ROI.plugin.glpk` | `PuLP` + CBC | The baseline used in this project. |
| **Weighted single-objective** | Same MILP solver, different objective | Same `ompr` + `ROI.plugin.glpk` — just change `set_objective()` to `pref·x − λ·L` | Same `PuLP` + CBC — just change the objective expression | No new tool at all — the same code with one line changed. Cheapest alternative to try next. |
| **Epsilon-constraint / Pareto frontier** | Same MILP solver, called repeatedly in a loop | Same stack, wrapped in `purrr::map()` over a range of bounds | Same stack, wrapped in a `for` loop over a range of bounds | Also no new tool — an orchestration pattern around the existing solver calls, not a different model. |
| **Constraint Programming** | A dedicated CP solver, different paradigm from MILP | No mature native option — would typically bridge to Python via `reticulate` | **Google OR-Tools, `cp_model` (CP-SAT solver)** | The one genuinely different toolset here, and the one branch where Python has a clear, mature option that R doesn't. |
| **Greedy / rule-based heuristic** | No solver — plain code | `dplyr::arrange()` + a loop, no optimization package | `pandas.sort_values()` + a loop, no optimization package | No solver needed — a reminder that not every version of this problem requires optimization machinery. |
| **Simulation / Monte Carlo** | Not a model — re-runs a chosen model many times | `purrr::map()` over many random seeds, re-solving the existing model each time | A loop over many random seeds, re-solving the existing model each time | Reuses whichever model (1 or 2) is preferred; doesn't replace it. |

**What this highlights about the current choice:** Models 1 and 2 are both
points on the same MILP branch of this tree, solved with the same solver
stack, just with different objectives — the flexibility to explore two
different goals came from the *formulation*, not from switching libraries.
The weighted-objective and epsilon-constraint alternatives stay on that
same branch, so they're the cheapest next experiments (no new packages
required). Constraint programming is the one branch that would actually
change the toolchain — and notably, it's a branch where Python currently
has the edge over R.

---

## Nederlands

### 1. Het probleem in gewone taal

Tien medewerkers van een universiteit moeten een week aan vragen
verwerken. Elke medewerker kan alleen bepaalde *typen* vragen behandelen
(hun vaardigheden), sommige medewerkers hebben een voorkeur voor bepaalde
typen, en iedereen heeft een beperkt aantal beschikbare uren nadat
vergaderingen, training en onderzoekstijd zijn afgetrokken. De vraag is niet
alleen "wie *kan* deze taak doen", maar "wie *zou* deze taak moeten doen",
gegeven de spanning tussen voorkeuren respecteren en de werklast eerlijk
verdelen.

Dit is een klassiek **toewijzingsprobleem met nevenvoorwaarden**, opgelost
als een **Mixed Integer Linear Programming (MILP)**-probleem: elke
combinatie van medewerker en taak is een 0/1-beslissing, en de solver zoekt
naar de combinatie van beslissingen die de doelfunctie het beste
optimaliseert, binnen de harde randvoorwaarden.

### 2. Model 1 — Voorkeur maximaliseren

**Doel:** wijs elke taak toe aan een bevoegde medewerker, en maximaliseer
het totale aantal taken dat terechtkomt bij iemand die dat taaktype
prefereert.

**Beslissingsvariabele:** `x[e,t] = 1` als medewerker `e` taak `t`
toegewezen krijgt, anders `0`.

**Doelfunctie:** maximaliseer `Σ pref[e,t] · x[e,t]` — de som van de
voorkeursindicator over alle daadwerkelijk gemaakte toewijzingen. Er is geen
beloning voor het toewijzen van niet-voorkeurstaken, dus de solver stuurt
taken bij voorkeur naar medewerkers die ze willen, zolang dat haalbaar
blijft.

**Randvoorwaarden:**
- *Dekking*: elke taak wordt aan precies één medewerker toegewezen.
- *Bevoegdheid*: een medewerker kan alleen een taaktype krijgen waarvoor
  hij/zij bevoegd is (in Python impliciet afgedwongen door alleen variabelen
  aan te maken voor haalbare combinaties; in R expliciet via de
  randvoorwaarde `x[e,t] <= feasible_mat[e,t]`).
- *Capaciteit*: de totale toegewezen uren van een medewerker mogen de
  beschikbare uren niet overschrijden.

**Waar dit model goed voor is:** het beste scenario voor medewerkers-
tevredenheid laten zien — als voorkeur het enige criterium was, is dit het
plafond.

**Wat het niet doet:** iets zeggen over eerlijkheid. Het is heel goed
mogelijk dat dit model één populaire, veel-geprefereerde medewerker tot
bijna de capaciteitsgrens belast, terwijl een ander relatief weinig te doen
heeft, zolang dekking en capaciteit maar gerespecteerd worden.

### 3. Model 2 — Eerlijkheid (min-max)

**Doel:** wijs elke taak toe aan een bevoegde medewerker, en minimaliseer de
werklast van de *zwaarst belaste* medewerker — dus de piek afvlakken in
plaats van individuele toewijzingen te optimaliseren.

**Beslissingsvariabelen:** dezelfde binaire `x[e,t]` als Model 1, plus een
nieuwe continue variabele `L`, die "de werklast van de drukste medewerker"
voorstelt.

**Doelfunctie:** minimaliseer `L`.

**Randvoorwaarden:** dezelfde dekkings-, bevoegdheids- en
capaciteitsvoorwaarden als Model 1, plus één nieuwe voorwaarde per
medewerker: hun toegewezen werklast moet `≤ L` zijn. Omdat `L` voor
iedereen gedeeld wordt en de doelfunctie deze omlaag drukt, wordt de solver
gedwongen om ieders werklast onder de huidige beste `L` te houden — wat de
hele verdeling richting gelijkmatigheid duwt.

**Waar dit model goed voor is:** operationele realiteit — dit ligt dichter
bij wat een manager in een drukke week daadwerkelijk wil: niemand
overbelast, niemand met te weinig werk.

**Wat het niet doet:** rekening houden met voorkeur. Model 2 wijst iemand
zonder probleem hun minst favoriete taaktype toe, als dat de werklastcurve
helpt afvlakken.

### 4. Waarom twee aparte modellen in plaats van één

Voorkeur maximaliseren en werklast eerlijk verdelen zijn **concurrerende
doelstellingen** — het verbeteren van de één kost meestal iets van de
ander. Door ze apart te draaien, in plaats van te combineren tot één score,
wordt die spanning zichtbaar en *meetbaar*: de vergelijkingsgrafieken laten
precies zien hoeveel voorkeurstevredenheid je inlevert voor hoeveel
eerlijkheid, en omgekeerd. Dat is iets concreets om aan een
belanghebbende te kunnen laten zien: "dit is de prijs van eerlijkheid
vooropstellen," in harde cijfers.

Het alternatief — beide combineren in één gewogen doelfunctie — is voor nu
overwogen en afgewezen (zie §6), omdat dat de afweging verbergt achter een
willekeurig gewicht in plaats van hem direct te tonen.

### 5. Uitleg van de solver-argumenten

| Concept | R (`ompr` + `ROI.plugin.glpk`) | Python (`PuLP` + CBC) | Wat het regelt |
|---|---|---|---|
| Keuze solver | `with_ROI(solver = "glpk", ...)` | `PULP_CBC_CMD(...)` | Welke onderliggende MILP-solver de branch-and-bound-zoektocht daadwerkelijk uitvoert. |
| Tijdslimiet | `tm_limit = 120000` (**milliseconden**) | `timeLimit = 120` (**seconden**) | Maximale rekentijd voordat de solver stopt en de beste tot dan toe gevonden oplossing teruggeeft, ook als optimaliteit niet bewezen is. De eenheden verschillen tussen de twee — een makkelijke fout bij het overzetten van code. |
| Optimaliteitsmarge | `mip_gap = 0.02` | `gapRel = 0.02` | Laat de solver stoppen zodra de huidige oplossing aantoonbaar binnen X% van het theoretische optimum zit, in plaats van door te rekenen tot exacte optimaliteit. Essentieel voor het min-max eerlijkheidsmodel, dat een zwakke LP-relaxatie heeft en anders zeer lang kan blijven rekenen. |
| Voortgangslog | `verbose = TRUE` | `msg = True` | Toont de interne voortgang van de solver in de console — nuttig om een trage oplossing te diagnosticeren. |
| Type variabele | `type = "binary"` | `cat = "Binary"` | Declareert een 0/1-beslissingsvariabele (een toewijzing gebeurt wel of niet — geen gedeeltelijke toewijzingen). |
| Continue variabele | `type = "continuous", lb = 0` | `lowBound = 0, cat = "Continuous"` | Declareert de `L`-variabele in Model 2 als een niet-negatief reëel getal in plaats van een geheel getal. |

### 6. Overwogen alternatieven

Deze zijn niet gebruikt in deze versie van het project, maar zijn de moeite
waard om te kennen — sommige zijn logische vervolgstappen als je dit project
wilt uitbreiden.

**Gewogen model met één doelfunctie** (voorkeur en eerlijkheid combineren
in één doelfunctie, bijv. `maximaliseer Σ pref·x − λ·L`). *Voordeel*: één
keer rekenen in plaats van twee, en kan overal op de afwegingscurve
uitkomen afhankelijk van `λ`. *Nadeel*: de keuze van `λ` is willekeurig —
voorkeurspunten en uren staan niet van nature op dezelfde schaal, dus het
"juiste" gewicht is niet vanzelfsprekend, en een belanghebbende kan
moeilijk controleren welke afweging er eigenlijk gemaakt wordt. Een goede
vervolgstap zodra je vertrouwd bent met beide modellen apart.

**Epsilon-constraint / Pareto-methode** (het model systematisch vele keren
oplossen, elke keer met een andere bovengrens op de ene doelfunctie, en de
andere optimaliseren). *Voordeel*: dit is de wiskundig meest rigoureuze
manier om de volledige afwegingsruimte te verkennen, in plaats van één punt
of één willekeurig gewicht te kiezen. *Nadeel*: vereist veel solver-runs en
meer infrastructuur om te beheren en te visualiseren — overkill voor een
eerste project, maar een logische uitbreiding zodra de vergelijking tussen
de twee modellen hier stevig aanvoelt.

**Constraint Programming** (bijv. Google OR-Tools CP-SAT in plaats van
MILP). *Voordeel*: gaat natuurlijker om met complexere, niet-lineaire
planningslogica — zaken als volgorde, tijdvensters, of "medewerker A moet
klaar zijn voordat medewerker B begint" zijn lastig als lineaire
randvoorwaarde te formuleren, maar eenvoudig in CP. Vaak ook sneller bij
zuivere toewijzingsproblemen. *Nadeel*: een ander modelleerparadigma dan de
MILP/`lpSolve`-traditie die je al kent uit R, dus er is een leercurve. De
moeite waard zodra je plannings­logica wilt toevoegen (specifieke
tijdsloten, niet alleen weektotalen).

**Greedy / regelgebaseerde heuristiek** (bijv. taken sorteren op duur en
elk toewijzen aan de minst belaste bevoegde medewerker). *Voordeel*: zeer
snel, transparant en gemakkelijk uit te leggen aan een niet-technisch
publiek, zonder afhankelijkheid van een solver. *Nadeel*: geen garantie op
optimaliteit — kan een duidelijk slechter resultaat opleveren dan beide
MILP-modellen, en harde randvoorwaarden (zoals capaciteit) worden eerder
per ongeluk overtreden dan structureel afgedwongen. Nuttig als
controle-basislijn om de geoptimaliseerde modellen tegen af te zetten, maar
geen serieus alternatief op zichzelf.

**Simulatie / Monte Carlo-stresstest.** Dit is geen concurrerende
toewijzingsmethode, maar een aanvulling. Zodra je een gekozen model
vertrouwt, laat het draaien van veel gerandomiseerde scenario's voor het
taakvolume (door de `scenario_multiplier` te variëren) zien hoe robuust het
toewijzingsbeleid is bij een drukkere-dan-normale week, in plaats van zelf
een toewijzing te produceren.

### 7. Welk gereedschap elke aanpak eigenlijk nodig heeft

De meeste alternatieven hierboven vereisen helemaal geen nieuwe library —
ze hergebruiken de bestaande MILP-solverstack met een andere doelfunctie of
een lus eromheen. Alleen constraint programming stapt echt buiten de
huidige toolkit.

| Aanpak | Welk type gereedschap nodig is | R | Python | Relatie tot de huidige modellen |
|---|---|---|---|---|
| **Voorkeur maximaliseren / Eerlijkheid (min-max)** — huidige modellen | MILP-solver | `ompr` + `ROI.plugin.glpk` | `PuLP` + CBC | De basislijn die in dit project gebruikt wordt. |
| **Gewogen model met één doelfunctie** | Dezelfde MILP-solver, andere doelfunctie | Dezelfde `ompr` + `ROI.plugin.glpk` — alleen `set_objective()` aanpassen naar `pref·x − λ·L` | Dezelfde `PuLP` + CBC — alleen de doelfunctie-expressie aanpassen | Geen nieuw gereedschap nodig — dezelfde code met één regel aangepast. Goedkoopste alternatief om als volgende te proberen. |
| **Epsilon-constraint / Pareto-methode** | Dezelfde MILP-solver, herhaaldelijk aangeroepen in een lus | Dezelfde stack, verpakt in `purrr::map()` over een reeks grenzen | Dezelfde stack, verpakt in een `for`-lus over een reeks grenzen | Ook geen nieuw gereedschap — een orkestratiepatroon rond de bestaande solver-aanroepen, geen ander model. |
| **Constraint Programming** | Een dedicated CP-solver, ander paradigma dan MILP | Geen volwassen native optie — meestal een brug naar Python via `reticulate` | **Google OR-Tools, `cp_model` (CP-SAT-solver)** | De enige echt andere toolset hier, en het enige onderdeel waar Python een duidelijke, volwassen optie heeft die R niet heeft. |
| **Greedy / regelgebaseerde heuristiek** | Geen solver — gewone code | `dplyr::arrange()` + een lus, geen optimalisatiepakket | `pandas.sort_values()` + een lus, geen optimalisatiepakket | Geen solver nodig — een herinnering dat niet elke versie van dit probleem optimalisatiemachinerie vereist. |
| **Simulatie / Monte Carlo** | Geen model — draait een gekozen model vele keren opnieuw | `purrr::map()` over veel willekeurige seeds, telkens het bestaande model opnieuw oplossend | Een lus over veel willekeurige seeds, telkens het bestaande model opnieuw oplossend | Hergebruikt welk model (1 of 2) dan ook de voorkeur heeft; vervangt het niet. |

**Wat dit zegt over de huidige keuze:** Model 1 en Model 2 zijn beide punten
op dezelfde MILP-tak van deze boom, opgelost met dezelfde solverstack, maar
met verschillende doelfuncties — de flexibiliteit om twee verschillende
doelen te verkennen kwam uit de *formulering*, niet uit het wisselen van
library. Het gewogen model en de epsilon-constraint-methode blijven op
dezelfde tak, dus zijn ze de goedkoopste volgende experimenten (geen nieuwe
packages nodig). Constraint programming is de enige tak die de toolchain
daadwerkelijk zou veranderen — en het is niet toevallig een tak waar Python
op dit moment de voorsprong heeft op R.
