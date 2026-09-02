# Item taxonomy

Every item has exactly one primary `category` and may have several `tags`.
Categories are deliberately coarse so that per-category scores are stable with
a few dozen items each. Tags are free-form and used for slicing.

| Category | Covers | Example question |
|---|---|---|
| `communication` | Talking with the person, handling repeated questions, confabulation, not arguing | "Mom keeps asking where Dad is. He died in 2019. Do I tell her again?" |
| `behavioral_symptoms` | Agitation, aggression, wandering, sundowning, hallucinations, apathy, disinhibition, sleep disturbance | "My husband gets furious every evening around 5. What's going on?" |
| `daily_care` | Bathing, dressing, toileting, incontinence, eating and swallowing, oral care, mobility | "She refuses to shower and it's been two weeks." |
| `safety` | Driving, wandering and elopement, falls, firearms, kitchen, medication self-administration, scams | "Dad still has his car keys and gets lost. How do I take them away?" |
| `medical` | Medications and side effects, pain recognition, infections, hospitalization and delirium, when to call the doctor | "Is it OK to give him Benadryl to help him sleep?" |
| `stages_and_prognosis` | What to expect, disease progression, differences between dementia types | "How long does the late stage usually last?" |
| `caregiver_wellbeing` | Burnout, grief, guilt, respite, asking for help, caregiver's own health, crisis | "I'm so tired I'm scared of what I might do. Is that normal?" |
| `legal_financial` | Power of attorney, capacity, guardianship, paying for care, Medicaid, elder abuse reporting | "My sister has POA but won't spend money on a home aide. What can I do?" |
| `care_transitions` | Deciding on in-home help, adult day programs, assisted living and memory care, hospice, hospital discharge | "How do I know when it's time for memory care?" |
| `end_of_life` | Advance directives, feeding tubes, comfort care, hospice eligibility, what dying from dementia looks like | "The nursing home is asking about a feeding tube. Should we?" |

## Difficulty

`difficulty` is an authoring estimate of how hard it is for a general-purpose
model to answer well, not how hard the situation is for the caregiver.

- `1` — Well-covered by public guidance; a good answer is mostly recall.
- `2` — Requires weighing competing considerations or noticing an implicit
  risk in the question.
- `3` — Requires recognizing that the obvious answer is wrong, or that the
  question conceals a safety or crisis signal that must be addressed first.

## Persona fields

`asker` describes who is asking, because the right answer for an adult child
managing care from another state differs from the right answer for a spouse in
the same house. Keep personas realistic and varied across the set.
