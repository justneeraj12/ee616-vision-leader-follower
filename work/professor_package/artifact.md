# Template execution contract

## Reference

- Path: `/home/justneeraj/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-system-design/assets/reference.docx`
- SHA-256: `13504f6c221a42c1726460a9e865e563355539ff97d702d6c9b2267b4b261d76`
- Rendered pages: 7
- Sections: 1
- Evidence: `template-reference-render/`, `template-style-evidence.json`, section, heading, image, field, footnote, and content-control audits run on 2026-09-14

## Page system

- Letter portrait, 8.50 x 11.00 inches
- Margins: left 0.70, right 0.70, top 0.70, bottom 0.62 inches
- One section with different first-page header and footer behavior
- Header and footer distances and all section properties remain inherited from the reference

## Typography and color

- Embedded Helvetica Neue family from the reference controls the visual system
- Title page uses the reference title hierarchy: light blue-gray system label, large dark navy proposal title
- Body headings use the reference dark navy Heading 1 treatment and gray-blue Heading 3 treatment
- Body text remains approximately 11 point with the reference paragraph rhythm and line spacing
- Headings and title are black or reference dark navy; no decorative paragraph borders

## Tables and lists

- Reuse reference dark navy table headers with white text, alternating pale blue and pale gray body rows, white/light-gray borders, and generous cell padding
- Use short numbered or bulleted lists only where the reader must compare parallel items or follow a sequence
- No fixed row heights; all narrative cells wrap and expand

## Components

- Cover page with status, owner, update date, author, reviewer, course, and scope metadata
- Numbered Heading 1 sections
- One full-width architecture figure with caption
- Compact metric, experiment, risk, literature, and milestone tables
- Footer derived from the reference and changed to `EE 616 Project Update | Neeraj Kumar Kanchani`
- References and email draft are appendices, not placeholders

## Content flow

1. Executive summary and review request
2. Academic context and revised scope
3. Research questions, hypotheses, and measurable targets
4. Proposed architecture and component responsibilities
5. Preliminary experiment and planned figures
6. Evaluation protocol and data contracts
7. Hardware and implementation constraints
8. Milestones through the first week of December 2026
9. Risks and mitigations
10. Related work and technical foundations
11. Decisions requested from Professor Imtiaz
12. Draft email
13. References

## Slot map

- `word/document.xml`: all placeholder body content is editable and will be replaced with project-specific material while preserving the reference section properties and visual vocabulary
- `word/header*.xml` and `word/footer*.xml`: text is editable; layout and paragraph properties are preserve-only
- `word/styles.xml`, `word/numbering.xml`, embedded fonts, theme, and relationships: preserve-only
- `word/media/image1.png`: template placeholder architecture diagram may be replaced by a project-specific diagram while preserving its full-width figure role
- Reference footnote placeholder is removed because the new document does not require a footnote
- No content controls or fields are present

## Package preservation

- Preserve all package parts except `word/document.xml`, header/footer text nodes, document relationships required for the new figure, and media required for the new figure
- Preserve page geometry, embedded fonts, styles, numbering, theme, and content types
- Retained reference must remain unchanged at the recorded SHA-256

## Fidelity gates

- Final document must remain recognizably derived from the reference cover, heading, table, figure, and footer system
- Render and inspect every page at 100 percent zoom
- No placeholder brackets, clipped text, split headings, unexplained blank pages, or broken tables
- Final package must distinguish measured facts from proposed targets and planned evidence
- DOCX and PDF must contain identical content
