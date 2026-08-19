# Theme Selection

Use this reference after the document type, audience, tone, information relationship, and density are known. It governs both the Feishu whiteboard and the self-contained HTML page.

## Contract

- Select exactly one allowed theme for every visual output. There is no fixed or silent default.
- Record the selected name in `visual_spec.style` and a short content-based reason in `visual_spec.style_rationale`.
- Use that same theme for the one-picture visual, body figures, and HTML page tokens. Do not mix themes within one artifact.
- Never print the theme name or selection rationale in the reader-facing document.
- Theme colors control page background, surfaces, rules, type contrast, and non-semantic accents only. The semantic colors in `config/3080-brief.json` still own favorable, unfavorable, warning, neutral, and unknown meaning.
- Reject banned or unknown names. The runtime registry is `assets/themes/beautiful-feishu-themes.json`.

## Selection Order

Choose from content fit, in this order:

1. **Document job:** research, decision, review, roadmap, experiment, launch, operations, learning, or general explanation.
2. **Reader and formality:** institutional or high-stakes work favors restrained/high-formality themes; team workflow or onboarding can use balanced or bold themes.
3. **Narrative energy:** analytical, editorial, action-oriented, product-led, or celebratory.
4. **Density and relationship:** dense evidence needs quiet surfaces and strong rules; a short sequence or launch story can tolerate stronger graphic accents.
5. **User preference:** an explicit allowed choice wins when it does not conflict with readability or semantic meaning.

Do not choose from personal taste alone. Do not reuse the last theme merely because it rendered successfully.

## Candidate Guide

The guide narrows candidates; it is not a default mapping.

| Content and reader need | Strong candidates |
| --- | --- |
| Data, experiment, technical comparison | Avocado Press, Jade Lens, Cut Bloom |
| Strategy, policy, consequential decision | Jade Lens, Editorial Forest, Bold Poster |
| Research, review, long-form explanation | Reading Room, Papier Bleu, Editorial Forest |
| Product plan, roadmap, operational sequence | Apricot Arc, Pin & Paper, Long Table |
| Product, growth, launch, feature comparison | Berry Pop, Lime Slab, Grove Block |
| Workshop, onboarding, team workflow | Checker Bloom, Mint Brut, Court Press |
| Short showcase or energetic announcement | Salmon Stamp, Specimen Bold, Stencil & Tablet |

Use restrained themes when evidence density or decision risk is high. Use bold themes only when the source is compact enough that stronger display treatment does not compete with the argument.

## Format Adaptation

### Feishu

Read the selected theme's original `design.md` from `beautiful-feishu-whiteboard` and express it with editable native SVG shapes. Preserve its visual character while following 3080 readability, evidence, and semantic-color rules.

### HTML

Use the bundled, MIT-attributed adaptation in `assets/themes/beautiful-feishu-themes.json`. It translates the same theme into page tokens for background, surfaces, rules, type contrast, spacing, borders, and figure colors. It does not copy external runtime code or require the source style skill after installation.

## Quality Gate

FAIL when:

- no theme is selected, the name is banned/unknown, or the reason is missing;
- the theme conflicts with the document's formality, density, or reader context;
- HTML and the visual use different themes;
- a theme remaps semantic evidence colors;
- multiple outputs requested as different styles differ only by palette rather than composition and narrative treatment.
