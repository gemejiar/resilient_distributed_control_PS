# STED Decision Log

STATUS: PENDING_COMPLETION

Use one entry per gate evaluation, phase transition, or integrator-level decision.

## Decision Entry Template

```markdown
## DEC-XXX
Date:
Gate:
Decision:
Justification:
Evidence reviewed:
Blockers or limitations:
Responsible:
Status:
Next action:
```

## DEC-001
Date: 2026-05-19
Gate: G0
Decision: Lean core initialized
Justification: Convert repository from project snapshot to reusable template
Evidence reviewed: User instruction
Blockers or limitations: Template still requires alignment work between live artifacts and Lean contracts
Responsible: Integrator
Status: passed_with_caveats
Next action: Keep logging structural changes and gate decisions with this template

## DEC-002
Date: 2026-05-19
Gate: G0
Decision: Require structured gate decisions in live integrator contracts and templates
Justification: The Lean specification already requires gate registration, but the live repository artifacts did not make the per-gate structure explicit enough for auditability
Evidence reviewed: STED-RW_Lean.md sections on gate rules and final quality report, `.agents/orchestrator.md`, `.claude/agents/sted_integrator.md`, previous `decision_log.md`, and `final_quality_report.md`
Blockers or limitations: Existing project instantiations may still carry older free-form or tabular decision logs
Responsible: Integrator
Status: passed
Next action: Use this structure for all future gate evaluations and mirror gate status in `final_quality_report.md`

## DEC-003
Date: 2026-05-31
Gate: G0 → G1
Decision: El proyecto se transforma de una revisión de modelado data-driven (paper previo) a un estudio experimental EMT sobre asistencia angular wide-area suave para inversores GFL coordinados con BESS-GFM.
Justification: El usuario instruyó explícitamente la transformación del proyecto. El paper anterior en paper/main.tex era un review sobre data-driven dynamic modeling, incompatible con el nuevo objetivo. El nuevo objetivo es original, defensible y diferenciado del paper base (Wide Area Control of Inverter Based Power Grids).
Evidence reviewed: AGENTS.md, CLAUDE.md, STED-RW_Lean.md, paper/main.tex (paper anterior), instrucción del usuario del 2026-05-31
Blockers or limitations: paper/main.tex contiene contenido del paper anterior; se preserva la clase LaTeX y preamble; el contenido de secciones científicas debe ser reemplazado gradualmente con trazabilidad.
Responsible: STED-RW Integrator
Status: passed
Next action: Crear plan_maestro.md, gap_matrix.md, contribution_matrix.md; obtener aprobación de G1 del usuario.

## DEC-004
Date: 2026-05-31
Gate: G1
Decision: El proyecto NO será una réplica directa del método WGFL/WGFM del paper base.
Justification: La conmutación dura del ángulo PLL usada en el paper base genera transitorios artificiales. Nuestra contribución central es evaluar una alternativa suave que evita esa conmutación, usando corrección de velocidad angular gradual con factor λg.
Evidence reviewed: plan_maestro.md sección 2 (decisión científica central); gap_matrix.md (bloque de brecha específica)
Blockers or limitations: Ninguno — decisión de alcance.
Responsible: STED-RW Integrator
Status: passed
Next action: Mantener el método de conmutación dura solo como baseline C2 para comparación.

## DEC-005
Date: 2026-05-31
Gate: G1
Decision: La contribución central será asistencia angular suave para GFL, no una nueva arquitectura de BESS ni un nuevo esquema de control GFM.
Justification: El BESS-GFM actúa como ancla dinámica (componente de soporte), pero la novedad metodológica está en la corrección suave del ángulo de referencia del GFL y en el protocolo comparativo EMT.
Evidence reviewed: plan_maestro.md sección 4 (contribuciones); contribution_matrix.md (C1 como contribución principal)
Blockers or limitations: Ninguno.
Responsible: STED-RW Integrator
Status: passed
Next action: Asegurar que la descripción del BESS-GFM en el manuscrito no reclame novedad en el diseño del GFM.

## DEC-006
Date: 2026-05-31
Gate: G1
Decision: El BESS-GFM es el ancla dinámica del sistema; el diseño del control de droop o VSM del BESS se documenta como contexto, no como contribución principal.
Justification: La contribución central es la asistencia angular suave del GFL. El BESS-GFM es un elemento necesario de la arquitectura pero su diseño de control es estándar (droop P-ω o VSM) y no es novedoso en sí mismo.
Evidence reviewed: plan_maestro.md sección 6 (arquitectura experimental); contribution_matrix.md (C2: coordinación como condición, no como fin)
Blockers or limitations: Si el BESS-GFM usa una estructura de control no estándar, debe registrarse como contribución adicional con evidencia.
Responsible: STED-RW Integrator
Status: passed
Next action: Definir en el modelo Simulink si BESS-GFM usa droop o VSM; registrar en plan_maestro.md.

## DEC-007
Date: 2026-05-31
Gate: G1
Decision: La validación es EMT en Simulink únicamente; no se incluye HIL, PHIL ni experimental física en este trabajo, salvo que exista evidencia adicional autorizada por el usuario.
Justification: El alcance del proyecto no incluye laboratorio ni equipamiento de HIL. La contribución metodológica es válida como estudio EMT documentando explícitamente esta limitación.
Evidence reviewed: plan_maestro.md sección 3 (alcance — excluye HIL/PHIL); contribution_matrix.md (C3: condición de validez)
Blockers or limitations: El claim CLM-004 y otros deben evitar el término "experimental validation"; usar "EMT simulation study".
Responsible: STED-RW Integrator
Status: passed
Next action: Verificar que paper/main.tex no use "experimental validation" para referirse a la simulación EMT.

## DEC-008
Date: 2026-05-31
Gate: G1
Decision: Los claims de generalización quedan prohibidos hasta tener más de un sistema de prueba. La conmutación dura se usa solo como baseline comparativo (C2).
Justification: Con un solo sistema de prueba (IEEE 14 modificado), no es posible afirmar generalización. La conmutación dura tipo paper base se incluye solo para cuantificar la diferencia de transitorios, no como método recomendado.
Evidence reviewed: plan_maestro.md sección 5 (claims prohibidos); contribution_matrix.md (C1: condición de validez)
Blockers or limitations: Si en el futuro se agrega un segundo sistema de prueba, se puede relajar esta restricción previa decisión del integrador.
Responsible: STED-RW Integrator
Status: passed
Next action: Asegurar que conclusions no contengan frases del tipo "generalizes to any IBR-dominated grid" o "applicable to all power systems".

## DEC-009
Date: 2026-05-31
Gate: G1
Decision: El BESS ya no se asume exclusivamente GFM. Cada BESS tiene una planta DC/SoC común y puede instanciarse con dos interfaces AC: GFL (fuente de corriente con PLL) o GFM (fuente de tensión/frecuencia con droop/VSM).
Justification: La formulación "BESS-GFM únicamente" mezcla el efecto del modo de operación con el efecto de la asistencia angular. Separar los dos permite un diseño experimental limpio con tres efectos independientes: modo BESS, asistencia angular y coordinación wide-area.
Evidence reviewed: instrucción del usuario 2026-05-31; plan_maestro.md sección 2
Blockers or limitations: El modelo Simulink debe implementar ambas interfaces sobre la misma planta DC/SoC. Decidir si droop o VSM es la implementación GFM base (a registrar en DEC posterior).
Responsible: STED-RW Integrator
Status: passed
Next action: Actualizar plan_maestro.md, main.tex y contribution_matrix.md con nueva formulación.

## DEC-010
Date: 2026-05-31
Gate: G1
Decision: La planta DC/SoC del BESS es un módulo común compartido por GFL y GFM. La interfaz AC (GFL o GFM) se selecciona por caso de simulación. La planta incluye: modelo de batería, condensador Cdc, evolución de SoC, límites Imax, saturación de P/Q y anti-windup.
Justification: La separación planta/interfaz es el eje arquitectónico central del paper. Sin ella, no es posible comparar GFL vs GFM bajo idénticas condiciones de energía, corriente y tensión DC.
Evidence reviewed: instrucción del usuario 2026-05-31
Blockers or limitations: Verificar que el modelo Simulink implementa esta separación antes de G3.
Responsible: STED-RW Integrator
Status: passed
Next action: Registrar en test plan T-MODE-001: verificar que cada BESS tiene exactamente un modo por caso.

## DEC-011
Date: 2026-05-31
Gate: G1
Decision: El paper compara tres configuraciones de BESS: BESS-GFL (fuente de corriente con asistencia angular suave), BESS-GFM (fuente de tensión/frecuencia con damping regional), y configuración mixta (al menos un BESS-GFL + al menos un BESS-GFM).
Justification: Esta comparación es el experimento central que permite atribuir diferencias de desempeño al modo BESS, no a la asistencia angular ni a la coordinación wide-area.
Evidence reviewed: instrucción del usuario 2026-05-31; gap_matrix.md
Blockers or limitations: Requiere al menos dos BESS en el modelo Simulink, o un BESS parametrizable.
Responsible: STED-RW Integrator
Status: passed
Next action: Incluir caso C6 (mixed BESS-GFL + BESS-GFM) en la matriz de casos.

## DEC-012
Date: 2026-05-31
Gate: G1
Decision: La asistencia angular suave (ωg^a, θg^a, λg) aplica únicamente a recursos que operan en modo GFL, es decir, a los miembros de I_GFL. Los recursos GFM (I_GFM) no reciben asistencia angular vía PLL porque no usan PLL como referencia primaria de sincronización.
Justification: Aplicar asistencia angular a un GFM crearía circularidad: el GFM ya impone la referencia de tensión/frecuencia que usa el PDC para calcular Ωc. La asistencia GFL solo tiene sentido donde el PLL es el elemento de sincronización.
Evidence reviewed: instrucción del usuario 2026-05-31; análisis de circularidades
Blockers or limitations: Verificar en T-MODE-002 y T-MODE-003 que ningún recurso GFM recibe asistencia angular y ningún recurso GFL usa GFM internamente.
Responsible: STED-RW Integrator
Status: passed
Next action: Agregar condición explícita en metodología: "g ∈ I_GFL" en la ecuación de ωg^a.

