# quest program study list

last updated 2026 08 24

this file records which quest programs have been explained and what each program does

## explained programs

| program | status | top summary comment | purpose |
| --- | --- | --- | --- |
| [ScenarioDefinition.cs](./ScenarioDefinition.cs) | explained | present | stores fixed scenario rules rewards target data and safe facts for the llm |
| [GeneratedNarrative.cs](./GeneratedNarrative.cs) | explained | present | stores story text returned by the backend or unity local fallback |
| [NarrativeGenerationRequest.cs](./NarrativeGenerationRequest.cs) | explained | present | turns one scenario into backend request data with continuity and tone |
| [NarrativeTestProvider.cs](./NarrativeTestProvider.cs) | explained | present | creates fixed local story text when backend text cannot be used |
| [NarrativeValidator.cs](./NarrativeValidator.cs) | explained | present | checks generated story fields lengths and required objective amount |
| [NarrativeApiClient.cs](./NarrativeApiClient.cs) | explained | present | sends story requests and gameplay logs through http coroutines |
| [QuestManager.cs](./QuestManager.cs) | explained | present | coordinates scenario selection narrative targets progress rewards ui continuity and logs |
| [ScenarioTargetResetter.cs](./ScenarioTargetResetter.cs) | explained | present | saves scene target templates and creates fresh gameplay targets for each scenario |
| [QuestUI.cs](./QuestUI.cs) | explained | present | creates the runtime quest panel and changes its layout from quest manager state |

## partly explained programs

| program | current coverage | next step |
| --- | --- | --- |
| [Backend app.py](../../../Backend/app.py) | python fallback and narrative tone were explained | read the complete backend next |

## recommended reading flow

```text
scenario definition
→ narrative generation request
→ narrative api client
→ generated narrative
→ narrative validator
→ quest manager
→ scenario target resetter
→ quest ui

backend or validation failure
→ narrative test provider
→ narrative validator
→ quest manager
```

## main system rule

```text
scenario data controls gameplay
narrative data controls player facing story text
the llm never controls gameplay mechanics
```
