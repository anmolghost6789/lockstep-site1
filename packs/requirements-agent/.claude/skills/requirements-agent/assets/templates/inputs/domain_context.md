# Domain Context

> Describe the actual business domain, terminology, operating model, data, and
> governing constraints. The agent derives context from this evidence rather
> than selecting a package-defined profile.

## Domain Overview
- **Business Domain:** [domain and operating context]
- **Key Business Functions:** [functions, decisions, and workflows in scope]

## Domain Terminology
| Term | Definition |
|------|-----------|
| [e.g., TRx] | [Total prescriptions — includes new and refill] |
| [e.g., NRx] | [New prescriptions only] |
| [e.g., HCP] | [Healthcare Professional — physician, prescriber] |
| [e.g., SFE] | [Sales Force Effectiveness] |
| [e.g., NPA] | [National Prescription Audit — national-level sales data] |

## Data Sources in This Domain
| Source | Vendor | Data Type | Description |
|--------|--------|-----------|-------------|
| [system name] | [provider or owner] | [system type] | [purpose and relevant information] |

## Regulatory Constraints
- [e.g., Patient data must be de-identified per HIPAA Safe Harbor rules]
- [e.g., Prescriber data subject to Sunshine Act reporting requirements]
- [e.g., Incentive compensation data has SOX audit requirements]

## Domain-Specific Metrics
- [e.g., Market share = brand TRx / total therapeutic class TRx]
- [e.g., Call plan compliance = actual calls / planned calls by territory]
- [e.g., Formulary access = covered lives with unrestricted access / total covered lives]

## Known Domain Challenges
- [e.g., Patient IDs are anonymized differently across vendors — cannot join across sources]
- [e.g., Territory alignments change quarterly, requiring point-in-time reporting]
- [e.g., Multiple data vendors provide overlapping but non-identical datasets for the same metric]