## DEC-013
Date: 2026-05-31
Gate: G1
Decision: Ωc se calcula exclusivamente desde las mediciones PMU (buses en M). No se calcula desde θg^a ni desde señales de control modificadas. Esta regla previene circularidades algebraicas en el lazo wide-area.
Justification: Si Ωc dependiera de θg^a y θg^a dependiera de Ωc, el lazo sería algebraicamente circular y no causalmente realizable. La separación PMU → PDC → Ωc → θg^a → inversor garantiza causalidad.
Evidence reviewed: análisis de circularidades (Tarea 17 de la instrucción del usuario); instrucción 2026-05-31
Blockers or limitations: En Simulink, asegurar que el bloque PDC usa exclusivamente señales de medición, no de control. Verificar con T-MODE-004.
Responsible: STED-RW Integrator
Status: passed
Next action: Agregar nota explícita en manuscrito: "Ωc is computed from measured PMU quantities only."

## DEC-014
Date: 2026-05-31
Gate: G1 → G3
Decision: Mathematical audit of main.tex methodology — 15 problems identified and corrected.
Justification: The methodology had undefined variables, dimensional inconsistencies, an algebraic loop in BESS-GFM, instantaneous fallback (not bumpless), missing current-reference conversion, and incomplete metric definitions. Correcting these is required before the Simulink model can be built without ambiguity.
Evidence reviewed: paper/main.tex (pre-correction); instrucción del usuario 2026-05-31 (mathematical audit specification)
Blockers or limitations: BESS-GFM implemented as droop filtered (Option A). VSM noted as alternative. Decision must be confirmed when Simulink model is defined before G3.
Responsible: STED-RW Integrator
Status: passed
Next action: Verify corrected equations against Simulink blocks before G3.

## MATH_AUDIT_TABLE — Ecuaciones auditadas (DEC-014)

| Eq. | Variable principal | Problema detectado | Tipo | Corrección aplicada |
|---|---|---|---|---|
| sets (eq 1-3) | I, I_GFL, I_GFM | Faltaba la partición completa I = I_GFL ∪ I_GFM con I_GFL ∩ I_GFM = ∅ | UNDEFINED_VARIABLE | Agregadas ecuaciones de partición completa |
| PMU (old eq) | V_dc, SoC | PMU no mide Vdc ni SoC — son telemetría local del BESS | TEXT_EQUATION_MISMATCH | Separado en y^PMU (phasors) y y^loc (P,Q,I,Vdc,SoC) |
| quality (old eq 6) | V_0 | V_0 undefined en peso de calidad; mezcla unidades SI y p.u. | UNDEFINED_VARIABLE | Reemplazado por ||V_m|-1| en p.u. |
| Φ_c (old eq phi_c) | Φ_c | Integral continua sin condición inicial ni wrap | MISSING_INITIAL_CONDITION | Reemplazado por integración discreta con wrap_{2π} e IC de promedio circular |
| R_c | R_c | RoCoF regional usado en BESS-GFL FFR sin definición de filtro | UNDEFINED_SIGNAL | Agregado filtro discreto exponencial R_c(k) = a_R R_c(k-1) + (1-a_R)ΔΩ_c/T_p |
| delayed signals | Φ^d_c,g, R^d_c,g | Solo Ω^d_c estaba definida; Φ^d_c y R^d_c usadas sin definición | UNDEFINED_SIGNAL | Definidas las tres señales retardadas para x ∈ I_GFL ∪ I_GFM |
| DC model (eq vdc) | P_bat, P_inv | i_bat y i_inv no conectados a potencia; convención de signo incompleta | INCONSISTENT_SIGN_CONVENTION | Agregadas P_bat = V_dc·i_bat, P_inv ≈ P_b,ac; convención P>0 explícita |
| SoC (eq soc) | E_nom | E_nom sin unidades declaradas; eficiencia ausente | DIMENSIONAL_AMBIGUITY | Especificado E_nom en Joules; eficiencia en P_bat con P_b,ac > 0 / < 0 |
| SoC limits | P^ch_max | Solo límite de descarga; límite de carga ausente | MISSING_SATURATION | Agregado P^ch_max(SoC) simétrico; restricción bilateral en P*_b |
| BESS-GFL (eq bess_gfl) | i*_d, i*_q | P* no convertido a referencias de corriente; sin limitación | NOT_IMPLEMENTABLE_IN_EMT | Agregada conversión P*,Q* → i*_d,i*_q estándar + escalado proporcional Imax |
| BESS-GFM (eq droop_p) | ω_b | ω_b aparece en ambos lados: ω_b = f(ω_b) — lazo algebraico | ALGEBRAIC_LOOP_RISK | Reemplazado por droop filtrado: ω^dr separado de ω_b con dinámica T_ω |
| angular assist (eq 17) | K_θ,g | K_θ,g dimensionalmente inconsistente (debería ser s^-1, no adimensional) | DIMENSIONAL_AMBIGUITY | Declarado K_θ,g en s^-1; agregado θ^a(k) con wrap_{2π} e IC θ^a(0)=θ̂_g(0) |
| severity (eq 19) | f_g | Índice usa f_g en Hz pero ω̂_g en rad/s — mezcla dimensional | DIMENSIONAL_AMBIGUITY | Reemplazado por Δω_g = ω̂_g - ω_0 en rad/s y ρ_g (RoCoF local filtrado) en rad/s² |
| fallback (eq lambda_eff) | λ^e_g = η_g·λ_g | Multiplica λ directamente → caída instantánea cuando η=0 (no bumpless) | NOT_IMPLEMENTABLE_IN_EMT | Reformulado: s^e_g = η_g·s_g; dinámica aplicada sobre λ^e_g con τ_off lento |
| metrics | f_min, RoCoF_max | Métricas sin fórmula reproducible; f_ref no definida | UNDEFINED_SIGNAL | Agregadas definiciones reproducibles: f_min, RoCoF_max, e^max_θ, E^FFR, T_sat |

## DEC-015
Date: 2026-05-31
Gate: G1->G3
Decision: BESS electrochemical/converter model updated to physical consistency: P_in/P_out SoC, V_oc(s) battery terminal, explicit DC-link balance, amplitude-invariant p/q (no 3/2), cross-saturation with active priority.
Justification: Seven model inconsistencies corrected using reference paper "Multi-agent hierarchical consensus...cooperative battery storage units".
Evidence reviewed: instruction 2026-05-31; main.tex pre-correction; referenced paper.
Blockers or limitations: p/q convention must be confirmed against Simulink current controller before G3.
Responsible: STED-RW Integrator
Status: passed
Next action: Verify p/q convention in Simulink before G3. Register if different from amplitude-invariant.

Decisions adopted (DEC-015):
1. SoC: P_in/P_out non-negative, ds/dt = (1/E_nom)[eta_c P_in - (1/eta_d) P_out]
2. V_bat = V_oc(s) - R_b I_bat; V_oc(s) as LUT or linear function
3. DC-link: explicit capacitor (Option B for EMT); V_bat != V_dc unless direct coupling
4. p/q: amplitude-invariant (no 3/2); P*/Q* -> i*_dq uses 1/D_v
5. Cross-saturation active priority: i*_d preserved to I_max, i*_q uses headroom
6. Same DC/SoC/current model for GFL and GFM (confirmed)
7. Historical effort sigma as secondary metric only

## DEC-016
Date: 2026-05-31
Gate: G1->G3
Decision: 7 targeted math corrections applied: (1) subsection renamed to "Power Bases..." + explicit p.u. declaration for all control gains; (2-6) already done in DEC-015; (7) hard-switch binary sigma_g with hysteresis replaces continuous s_g=0/1 which was mathematically undefined.
Justification: s_g is continuous in [0,1]; using it as a binary threshold for hard-switching was undefined for intermediate values. sigma_g is a proper hysteretic relay.
Evidence reviewed: instructions 2026-05-31; main.tex pre-correction.
Responsible: STED-RW Integrator
Status: passed
Next action: Verify h_zeta value and confirm sigma_g implementation in Simulink before G3.

## DEC-BIB-001
Date: 2026-05-31
Gate: G2
Decision: Removed PENDING_VERIFICATION text from the `note` field of all 8 PENDING_VERIFICATION entries in paper/biblio_paper.bib. Status tracking moved to %%-comments above each entry.
Justification: The cas-model2-names bibliography style renders the `note` field in the compiled PDF. Having "PENDING_VERIFICATION." and multi-line instructions in `note` caused that text to appear literally in the bibliography output of the draft. This is an editorial artifact, not a scientific problem. The verification status is now tracked only in comments, which do not render.
Evidence reviewed: paper/biblio_paper.bib (all Section A entries); paper/main.tex (identified 3 cited PENDING entries: mahish2025wideareacontrol, hong2020wamc_ffr, mitsugi2021bess_ffr_chil). All PDFs in paper/core_refs/ are password-protected; no DOI/volume/pages could be confirmed at this time.
Blockers or limitations: All 3 cited PENDING entries subsequently verified via CrossRef API (same session, 2026-05-31). See confirmed data below.
Responsible: STED-RW Integrator
Status: passed
Next action: Cross-check volume/pages against author PDFs when unlocked (optional pre-submission sanity check). Remaining 5 non-cited PENDING entries (A3,A5,A6,A7,A8) to be verified when cited.

Confirmed bibliographic data (CrossRef, 2026-05-31) — all 8 Section A entries:
- mahish2025wideareacontrol: Priyatosh Mahish, Pratim Kundu, Sukumar Mishra. IEEE Trans. Sustain. Energy, vol.16, no.2, pp.852-865, 2025. DOI: 10.1109/tste.2024.3486608
- hong2020wamc_ffr: Qiteng Hong et al. (10 authors). IEEE Trans. Smart Grid, vol.11, no.4, pp.3394-3404, 2020. DOI: 10.1109/tsg.2019.2963796
- shi2023rocof_estimator: Wenshuai Shi, Jingrong Yu, Ying Guo. IEEE Trans. Power Syst., 2022, early access pp.1-14, no volume/issue in CrossRef. DOI: 10.1109/tpwrs.2022.3205171
- mitsugi2021bess_ffr_chil: Yasuaki Mitsugi et al. (6 authors). IEEE Trans. Ind. Appl., vol.57, no.6, pp.5541-5551, 2021. DOI: 10.1109/tia.2021.3107223
- he2025bess_performance: Yutong He, Guangchun Ruan, Haiwang Zhong. IEEE Trans. Sustain. Energy, vol.16, no.4, pp.2547-2559, 2025. DOI: 10.1109/tste.2025.3557004
- dhara2025mininertia_ffr: Pijush Kanti Dhara, Zakir Hussain Rather, Chitaranjan Phurailatpam. IEEE Trans. Instrum. Meas., vol.74, pp.1-14, 2025. DOI: 10.1109/tim.2025.3538063
- peng2024inertia_allocation: Zefeng Peng et al. (6 authors). IEEE Trans. Power Syst., vol.39, no.1, pp.1615-1627, 2024. DOI: 10.1109/tpwrs.2023.3267267
- pandit2025ev_freq: Dilip Pandit et al. (8 authors). IEEE Trans. Power Syst., vol.40, no.1, pp.636-649, 2025. DOI: 10.1109/tpwrs.2024.3391211

## DEC-017
Date: 2026-06-12
Gate: G1->G3
Decision: Writing and methodology audit of Conference_version/main.tex (skills: latex-paper-en, gabriel_scientific_writer, audit-methodology). 20 corrections applied. Key items: (1) fixed undefined references sec:cases, fig:ieee14_modified (pending placeholder, FIG-004), and journal-version labels eq:pbess_gfl_raw/eq:iq_lim/eq:pgfm_local in tab:cases, replaced by the reduced-version labels; (2) added first-order activation law for lambda_g (eq:lambda_activation_reduced) and restricted the assistance scope from undefined I_GFL to B_GFL with explicit note that only the GFL BESS is assisted; (3) removed PDC RoCoF computation claim that contradicted Section II; (4) reworded "local PLL frequency is corrected" to angle augmentation without PLL overwrite, consistent with the assistance law; (5) defined how wide-area terms are disabled in baselines C1 (local omega_hat substitution, lambda=0) and C3 (D_c=0); (6) added formal definitions of e_theta_max and e_a_max and renamed cross-saturation time to power-limit saturation time; (7) realigned Conclusions to the reduced conference model, removing journal-version claims (P_in/P_out SoC, V_oc equation, explicit DC-link balance, cross-saturation with active priority) that this paper does not present; (8) removed leftover duplicate paragraph and empty tab:system_config, superseded by tab:resource_allocation and tab:bess_parameters; (9) repaired artifacts from concurrent user edits: broken abstract sentence ("assigns BESS at as GFL...") and stray markdown fence after \end{abstract}; (10) terminology aligned with the new title (multimode -> mode-assigned in keywords, tab:cases, Conclusions); (11) SoC efficiency note added; omega_0 notation fixed (2pi x 60).
Justification: main.log showed 5 undefined references; internal contradictions between Sections II-III and IV; Conclusions described the journal model (DEC-015/DEC-016) instead of the reduced conference formulation, creating overclaim risk under T-007/T-008.
Evidence reviewed: Conference_version/main.tex and main.log; plan_maestro.md secs 5-9; research/gap_matrix.md; ops/sted/traceability_matrix.csv (CLM-001..007, EQ-001..004, FIG-004); Conference_version/biblio_paper.bib (all cited keys VERIFIED).
Blockers or limitations: pending user confirmation in tab:ibr_battery_parameters: transformer ratio 420 V/345 kV vs grid-side rated voltage 690 V_LL (contradictory); T_p and tau_x are "case-defined" (numeric values required before G4); efficiency units differ between tables (% vs p.u.); author metadata incomplete (empty \ead[url] for author 2, Autor3 placeholder, CRediT TBD).
Responsible: Claude (editorial red-team)
Status: passed
Next action: User confirms transformer/voltage values and defines T_p and tau_x; FIG-004 and quantitative results required before G4; strip \pendingresult markers before submission. Recompiled after corrections: 0 errors, 0 undefined references.

## DEC-SKILL-001
Date: 2026-07-13
Gate: tooling (skill infrastructure, no paper gate)
Decision: Refactored the `gabriel_scientific_writer` skill based on `scientific_writer` and the official skill-creator authoring guidance (platform.claude.com/docs, Agent Skills best practices). Changes: (1) SKILL.md rewritten (~180 lines, <500 as recommended); (2) `name` fixed to match the folder (`gabriel_scientific_writer`, was the non-matching display name "Author-Profiled Scientific Writer"); (3) `description` differentiated toward the power-systems/power-electronics/IBR/control/HIL-PHIL domain and given an explicit routing hint to `scientific_writer` for general writing, to stop trigger collision with that skill; (4) adopted from `scientific_writer` the 4 operation modes (full rewrite / surgical polish / [MISSING] resolution / diagnostic), rationale-based rules, cross-coherence checks, valid literature-comparison policy, explicit LaTeX/\cite/\ref/\label/macro/color-revision preservation, and the drafting-vs-diagnostic output contract; (5) removed all arbitrary numeric thresholds (sentence length 18-30/28-32/8-14 tokens, std dev 8-15, connectors 8-12/1k, hedging 1 per 4-6 sentences, ">12/1k") and the anti-AI-detection framing (anti-baja-entropia, burstiness, "anti-senales de texto generico", window-of-3/4 rules, forced verb rotation, absolute em-dash and `we` bans, universal mandatory numbered contributions), replacing them with functional rules; (6) added progressive-disclosure reference files references/domain_conventions.md, references/section_patterns.md, references/style_rules.md; (7) deleted style_calibration_protocol_v3.md, a near-verbatim duplicate of the old SKILL.md whose content (thresholds + anti-detection heuristics) contradicts the refactor and is superseded by the new SKILL.md + references.
Justification: The two writer skills had colliding activation triggers and gabriel's distinctive content was mostly unsourced numeric thresholds plus anti-detector heuristics, which are voodoo constants (skill-creator "no voodoo constants") and which the audit brief itself flagged for removal. No author corpus exists to justify a personalized style profile, so gabriel was refactored as the domain-specialized (power/control/IBR) writer while scientific_writer remains the general one. No manuscript text, results, equations, or citations were touched.
Evidence reviewed: .claude/skills/gabriel_scientific_writer/SKILL.md and style_calibration_protocol_v3.md (pre-refactor); .claude/skills/scientific_writer/SKILL.md and references/ieee_patterns.md; platform.claude.com/docs Agent Skills best practices (name <=64 chars lowercase/hyphens, description <=1024 chars third person what+when, SKILL.md body <500 lines, one-level-deep references, no voodoo constants, forward-slash paths). Both gabriel files were git-tracked and clean, so history is preserved.
Blockers or limitations: `name` uses an underscore to match the existing folder/registration convention (as does the sibling `scientific_writer`), which deviates from the strict lowercase/hyphen charset in the API docs but is what Claude Code loads; no author-paper corpus was available, so references/ contains domain conventions and functional style rules, not an empirical author style profile. Not committed to git (left for user review).
Responsible: Claude (skill refactor)
Status: passed
Next action: User reviews the new SKILL.md and references/; optionally build an empirical references/gabriel_style_profile.md from 3-8 of the author's papers if a personalized style layer is wanted; run the dry-run test cases before relying on the skill for submission text.

## DEC-SKILL-002
Date: 2026-07-13
Gate: tooling (skill infrastructure, no paper gate)
Decision: Consolidated the two writer skills into one. Deleted `.claude/skills/scientific_writer` (SKILL.md + references/ieee_patterns.md) and made `gabriel_scientific_writer` the single scientific-writing skill of the project. Before deletion, the reusable field-agnostic content of scientific_writer/references/ieee_patterns.md (fill-in section templates, literature-comparison LaTeX snippets, conditional-formulation table, and final-review checklist including \cite/\ref/\label checks) was migrated into the new references/ieee_patterns.md under gabriel (power-domain examples substituted for the original indoor-localization ones). gabriel's SKILL.md description and body were rewired: the description was broadened to absorb scientific_writer's general activation triggers (activates whenever the user asks to draft/rewrite/polish/improve academic text, even without naming it) while keeping the power/electronics/IBR/control/HIL-PHIL specialization; every routing pointer and body reference to scientific_writer was removed. The stale `scientific_writer` entries in .claude/skills/README.md and .codex/skills/README.md were removed and the totals decremented (31->30 and 37->36).
Justification: The user requested keeping the personalized `gabriel_scientific_writer` and removing `scientific_writer`. The two had colliding activation triggers; consolidating avoids ambiguity. All engineering strengths of scientific_writer (4 operation modes, rationale-based rules, cross-coherence, valid-comparison policy, LaTeX/\cite preservation, output contract) were already present in gabriel from DEC-SKILL-001, and the remaining reusable reference material was migrated rather than lost. No manuscript text, results, equations, or citations were touched. Deletion is recoverable via git history (files were tracked and clean).
Evidence reviewed: scientific_writer/SKILL.md and scientific_writer/references/ieee_patterns.md (read in full pre-deletion); gabriel SKILL.md and references/*; repo-wide grep for "scientific_writer" (hits only in the two README indexes and this log). Both scientific_writer files were git-tracked and clean.
Blockers or limitations: gabriel is now the sole writer and will also handle non-power scientific text under the same rigor rules; it is not restricted to the power domain. The decision_log DEC-SKILL-001 narrative still references scientific_writer as "the general one"; that is historical context at the time of writing and is intentionally not rewritten (append-only log). Not committed to git (left for user review).
Responsible: Claude (skill consolidation)
Status: passed
Next action: User reviews; run dry-run test cases on a real section; optionally build references/gabriel_style_profile.md from 3-8 author papers for an empirical style layer.

## DEC-SKILL-003
Date: 2026-07-13
Gate: tooling (skill infrastructure, no paper gate)
Decision: Deep review of `gabriel_scientific_writer` and three fixes. (1) NEW CRITICAL CAPABILITY: the skill now enforces the project's own claim contract. Added a mandatory "Contrato de trazabilidad del proyecto" section binding the writer to ops/sted/traceability_matrix.csv: it must apply each claim's `permitted_wording`, never reproduce its `forbidden_wording` (not even reformulated), condition or mark [MISSING] when `status` is not verified (e.g. PENDING_EVIDENCE), and anchor to the declared `evidence_id`/`figure_or_table`. Also added the BLOCKED stop condition required by CLAUDE.md (claim exceeds evidence / no validation metrics / request matches a forbidden_wording) and wired it into the rewrite algorithm (new step 3), the auto-check, and the output contract. Pointers to plan_maestro.md, research/gap_matrix.md, research/contribution_matrix.md and research/related_work_map.md were added. (2) DEDUPLICATION: references/ieee_patterns.md (migrated in DEC-SKILL-002) was found to duplicate ~70% of the other references - section patterns appeared 3x, comparison policy 4x, and it introduced a second competing checklist. It was dissolved: its fill-in templates merged into references/section_patterns.md, its conditional-formulation table and LaTeX comparison snippets merged into references/domain_conventions.md, and its checklist absorbed into the single Auto-check in SKILL.md (now enriched with the \ref/\label correspondence and math-environment checks it contributed). references/ now has 3 non-overlapping files. (3) EVALUATIONS: added evaluations/cases.json (7 dry-run cases) + evaluations/README.md, satisfying the skill-creator requirement of at least three evaluations. Cases cover forbidden_wording rejection, BLOCKED, unresolvable [MISSING], EMT-vs-phasor comparison, surgical polish, diagnostic-without-rewrite, and terminological stability. Minor: the target-section input was broadened beyond the six IMRaD sections (Related Work, Case studies).
Justification: The skill was a competent generic writer but ignored the machine-readable wording contract that already exists in this repo. traceability_matrix.csv carries permitted_wording / forbidden_wording / status per claim (e.g. CLM-001 forbids "guarantees smooth operation under all conditions"); without reading it the writer could produce a known overclaim while still obeying its "do not invent" rule. Binding the writer to that matrix is what turns it from a careful drafter into an enforcer of the project's traceability contract. The deduplication removes ambiguity about which checklist is authoritative, which skill-creator explicitly warns against.
Evidence reviewed: ops/sted/traceability_matrix.csv (header + CLM-001 row: permitted_wording, forbidden_wording, status=PENDING_EVIDENCE, evidence_id=EV-SIM-C4vsC5); CLAUDE.md (active evidence files; BLOCKED stop conditions); all five declared evidence files confirmed present; grep of *.tex showing \textcolor{red} in use (x2) and no \textcolor{blue} or \pendingresult currently present; skill-creator best practices (single authoritative instruction set, >=3 evaluations, no competing checklists).
Blockers or limitations: The skill still contains no empirical author style profile despite the `gabriel_` prefix; the personalization remains unsubstantiated until a corpus of 3-8 author papers is analyzed. `name` still uses an underscore to match the folder/registration convention, deviating from the strict lowercase/hyphen charset in the API docs. The blue/red revision-colour rule is aspirational: only \textcolor{red} is currently used in the manuscript. Evaluations have no automated runner; they are dry-run only. Not committed to git (left for user review).
Responsible: Claude (skill deep review)
Status: passed
Next action: Run the 7 dry-run cases, especially EVAL-01 and EVAL-02, which guard the traceability contract. Optionally build references/gabriel_style_profile.md from author papers to justify the `gabriel_` prefix.

## DEC-SKILL-004
Date: 2026-07-13
Gate: tooling (skill infrastructure, no paper gate)
Decision: Raised gabriel_scientific_writer to Q1-journal writing standard for electrical/control engineering. Five additions, all verified against the real manuscript (paper/main.tex, cas-dc class; Conference_version/main.tex, IEEEtran) before being written. (1) NEW critical rule 4 "Rigor matematico y claims formales" in SKILL.md + new references/math_writing.md: symbol definition with `where` clauses and units, equation punctuation as part of the sentence, and a hard rule that formal-stability terms (asymptotically stable, passive, optimal, ISS, converges) require a formal argument (Lyapunov, passivity function, optimization formulation, convergence proof) in CONTEXTO before being used - otherwise condition the sentence or mark [MISSING], mirroring the forbidden_wording contract but for mathematical overclaims. Assumptions must be explicit (numbered `assumption` environment or clear prose). (2) Methods pattern rewritten in SKILL.md and references/section_patterns.md to cover, when applicable, the 12 points CLAUDE.md mandates for methodology sections (system under study, baselines, measurement layer, workflow, objective, platform, acquisition, execution, test scenarios, metrics, reproducibility parameters, limitations) - previously the pattern only had 4 generic steps and silently dropped baselines/metrics/reproducibility/limitations that CLAUDE.md requires. (3) Front matter added to references/section_patterns.md (Title, Highlights with the 85-character/bullet Elsevier limit, keywords, figure/table captions) - the manuscript is Elsevier cas-dc with \begin{keywords} and \credit{} already in use but no Highlights yet, and the skill previously ignored the part of the paper that determines desk-reject. (4) references/style_rules.md gained an "Interferencia ES->EN" section (calques: allows to + infinitive, article-with-uncountables, actual/current false friend, data is/are, etc.) since the group drafts from Spanish and English-quality is a real Q1 rejection cause. (5) New references/rebuttal_guide.md: point-by-point reviewer response structure (acknowledge -> action -> evidence -> location), tone rules, and reuse of the same \textcolor{blue}{} revision-marking system already required elsewhere in the skill - no Q1 submission in this field skips a review round, and no other skill in the project's ecosystem covers rebuttal writing. Auto-check, the Methods entry in "Entradas requeridas", "Cuando usar", and the references index in SKILL.md were all updated to wire in the new content; two new dry-run evaluation cases (EVAL-08 formal claim without backing, EVAL-09 Highlights length/anchoring) were added to evaluations/cases.json (now 9 cases) so the new capabilities are covered the same way the traceability contract already was.
Justification: A Q1 reviewer in control/power engineering judges a paper on its mathematics, its methodology completeness, its front matter (title/highlights/abstract/figures decide triage before the body is read), its English quality, and its rebuttal - not only on prose sobriety and citation hygiene, which the skill already handled well. Each addition was grounded in this repository's actual state rather than assumed: main.tex confirmed as cas-dc (Elsevier) with 25 equation/align environments and zero formal theorem/assumption/proposition environments; CLAUDE.md's 12-point methodology contract confirmed present and stricter than the skill's prior 4-step Methods pattern; \begin{keywords}/\credit{} confirmed present with no Highlights block yet.
Evidence reviewed: paper/main.tex (documentclass cas-dc, keywords/credit present, 25 equation/align, no formal theorem-like environments); Conference_version/main.tex (IEEEtran, 26 equation/align); CLAUDE.md (12-point methodology contract, active evidence files); ops/sted/traceability_matrix.csv (permitted_wording/forbidden_wording contract, reused as the model for the new math-claims rule); prior DEC-SKILL-001/002/003 entries for continuity.
Blockers or limitations: No author-paper corpus was analyzed, so the `gabriel_` prefix still has no empirical style-profile backing (same open item as DEC-SKILL-001/003). The Highlights character limit (85) and bullet count (3-5) are Elsevier's general convention; the exact figure should be confirmed against the specific target journal's guide for authors before submission. Rebuttal guidance assumes the project's existing \textcolor{blue}{} convention; if a specific journal mandates a different revision-marking format, that format takes precedence. Evaluations remain dry-run only, no automated runner. Not committed to git (left for user review).
Responsible: Claude (skill deep improvement, Q1 standard)
Status: passed
Next action: Run the 9 dry-run cases, especially EVAL-08 and EVAL-09 (new). Optionally build references/gabriel_style_profile.md from author papers to justify the `gabriel_` prefix; confirm Highlights character limit against the specific target journal before submission.

## DEC-SKILL-005
Date: 2026-07-13
Gate: tooling (agent/skill infrastructure, no paper gate)
Decision: Three related organizational fixes across .claude and .codex, agreed together by the user ("los 3"): (1) Added YAML frontmatter (name, description, tools) to .claude/agents/sted_integrator.md, which previously had none and consequently did not appear in the harness's list of available Agent-tool subagent types (confirmed empty at session start) -- the file's existing Mission/Read-first/Responsibilities/Escalate-when body was preserved verbatim. (2) Reconciled drift between .claude/skills and .codex/skills discovered while auditing gabriel_scientific_writer: verified .codex/skills/gabriel_scientific_writer/{SKILL.md,references/*,evaluations/*} are already byte-identical (same git blob hash) to the .claude copy improved in DEC-SKILL-001..004, so no content sync was needed there; removed the one orphaned leftover, .codex/skills/gabriel_scientific_writer/style_calibration_protocol_v3.md (its .claude counterpart was deleted in DEC-SKILL-001 but the deletion was never mirrored); removed the now-fully-superseded .codex/skills/scientific_writer/ (2 files) and .codex/skills/academic-paper/ (45 files) directories, including the empty directory trees git rm left behind, mirroring the same consolidation already made on the .claude side (DEC-SKILL-002 for scientific_writer; academic-paper was already absent from .claude/skills before this session, with no corresponding decision_log rationale found -- its .codex removal is not backed by a discovered rationale beyond matching the .claude state). Updated .codex/skills/README.md (removed the academic-paper line, decremented 30->29) and .claude/skills/README.md (removed a stale academic-paper line and added the previously-missing ieee_elsevier_paper_skill entry that already existed on disk but was never listed, plus the new metadata-pipeline entry; count corrected to 31, verified against the actual folder count on disk). (3) Ported metadata-pipeline from .codex/agents/metadata-pipeline.toml into a new .claude/skills/metadata-pipeline/SKILL.md (bibliographic metadata extraction/normalization/deduplication), since it was the one Codex agent from the earlier 7-agent audit with no close Claude-side equivalent; left .codex/agents/metadata-pipeline.toml untouched since Codex already has a working native copy.
Justification: sted_integrator's non-registration mirrors the same "prose file with no wiring into the harness" defect already found and fixed for the two hooks in DEC- entries earlier this session; fixing it is required for the agent to be selectable at all. The .codex skill-tree drift is a direct, foreseeable consequence of skills being duplicated per-tool rather than shared: a deliberate consolidation decision made on the .claude side (DEC-SKILL-002) silently left the old content live and reachable from Codex, defeating the purpose of the consolidation for any session run from that tool. metadata-pipeline was the only one of the seven audited Codex agents without a close functional match already covered by an existing Claude skill (the other six -- literature-scout, manuscript-builder, methodology-red-team, review-gap-auditor, review-topic-scout, stats-and-figures -- all duplicate existing Claude skills and were deliberately not ported).
Evidence reviewed: system's own "Available agent types" listing at session start (sted_integrator absent); .claude/agents/sted_integrator.md and .codex/instructions.md (parallel per-tool instruction files, both converging on shared AGENTS.md/STED-RW_Lean.md/ops/sted/); diff and git blob hash of .codex vs .claude gabriel_scientific_writer/SKILL.md (identical); file listing and mtimes of .codex/skills/gabriel_scientific_writer/references/* (already mirrored); git ls-files confirming all removed content was tracked (mode 100644, not a symlink); grep of decision_log.md for prior academic-paper rationale (none found); disk folder counts for both .claude/skills (31) and .codex/skills README cross-check.
Blockers or limitations: No decision_log rationale exists for the original .claude-side academic-paper removal (predates this session); the .codex/skills/README.md still has other pre-existing stale entries unrelated to this task (missing audit-methodology, consensus-cdp-search, ieee_elsevier_paper_skill, review-code, review-paper, update-research-state, write-section; and two entries -- ieee-elsevier-benchmark-figures, scientific-graphic-maker -- not independently re-verified against .codex/skills disk contents) that were out of scope for this reconciliation and were not touched. metadata-pipeline has not been dry-run tested. The mechanism that kept .codex/skills/gabriel_scientific_writer in sync with .claude's improvements throughout DEC-SKILL-001..004 was not identified (no sync script was found or run by this session) and remains unexplained. Not committed to git (left for user review).
Responsible: Claude (agent/skill organization across .claude and .codex)
Status: passed
Next action: User reviews; optionally do a full .codex/skills/README.md audit against disk (separate, larger task, not requested here); dry-run test the new metadata-pipeline skill and the now-registered sted_integrator agent.

## DEC-SKILL-006
Date: 2026-07-13
Gate: tooling (cross-tool instruction alignment, no paper gate)
Decision: Closed a gap where the STED-RW Lean governance layer was read unconditionally by Codex on every session (via .codex/instructions.md) but was invisible to a normal Claude Code session unless the user explicitly invoked the sted_integrator agent. Two edits: (1) CLAUDE.md "Read first" list now includes STED-RW_Lean.md and prompt_maestro_STED_RW.md as items 1-2 (before AGENTS.md), matching the source-of-truth order already established in .codex/project_context.md and .claude/agents/sted_integrator.md; added a "Repository alignment" bullet pointing at `python ops/checks/check_required_files.py --mode paper --strict`, which CLAUDE.md previously never mentioned even though the script exists and is Codex's own documented validation step (.codex/validation_rules.md). (2) Fixed .codex/project_context.md's STATUS field, which read TEMPLATE_ACTIVE despite this repository being a fully instantiated, active paper project (paper/main.tex, research/gap_matrix.md, an in-progress Wide-Area Control manuscript) -- changed to PAPER_ACTIVE, matching the mode vocabulary already used by check_required_files.py's MODE_REQUIREMENTS (template/paper/book/software/pipeline), and expanded the Purpose paragraph to state the template origin remains valid for structural conventions while project content is real, not placeholder.
Justification: check_required_files.py's own REQUIRED_CORE list already treats STED-RW_Lean.md, prompt_maestro_STED_RW.md, and .claude/agents/sted_integrator.md as load-bearing files, confirming these are meant to be functional, not decorative; a Claude session that never reads them (the pre-existing state) was operating with less of the project's own governance context than a Codex session on the same repo, for no principled reason -- both tools should default to the same foundational awareness. project_context.md's stale TEMPLATE_ACTIVE status is the same category of drift found repeatedly this session (broken decision_log path in post_edit_check.md, missing sted_integrator frontmatter, stale skill README inventories): governance scaffolding left over from template creation that was never updated as the project matured.
Evidence reviewed: ops/checks/check_required_files.py (confirmed no code path reads project_context.md's STATUS value -- it is documentation-only, safe to correct without behavioral risk; confirmed REQUIRED_CORE/OPTIONAL_ADAPTERS/MODE_REQUIREMENTS lists); `python ops/checks/check_required_files.py --mode paper --strict` run before and after the edits, both times reporting required_core present, all optional adapters present, and paper mode requirements present; grep of CLAUDE.md confirming zero prior mentions of STED-RW_Lean.md, prompt_maestro_STED_RW.md, or check_required_files.py; direct read of .codex/instructions.md, .codex/latex_rules.md, .codex/methodology_rules.md, .codex/validation_rules.md, .codex/project_context.md.
Blockers or limitations: check_required_files.py's OPTIONAL_ADAPTERS list references .codex/research_rules.md and .agents/orchestrator.md / .agents/skills/sted-rw/SKILL.md -- both confirmed present by the --strict pass but neither has been read or evaluated in this session; a third agent/instruction surface (.agents/, distinct from .claude/ and .codex/) exists in this repository and has not yet been audited. Not committed to git (left for user review).
Responsible: Claude (cross-tool instruction alignment)
Status: passed
Next action: User reviews; optionally audit the .agents/ directory (orchestrator.md, skills/sted-rw/SKILL.md) and .codex/research_rules.md, which surfaced during validation but were out of scope for this task.

## DEC-SKILL-007
Date: 2026-07-13
Gate: tooling (cross-file style governance, no paper gate)
Decision: Resolved a contradiction found while auditing ops/ and research/ for overlap: ops/profile/writing_style.md ("Guia de estilo para toda produccion escrita generada en este workspace") retained a hard numeric cap -- "Maximo 25-30 palabras por oracion en texto tecnico" -- while .claude/skills/gabriel_scientific_writer/SKILL.md deliberately removed all arbitrary numeric thresholds (sentence length, connector density, hedging quota) in DEC-SKILL-001, replacing them with functional rules with no corpus backing for the numeric values. Per explicit user decision ("manda gabriel_scientific"), ops/profile/writing_style.md principle 2 was rewritten to drop the word-count cap and state the same functional rule already in gabriel_scientific_writer's SKILL.md ("divide una oracion cuando acumule varias relaciones causales independientes, demasiadas condiciones o una secuencia dificil de seguir"), with an explicit cross-reference back to gabriel_scientific_writer so the two files no longer give contradictory guidance on this point.
Justification: The user was asked, during a broader ops/research overlap audit, which of the two sources should be authoritative on this specific contradiction; gabriel_scientific_writer's position was already deliberately reasoned (DEC-SKILL-001: no evidence that any numeric sentence-length threshold reflects the author's actual corpus, and such caps risk inducing artificial uniformity) and the user confirmed it should win. Only the contradicting line was changed -- the rest of ops/profile/writing_style.md (IEEE/Elsevier conventions, the "errores frecuentes" table, Spanish-text rules) was left untouched since it was not reported as contradictory, only as overlapping in substance with gabriel_scientific_writer's references/style_rules.md, which is acceptable duplication between a general cross-project profile and a domain-specialized skill.
Evidence reviewed: ops/profile/writing_style.md (full read, prior turn); .claude/skills/gabriel_scientific_writer/SKILL.md line 85 (Sintaxis y ritmo rule, quoted verbatim to confirm the mirrored wording matches the actual current rule, not a stale paraphrase).
Blockers or limitations: The broader ops/research audit from the same session surfaced other unresolved items (check_bib_entries.py wrong bib path, check_claim_evidence.py status-vocabulary mismatch plus a column-shift data-corruption bug in traceability_matrix.csv row EQ-004, check_latex_structure.py's generic section list not matching this paper's actual sections, check_forbidden_claims.py flagging legitimate "state-of-the-art" usage, and research/bibliography/references.bib being a stale 5-entry file inherited from legacy/pmu_kundur_previous_project while AGENTS.md/CLAUDE.md still list it as an active evidence file) -- none of those were addressed in this entry; only the writing_style.md contradiction was in scope for this specific user confirmation. Not committed to git (left for user review).
Responsible: Claude (style-governance conflict resolution)
Status: passed
Next action: User decides whether to address the remaining ops/checks/*.py validator bugs and the stale research bibliography reference found in the same audit.

## DEC-EVID-001
Date: 2026-07-13
Gate: governance (evidence-location contract, no paper gate)
Decision: Corrected the "Active evidence files" section in CLAUDE.md and AGENTS.md, which pointed agents at `research/papers/` and `research/bibliography/` as the location of the active literature and bibliography. Neither holds active evidence: `research/papers/` contains only `.gitkeep`, and `research/bibliography/references.bib` contains five `@misc{PENDING_REF_*}` placeholder stubs. The real evidence lives in `paper/core_refs/` (5 source PDFs + 8 per-paper reading notes) and `paper/biblio_paper.bib` (36 entries). Both files now name `paper/core_refs/` and `paper/biblio_paper.bib` as canonical, explicitly mark `research/papers/` and `research/bibliography/references.bib` as non-sources, and flag `Conference_version/core_refs/` as a byte-identical frozen copy and `Conference_version/biblio_paper.bib` (40 entries) as conference-only. Also removed the dead guard about `paper_ingestion_pack_v2/`, a directory that does not exist in this repository. Documentation-only change; no evidence file was moved, renamed or deleted.
Justification: This defect was already recorded as an open item in DEC-SKILL-007's limitations ("research/bibliography/references.bib being a stale 5-entry file ... while AGENTS.md/CLAUDE.md still list it as an active evidence file"). The operational artifacts had already converged on reality without the governance docs following: `ops/sted/traceability_matrix.csv` row REF-BASE records `source_path=paper/biblio_paper.bib`, and `ops/sted/test_plan.md` T-BIB-001 points at "PDF en paper/core_refs/" while T-006 validates against `biblio_paper.bib`. CLAUDE.md and AGENTS.md were therefore the only two surfaces still misdirecting agents, and they are the two files an agent reads first, so the error propagated to every session. Per user instruction the contract was aligned to the observed reality rather than relocating files into `research/`, which keeps the manuscript's compile path (`\bibliography{biblio_paper}`, figures and refs resolved relative to `paper/`) untouched at gate G1.
Evidence reviewed: `find research -type f` (confirmed `research/papers/` holds only `.gitkeep`); `grep '^@' research/bibliography/references.bib` (5 PENDING_REF_* @misc stubs); `grep -c '^@' paper/biblio_paper.bib` (36 entries) and `Conference_version/biblio_paper.bib` (40 entries); md5sum comparison of all 14 files in `paper/core_refs/` vs `Conference_version/core_refs/` (all identical); `paper/main.tex:1156` (`\bibliography{biblio_paper}`); `ops/sted/traceability_matrix.csv:18` (REF-BASE source_path); `ops/sted/test_plan.md:25,62`; confirmed `paper_ingestion_pack_v2/` does not exist on disk.
Blockers or limitations: `ops/checks/check_bib_entries.py:6` still hardcodes `Path("research/bibliography/library.bib")` -- a file that has never existed in this repository -- so the check currently returns exit 1 ("Missing canonical bibliography file") on every run regardless of repository state. It was left unchanged here because it is a code change rather than a governance-doc correction, and was not in scope for this instruction. The duplication of `core_refs/` (~23 MB stored twice) and the three divergent .bib files (36/40/5) are documented but not resolved. `paper/main.tex` still loads its figures from `../Conference_version/figs/` while `paper/figures/` is empty. Not committed to git (left for user review).
Responsible: Claude (evidence-location contract correction)
Status: passed
Next action: User decides whether to (a) fix `check_bib_entries.py` to point at `paper/biblio_paper.bib`, (b) delete the stale `research/bibliography/references.bib` and the empty `research/papers/` placeholder now that they are declared non-sources, and (c) address the `paper/main.tex` -> `Conference_version/figs/` figure coupling.

## DEC-EVID-002
Date: 2026-07-13
Gate: governance (evidence cleanup, no paper gate)
Decision: Executed the cleanup authorized by the user after DEC-EVID-001. Three actions: (1) Fixed `ops/checks/check_bib_entries.py`, whose hardcoded path `research/bibliography/library.bib` (a file that never existed here) made the check return exit 1 on every run; it now points at `paper/biblio_paper.bib`, the canonical bibliography, and returns exit 0. (2) Deleted the two files formally declared non-sources in DEC-EVID-001: `research/bibliography/references.bib` (five `@misc{PENDING_REF_*}` placeholder stubs, no verifiable data, all its titles already present as verified entries in `paper/biblio_paper.bib`) and the now-empty `.gitkeep` markers under `research/bibliography/` and `research/papers/`; `research/` now holds only the three active matrices (gap, contribution, related_work_map). (3) Removed the resulting dead references: the `research/papers/` and `research/bibliography/references.bib` bullets in CLAUDE.md and AGENTS.md (both now list `check_bib_entries.py` as a consumer of the canonical bib), and README.md's "bibliografía activa" claim for `research/` plus its dead `paper_ingestion_pack_v2/` guard.
Justification: With the evidence-location contract corrected in DEC-EVID-001, the stub bibliography and empty placeholders had no remaining function and only preserved the risk of an agent treating them as sources; the user explicitly authorized their deletion. The validator fix removes a check that was failing for a structural reason (wrong path) rather than a repository-state reason, so `check_bib_entries.py` now measures something real. Deleting the files required removing the governance bullets that named them, otherwise DEC-EVID-001's own goal (no dead evidence references in the first-read files) would have been reintroduced.
Evidence reviewed: full read of `research/bibliography/references.bib` before deletion (confirmed all five entries are PENDING_VERIFICATION stubs); `grep` across active files (excluding legacy/ and vendored skills) confirming the only remaining consumers of `research/papers|research/bibliography` were the two governance docs and `check_bib_entries.py`; `python ops/checks/check_bib_entries.py` before (exit 1, "Missing canonical bibliography file") and after (exit 0, "Canonical bibliography file exists"); `find research -type f` after deletion (only the three matrices remain).
Blockers or limitations: Unresolved items from DEC-EVID-001 still stand and were out of scope here: the ~23 MB `core_refs/` duplication between `paper/` and `Conference_version/`, the divergent 36/40-entry .bib pair, and `paper/main.tex` loading figures from `../Conference_version/figs/` while `paper/figures/` is empty. Other validators in `ops/checks/` (check_claim_evidence.py status-vocabulary mismatch and the EQ-004 column-shift in traceability_matrix.csv, check_latex_structure.py's generic section list, check_forbidden_claims.py flagging legitimate "state-of-the-art") remain unaddressed. Not committed to git (left for user review).
Responsible: Claude (evidence cleanup and validator fix)
Status: passed
Next action: User decides whether to address the core_refs duplication and the main.tex -> Conference_version/figs figure coupling flagged in the original structure review.

## DEC-018
Date: 2026-07-13
Gate: governance (session-memory workflow, no paper gate)
Decision: Replaced the project's narrated (hand-written) session memory with a derived-and-enforced memory workflow, and removed the stale narrated artifacts. Four parts. (1) NEW ops/checks/session_boot.py: a read-only script that computes a compact project-state snapshot directly from the governed artifacts (active gate from plan_maestro.md cross-checked against README.md and final_quality_report.md; claim/equation/figure/reference progress from ops/sted/traceability_matrix.csv; test progress and pending IDs from ops/sted/test_plan.md; last three DEC entries and the most recent non-empty "Next action" from this log; git branch/HEAD/dirty count; and light CLAUDE.md stop-condition checks including the missing outputs/ and scripts/ dirs promised by README). Nothing is stored, so it cannot go stale. Wired to run automatically at Claude Code session start via a new SessionStart hook in .claude/settings.json, and added as step 0 of the "Read first" list in .codex/instructions.md since Codex does not execute Claude hooks -- one generator, two consumers, so they cannot diverge. (2) NEW ops/checks/session_close.py: compares the working tree against HEAD and, if any GOVERNED artifact (plan_maestro.md, paper/main.tex, paper/biblio_paper.bib, ops/sted/traceability_matrix.csv, ops/sted/test_plan.md, research/) changed without a matching touch to this decision_log.md, prints an advisory reminder naming the files and the next free DEC number. Wired to the Stop hook. Advisory (always exit 0) to match the repository's existing hook convention. (3) HARDENED .claude/hooks/post_edit_check.py: now reads the hook payload from stdin, and when the edited file is a governed artifact it emits a targeted edit-time reminder (register a DEC entry, respect the traceability status of any claim, preserve LaTeX labels/cites/refs) instead of the generic advisory -- moving enforcement to the moment the agent is still working. (4) REMOVED the old narrated memory: 08_session_memory/ (plan_expand_anchor_n98.md, progress.md, research_state.md, test_oracle.md), .claude/commands/update-session.md, and .codex/skills/update-research-state/SKILL.md.
Justification: The four files under 08_session_memory/ were verified to be a byte-identical copy (same sizes and mtimes, empty `diff -rq`) of ../Review_DD_identification/08_session_memory/ -- they describe a different project ("Data-Driven Dynamic Modeling for Control of IBR-Dominated Power Systems: A Critical Review", Phase 4, ~1,700-line manuscript) with zero mentions of this project's topic (wide-area, BESS, GFM), and actively contradicted the real state (G1, all evidence PENDING). This repository therefore had no real project memory; it had a foreign project's memory left over from cloning the workspace. .claude/commands/update-session.md was already broken (it reads 08_session_memory/current_week.md and done_log.md, neither of which exists). .codex/skills/update-research-state/SKILL.md was the dangerous one: it still functioned and WRITES progress.md/research_state.md/test_oracle.md by hand, so leaving it would have regenerated narrated (drift-prone, cross-project-contaminable) memory on its next run. The derived approach fixes the root cause: memory computed from artifacts cannot be copied stale between projects, cannot silently contradict the gate, and is auditable in git. This also directly addresses the earlier-rejected PROJECT_STATUS.md idea -- a generated view is a cache, not a fifth competing source-of-truth for the gate.
Evidence reviewed: `diff -rq` of the two 08_session_memory/ folders (empty); `ls -la` of both (identical sizes/mtimes); `grep` for wide-area/BESS/GFM in 08_session_memory/ (no matches); full read of test_oracle.md, research_state.md headers, progress.md header, plan_expand_anchor_n98.md outline; confirmation that ../Review_DD_identification/08_session_memory/ holds the live originals; read of .claude/commands/update-session.md and .codex/skills/update-research-state/SKILL.md confirming their targets; three dry-runs of session_boot.py (output verified against known state: G1, 0/7 claims, 0/23 tests, 28 DEC entries, DEC-EVID-002 Next action, 113 uncommitted, outputs//scripts/ missing); session_close.py run ("Sin cambios en artefactos gobernados. OK."); post_edit_check.py tested with governed, non-governed, and empty-stdin payloads; `python -c json.load` validation of settings.json after each edit (SessionStart, PreToolUse, PostToolUse, Stop all present). Deletions verified staged-only (git diff --cached --diff-filter=D), still present in HEAD (git cat-file), and duplicated in the sibling project -- fully recoverable.
Blockers or limitations: The user's earlier `rm -rf legacy/` (whole legacy/ tree) was done outside any decision entry and remains staged/uncommitted; it is captured here for the record but its rationale (redundant historical material, per ops/README.md legacy policy) predates this session. The dangling reference to the deleted path in README.md is fixed in the same change set, and CLAUDE.md "Read first" is slimmed to point at the boot output first. 01_operating_rules/context_loading.md also references the now-deleted 08_session_memory/current_week.md and /update-session, but it is left untouched on purpose: that file is pervasively stale independently of this change (it also points at nonexistent 00_profile/, 03_templates/, 04_projects/ and a dozen missing SOPs/commands) and belongs to the 01_operating_rules/ consolidation that was proposed but NOT authorized for execution; partially patching two of its ~20 dead references would imply the rest is valid. 01_operating_rules/, 02_routines/ and 05_reference_maps/ remain present and out of scope for DEC-018. Nothing in this change set is committed to git (left for user review). The Stop/SessionStart hooks are advisory by design; hard enforcement (blocking stop until a DEC entry exists) was deliberately not adopted to avoid trapping the user in a stop loop.
Responsible: Claude (session-memory workflow) with explicit user authorization for the deletions
Status: passed
Next action: User to review and commit. Populate outputs/ and scripts/ (promised by README, flagged by session_boot as open stop conditions) as the project moves toward G3/G4. Decide separately whether to consolidate 01_operating_rules/, 02_routines/ and 05_reference_maps/.

## DEC-019
Date: 2026-08-17
Gate: governance (repository configuration)
Decision: Registered canonical GitHub repository URL as https://github.com/gemejiar/Paper_Andes_ML_control in project memory and updated git remote configuration. This ensures the repository path is persisted and accessible across sessions.
Justification: The project was initially pushed to an incorrect repository (Paper_wide_area_control). The correct repository has been identified and registered. Project memory now stores this reference so future sessions can verify and maintain the correct remote.
Evidence reviewed: Confirmation that git remote now points to https://github.com/gemejiar/Paper_Andes_ML_control; creation of project memory entry at ~/.claude/projects/.../memory/project_repository.md
Blockers or limitations: None. Previous push to incorrect repository (Paper_wide_area_control) has been superseded by the correct push.
Responsible: Claude (configuration and memory registration)
Status: passed
Next action: Subsequent sessions will reference the canonical repository URL from project memory for all git operations.

## DEC-020
Date: 2026-08-17
Gate: governance (multi-paper workspace pivot)
Decision: Repository pivots from a single-paper layout to a multi-paper workspace. The existing STED-RW-governed Wide-Area Control paper (plan_maestro.md, gates G0-G4, Journal_paper/, Conference_version/) is untouched and keeps full gate governance. A new sibling top-level directory, Paper_1/, is introduced as an independent, self-contained ANDES-based experimentation workspace (IEEE-39 case, system identification / ML control) with minimal governance: no dedicated plan_maestro.md, no gate track of its own, only its own README.md documenting objective/simulator/how-to-run. The repository-root `venv/` (Python 3.12.10) is adopted as a shared dependency across both papers rather than per-paper; ANDES (verified latest stable PyPI release) is installed there, frozen via root-level requirements.txt / requirements-lock.txt. Root README.md gains a short "Papers en este repositorio" section pointing at both papers.
Justification: The user explicitly requested a multi-paper workspace and, when asked to choose a governance depth (minimal registration vs. full CLAUDE.md/AGENTS.md integration vs. no registration at all), chose minimal registration. This is the smallest change that still complies with the repository's own "Repository alignment" rule in CLAUDE.md ("do not replace historical files silently; register nontrivial migrations") without inventing a second gate system that the user's own instructions for Paper_1/README.md explicitly rejected ("No convertirlo en otro plan maestro"). CLAUDE.md and AGENTS.md "Active evidence files" sections are intentionally left unchanged since they describe evidence for the Wide-Area Control paper specifically, which is unaffected.
Evidence reviewed: Full repo-root listing and .gitignore contents (already cover venv/ and .venv/, no changes needed); confirmation via repo-wide grep that no ANDES/IEEE-39/RL content existed anywhere prior to this change; confirmation that Journal_paper/ (submission paperwork only) and Conference_version/ (the real Wide-Area Control manuscript) are topically unrelated to Paper_1 and untouched; read of ops/checks/check_required_files.py confirming it enumerates files, not directories, so Paper_1/ cannot break --mode paper --strict; plan_maestro.md confirmed to govern only the Wide-Area Control paper (Gate G1, IEEE-14 EMT scope) with no mention of ANDES/IEEE-39/ML.
Blockers or limitations: ops/checks/check_required_files.py --mode paper already required paper/main.tex before this change, which does not exist (the real manuscript lives in Conference_version/main.tex) -- a preexisting gap, unrelated to this decision and left unaddressed. CLAUDE.md/AGENTS.md "Active evidence files" sections do not mention Paper_1 at all; if Paper_1 later needs its own evidence-traceability contract, that will require a follow-up decision.
Responsible: Claude (multi-paper restructuring) with explicit user authorization and governance-depth choice
Status: passed
Next action: Populate Paper_1/ with the ANDES environment and reproducible skeleton (see this same session's execution). No further governance action required unless Paper_1 later needs its own gate-tracked evidence contract.

## DEC-021
Date: 2026-08-17
Gate: governance (STED-RW plan-generation spec, no paper gate)
Decision: Added a mandatory pre-closure interrogation protocol to `prompt_maestro_STED_RW.md` (version bumped 1.0 -> 1.1). New block `PROTOCOLO OBLIGATORIO DE INDAGACION ANTES DE CERRAR EL PLAN` inside the master prompt defines: (1) two plan states, `PLAN_DRAFT` (mandatory while any clarity item is open) and `PLAN_FROZEN`, stamped in a required header, with G1 explicitly blocked while the plan is `PLAN_DRAFT`; (2) a question-economy rule (four preconditions before asking, ban on cosmetic/repeat/open-ended questions, every question must carry a recommended default); (3) a 14-item methodological clarity checklist -- the 12 items of CLAUDE.md's methodology writing rules plus generalization scope and product-closure criterion -- extended per project type (review, software, pipeline, book), each item carrying a state of `resuelto`, `supuesto_aceptado`, `abierto` or `no_aplica`; (4) a fixed question format stating why the item blocks closure, what changes per answer, and the default assumption plus risk; (5) iterative rounds of up to seven questions with no fixed round limit, always delivering plan and questions together, auto-converting to `supuesto_aceptado` any item left unanswered twice from round three; (6) a registration rule routing answers into plan section 0 and this decision log with no new files; (7) a forced-closure path (`PLAN_FROZEN_CON_SUPUESTOS`) that requires listing assumptions with risk, adding a verification per high-risk assumption, and downgrading dependent claims. Supporting edits: new mandatory plan section `0. Estado de clarificacion metodologica` with its register table; principles 16-18; `REGLAS DE SALIDA` rewritten (the old "maximo cinco preguntas, luego version provisional" one-shot rule is replaced by the iterative round rule); success criteria 11-12; compact-version rules 11-12; context-template sections 13-15 (methodology already decided / still open / interrogation mode); expected-output structure and the audit checklist gained the corresponding rows.
Justification: The previous wording allowed the agent to close a plan after a single round of at most five questions, then proceed under assumptions -- which lets undeclared methodological choices (baselines, metrics, test scenarios, reproducibility parameters) enter the plan as if they were decided facts, exactly the failure mode the STED-RW evidence hierarchy exists to prevent. The user asked that the agent keep asking until every methodological aspect is clear before the plan is closed. Binding the question set to CLAUDE.md's own 12-point methodology list keeps the protocol aligned with the repository's existing writing rules instead of introducing a second, competing checklist, and binding `PLAN_DRAFT` to G1 makes the requirement enforceable by the existing gate machinery rather than by good intentions. No new files were proposed: the register lives in the plan maestro and in this log, per the minimal-file rule.
Evidence reviewed: full read of `prompt_maestro_STED_RW.md` (745 lines pre-edit, 928 post-edit; 190 insertions, 7 deletions); CLAUDE.md "Methodology writing rules" (12 items, mirrored as checklist items 1-12) and "Stop conditions"; `grep -rn prompt_maestro_STED_RW` confirming its consumers (.claude/agents/sted_integrator.md:14, .codex/instructions.md:15, .codex/project_context.md:10, CLAUDE.md:19, ops/checks/check_required_files.py:11 REQUIRED_CORE); byte-level check that line endings stayed LF, matching the HEAD blob; anchor-uniqueness assertion on every one of the 13 splice points.
Blockers or limitations: `python ops/checks/check_required_files.py --mode paper --strict` still exits 1 for `plan_maestro.md` and `paper/main.tex` -- both pre-existing and unrelated to this edit (`plan_maestro.md` is deleted in the working tree in favour of `plan_maestro_DDPG_FFC_IEEE39_ANDES.md`; the missing `paper/main.tex` was already recorded in DEC-020's limitations). The protocol was added only to `prompt_maestro_STED_RW.md`; `STED-RW_Lean.md`, `.claude/agents/sted_integrator.md` and `.codex/instructions.md` still describe plan closure without the `PLAN_DRAFT`/`PLAN_FROZEN` state, so an agent that reads only those files will not enforce it. No existing plan was re-opened or re-stated under the new protocol. Not committed to git (left for user review).
Addendum (2026-08-18): a peticion del usuario se verifico que el bloque anadido fuera project-agnostic. Un grep de terminos del proyecto activo (ANDES, DDPG, IEEE, BESS, RoCoF, droop, seed, inercia) sobre el archivo no devuelve coincidencias, y las 14 modificaciones pertenecen todas al protocolo de preguntas, con una unica sustitucion de texto previo (la regla de 'maximo cinco preguntas'). Se corrigio el sesgo restante: las filas 4, 7, 8 y 11 del checklist usaban ejemplos experimentales/computacionales y ahora estan redactadas en terminos generales; se anadio una regla de traduccion que obliga al agente a reexpresar cada aspecto en el vocabulario del proyecto (revision, libro, curso, software) y a usar `no_aplica` solo cuando la traduccion no exista; y la plantilla de contexto advierte que los nombres de la seccion 13 son genericos.
Responsible: Claude (plan-generation spec update) at explicit user request
Status: passed
Next action: User decides whether to propagate the `PLAN_DRAFT`/`PLAN_FROZEN` state and the clarity checklist into `STED-RW_Lean.md`, `.claude/agents/sted_integrator.md` and `.codex/instructions.md`, and whether the active plan (`plan_maestro_DDPG_FFC_IEEE39_ANDES.md`) should be re-audited against the new checklist before G1 is approved.

## DEC-022
Date: 2026-08-18
Gate: governance (aplicacion del protocolo de indagacion al plan de Paper_1, sin gate de paper)
Decision: Se aplico el protocolo de indagacion de DEC-021 al plan experimental `plan_maestro_DDPG_FFC_IEEE39_ANDES.md` y se le anadio la seccion obligatoria `0. Estado de clarificacion metodologica`. El plan queda marcado `PLAN_DRAFT` con 7 de 14 puntos del checklist en estado `abierto` (sistema, lineas base, capa de medicion, escenarios, metricas, reproducibilidad y limitaciones); su linea de estado, que declaraba "Plan experimental congelado antes de implementacion", se corrigio porque contradecia la existencia de esos puntos abiertos. La seccion contiene cuatro bloques: (0.1) el checklist con el estado de cada aspecto y el lugar del plan donde se resuelve; (0.2) los hechos verificados por inspeccion de solo lectura del caso base; (0.3) catorce supuestos por defecto (S-01 a S-14) con su base, riesgo y gate consumidor, adoptados solo donde el plan no fija el valor y su ausencia impide ejecutar; (0.4) siete preguntas abiertas P-1.1 a P-1.7 en el formato del protocolo (por que bloquea, que cambia segun la respuesta, supuesto por defecto y riesgo); (0.5) tres puntos diferidos a la ronda 2. Ningun archivo nuevo fue creado: la seccion vive dentro del propio plan.
Justification: DEC-021 dejo como accion siguiente decidir si el plan activo debia re-auditarse contra el nuevo checklist antes de aprobar su congelamiento, y el usuario pidio continuar. La auditoria encontro ambiguedades que habrian entrado al codigo como decisiones silenciosas: (a) el escalado low-inertia recae mayoritariamente sobre la maquina equivalente del bus 39, que concentra ~66% de la inercia del caso y ademas es el slack, de modo que "0.70H" no significa lo que el plan asume; (b) el plan escala las cargas con lambda_L sin decir como sigue la generacion, lo que deja indefinido el despacho previo a la falla y con el la severidad real de T3, T4, T7 y T8; (c) los gates 6/8, 5/8 y 3/4 usan desigualdades estrictas sin margen minimo, de modo que una diferencia dentro del ruido de integracion contaria como victoria y decidiria H1; (d) §21 define f_nadir y RoCoF_max como minimo/maximo "sobre i,t" sin fijar si i recorre las 10 maquinas o los buses, y el caso base solo instancia BusFreq en los buses 30-39; (e) el droop mide frecuencia local mientras DDPG observa 20 senales globales, asimetria de informacion que condiciona como puede enunciarse H1; (f) t_f = 6 s puede truncar el nadir con TGOV1N activo e inercia reducida; (g) §27 propone un arbol de archivos (scripts/, results/, models/) que contradice el arbol de Paper_1 registrado en DEC-020 (src/, experiments/, artifacts/, cases/ieee39/). Cada uno de estos puntos cambia resultados o claims, por lo que se formularon como preguntas en vez de resolverse por cuenta propia; el resto se cerro como supuesto declarado con riesgo, segun exige el protocolo.
Evidence reviewed: lectura completa de `plan_maestro_DDPG_FFC_IEEE39_ANDES.md` (1603 lineas pre-edicion, 1971 post-edicion); inspeccion de solo lectura del caso base con ANDES 2.0.0 sobre `Paper_1/cases/ieee39/base/ieee39_full.xlsx`, que reporto 39 buses, 46 lineas, 19 cargas PQ (5856.4 MW nominales), 10 GENROU en los buses 30-39 con TGOV1N/IEEEX1/IEEEST, H = [43.7, 25.3, 30.2, 33.6, 28.1, 37.8, 27.1, 23.6, 58.1, 599.5], slack en el bus 39 (la misma maquina de H = 599.5), BusFreq instanciado solo en los buses 30-39, un Toggle que desconecta GENROU_1 en t = 12 s, un ACEc en el bus 1 con dos areas, y disponibilidad de ESD1, PVD1, REGCA1, REECA1, REPCA1 y la familia WT* como actuadores candidatos; `requirements-lock.txt` y `requirements.txt` (confirman andes[rl]==2.0.0 y gymnasium==1.3.0, y la ausencia de stable-baselines3 y torch); `Paper_1/README.md` y `find Paper_1 -type f` (arbol real: src/, experiments/, artifacts/, paper/, cases/ieee39/{base,variants}/); DEC-020 (gobernanza minima de Paper_1 y venv compartido); `prompt_maestro_STED_RW.md` v1.1 seccion `PROTOCOLO OBLIGATORIO DE INDAGACION ANTES DE CERRAR EL PLAN`.
Blockers or limitations: El plan permanece `PLAN_DRAFT`: no se autoriza ejecutar nada mas alla de `--stage inspect` hasta que se respondan P-1.1 a P-1.7 o se acepten sus supuestos por defecto. `plan_maestro.md`, declarado por CLAUDE.md como contrato central del repositorio y usado por `ops/checks/session_boot.py` como fuente del gate activo, sigue borrado en el working tree; no se restauro aqui porque la eliminacion pudo ser deliberada y la restauracion es objeto de P-1.7. La contradiccion entre §34 del plan (que exige `Paper_1/ops/sted/` propio) y la gobernanza minima registrada en DEC-020 queda diferida a la ronda 2. No se instalo stable-baselines3 ni torch (S-11 propone hacerlo, sin ejecutar). No se modifico el caso base ni se creo la variante low-inertia. Nada esta commiteado.
Responsible: Claude (auditoria de claridad metodologica bajo el protocolo de DEC-021)
Status: passed
Next action: El usuario responde P-1.1 a P-1.7 o acepta los supuestos por defecto; con eso se cierra la ronda 1, se actualiza la seccion 0 del plan y, si no quedan puntos abiertos, el plan pasa a PLAN_FROZEN y se autoriza el gate G0 completo.

## DEC-023
Date: 2026-08-18
Gate: governance (enmienda a DEC-020, arbol STED propio para Paper_1; sin gate de paper de la raiz)
Decision: Se crea `Paper_1/ops/sted/{traceability_matrix.csv,test_plan.md,decision_log.md}`, enmendando la gobernanza minima de DEC-020 ("no dedicated plan_maestro.md, no gate track of its own") para Paper_1. Esto ejecuta la decision de usuario ya registrada dentro de `plan_maestro_DDPG_FFC_IEEE39_ANDES.md` (Seccion 0.5, punto 2, ronda 1: "arbol propio en `Paper_1/ops/sted/`") y resuelve la contradiccion entre esa decision y DEC-020 que DEC-022 dejo diferida a la ronda 2. A partir de ahora, toda decision de gate propia de `Paper_1` (LI-1, placement freeze, split freeze, droop freeze, seleccion de checkpoint, etc., conforme a `plan_maestro_DDPG_FFC_IEEE39_ANDES.md` SS27/SS34) se registra en `Paper_1/ops/sted/decision_log.md`, nunca en este archivo ni en el `plan_maestro.md` de la raiz -- ambos siguen gobernando exclusivamente el paper Wide-Area Control (Gate G1).
Justification: Al ejecutar la etapa P1-E0 (--stage inspect) del plan de Paper_1, se encontro que `Paper_1/ops/sted/` no existe en disco, pese a que SS0.5/SS27/SS34 del plan lo dan por resuelto y afirman explicitamente que la decision "quedo registrada como enmienda a DEC-020 via una nueva entrada DEC-021". Se verifico que el DEC-021 real de este log (arriba) trata de un tema distinto y no relacionado -- la adicion del protocolo de indagacion obligatoria a `prompt_maestro_STED_RW.md` -- no la gobernanza de Paper_1. Es decir, el plan cita un numero de decision que nunca correspondio a esa decision; el registro nunca se hizo pese a que el plan avanzo (rondas 2 y 3) asumiendo que si. Se presento la discrepancia al usuario junto con las tres opciones posibles (crear el arbol ahora, mantener gobernanza minima y readaptar el plan, o detenerse a esperar instruccion); el usuario eligio explicitamente crear el arbol y continuar a P1-E1.
Evidence reviewed: `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md` SS0.5 punto 2, SS27 ("Regla de registro"), SS34 (arbol minimo STED-RW); lectura completa de DEC-020 y DEC-021 en este archivo (lineas 379-400), confirmando que DEC-021 no contiene ninguna mencion a Paper_1, arbol STED, traceability_matrix, test_plan ni decision_log de Paper_1; `find Paper_1 -type d` confirmando la ausencia de `Paper_1/ops/`; respuesta explicita del usuario a la pregunta de gobernanza planteada en esta sesion.
Blockers or limitations: Los tres archivos creados en `Paper_1/ops/sted/` arrancan vacios/con plantilla (sin filas de evidencia todavia) porque ninguna etapa posterior a P1-E0 se ha ejecutado aun. Esta entrada no reabre ni corrige retroactivamente DEC-021 (que sigue siendo valida para su propio tema); simplemente deja constancia de que la referencia cruzada del plan a "DEC-021" para este topico es incorrecta y que este es el registro correcto. `plan_maestro.md` de la raiz sigue borrado en el working tree (P-1.7, fuera de alcance de esta sesion, sin cambios).
Responsible: Claude (ejecucion de P1-E0 del plan de Paper_1, discrepancia de gobernanza escalada al usuario y resuelta segun su decision explicita)
Status: passed
Next action: Continuar con P1-E1 (construccion del caso low-inertia y Gate LI-1) segun `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md` SS31/SS5.3, registrando su resultado en `Paper_1/ops/sted/decision_log.md`.

## DEC-024
Date: 2026-08-19
Gate: governance (limpieza de duplicado, sin cambio de contenido cientifico)
Decision: Se elimina el archivo duplicado y obsoleto `plan_maestro_DDPG_FFC_IEEE39_ANDES.md` en la
raiz del repositorio (via `git rm`). Es la copia original del commit `b652e68` ("Add Paper_1
workspace..."), nunca actualizada desde entonces (2689 lineas); la copia canonica y activamente
mantenida durante toda la campana P1-E0-P1-E7 es `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`
(2758 lineas: S-01 revisado a ~40 mHz, BESS sizing 0.50x, correccion Pext0/DEC-P1-016, etc.). El
propio plan ya instruia moverlo a `Paper_1/` en su paso P1-E0.6 ("mover este documento a
`Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`"); la copia de raiz nunca se borro tras esa mudanza.
Justification: Instruccion explicita del usuario al abrir la campana P2 ("sin eliminar o modificar
los resultados ya obtenidos, colocar todo lo necesario dentro de paper 1"). Mantener dos copias
divergentes del mismo documento (una congelada en el commit inicial, otra con 20+ decisiones
posteriores) es un riesgo de que alguien lea la version equivocada; no hay ningun resultado de P1
que dependa de la copia de raiz -- todo el trabajo de esta sesion siempre leyo/escribio
exclusivamente `Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md`.
Evidence reviewed: `diff` confirmando que ambos archivos difieren (2689 vs 2758 lineas); `git log
--oneline -- plan_maestro_DDPG_FFC_IEEE39_ANDES.md` (una sola entrada, el commit inicial) vs `git
log --oneline -- Paper_1/plan_maestro_DDPG_FFC_IEEE39_ANDES.md` (multiples commits durante P1-E1 a
P1-E7); `grep` confirmando que ningun otro archivo del repo referencia la ruta de raiz de forma que
dependa de su existencia fisica (solo se citaba por nombre de archivo, no por ruta absoluta).
Blockers or limitations: `plan_maestro.md` de la raiz sigue borrado en el working tree (P-1.7,
inventariado en DEC-023, fuera de alcance de esta sesion, sin cambios). No relacionado con esta
entrada.
Responsible: Claude (instruccion explicita del usuario al iniciar la campana Paper_2)
Status: passed
Next action: Ninguna accion adicional sobre la raiz; el trabajo continua en `Paper_2/` (ver
`Paper_1/ops/sted/decision_log.md` para la entrada que registra el nacimiento de Paper_2 a partir de
los hallazgos de Paper_1).
