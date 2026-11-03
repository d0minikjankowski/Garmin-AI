# Garmin AI Training Assistant

A personal Python application that combines Garmin running history with sleep, HRV, and Body Battery data to generate a training report using the OpenAI API.

The current version runs locally on **Windows with PowerShell**. The application messages and AI reports are currently in Polish; this README is in English.

## Features

- Fetches up to **50 recent running activities** through Garmin Personal API.
- Fetches **14 calendar days of recovery data**, including the current, potentially incomplete day.
- Calculates running pace and formats duration in Python before sending data to AI.
- Summarizes sleep duration, sleep score, nightly and weekly HRV, Garmin HRV status, and available Body Battery samples.
- Calculates the number of runs and the running distance within the latest seven calendar days.
- Generates a report containing deterministic summaries followed by AI interpretation.
- Skips the OpenAI request when the prepared input and tracked program version have not changed and the saved report is intact.
- Supports forced analysis and recovery-only data collection.
- Stores API keys locally using Windows account-bound encryption.

## How it works

```text
Garmin Personal API
        |
        +-- Up to 50 running activities
        +-- 14 days of sleep, HRV, and Body Battery
        |
Python validation and summaries
        |
Change detection
        |
        +-- Unchanged input -> reuse the previous report
        +-- Changed input / forced run -> OpenAI analysis
                                             |
                                      Local text report
```

Garmin data is fetched on each normal run. Change detection skips the **OpenAI analysis**, not data retrieval. The retrieval timestamp alone does not trigger a new analysis; changing date windows, prepared measurements, or the main program can do so.

## Requirements

- Windows and PowerShell.
- Python with the `venv` module.
- A Garmin account, a Garmin Personal API key, and access to the requested data.
- An OpenAI API key with access to the configured model and available API credits.
- Internet access for data collection and AI analysis.

The project uses `garmin-connect-personal-api-python` and `openai`. The existing development environment used versions `1.0.0` and `3.42.1`, respectively. The repository does not yet include a dependency lock file.

## Installation

Clone or download the repository, then open PowerShell in the project directory.

Create a virtual environment and install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install garmin-connect-personal-api-python openai
```

**Adjust the launcher before using a different checkout location.** The current `start_garmin_ai.ps1` contains a development-machine-specific Python path. Replace its `$python = ...` line with:

```powershell
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
```

This makes the launcher use the virtual environment inside your project directory.

If PowerShell blocks script execution, review the execution policy applicable to your computer before proceeding. Managed computers may require administrator assistance.

## Configure API keys

Run:

```powershell
.\start_garmin_ai.ps1 -Configure
```

Enter the OpenAI API key and Garmin Personal API key at the hidden prompts. Do not paste keys into source files, GitHub issues, or chat messages.

The launcher stores the keys in `.secrets.clixml` using PowerShell's Windows encryption for secure strings. This file is tied to the Windows user and computer that created it. Configure the keys again when moving to another computer or Windows account.

At runtime, the launcher exposes the required keys to the Python process through environment variables and restores the previous environment values afterward. The Python code keeps Garmin bearer tokens in memory instead of writing the library's default token cache.

## Usage

### Fetch data and generate a report

```powershell
.\start_garmin_ai.ps1
```

The application:

1. Requests up to 50 running activities.
2. Fetches sleep, HRV, and Body Battery data.
3. Validates and summarizes the data.
4. Generates an AI report or reuses the previous report if its input is unchanged.

If fewer runs are available, the application analyzes the available running records.

### Force a new AI analysis

```powershell
.\start_garmin_ai.ps1 -Force
```

This makes a new OpenAI request even when the prepared input has not changed. API usage may incur charges.

### Collect recovery data without AI

```powershell
.\start_garmin_ai.ps1 -Recovery
```

This fetches recovery data, saves the raw responses locally, and prints a bounded inventory of response fields and types. It does not call OpenAI. Do not combine `-Recovery` with `-Force`.

### Summarize previously collected recovery data

```powershell
.\.venv\Scripts\python.exe .\recovery_summary.py
```

This reads `recovery_data.json` and writes `recovery_summary.txt` without calling either API.

### Check an existing activity export offline

```powershell
.\.venv\Scripts\python.exe .\garmin_ai.py --offline .\activities_history.json
```

This validates a previously saved activity export and previews formatted values. It does not download data, generate an AI report, or write output files. The activity export is not included in the repository.

## Project files

| File | Purpose |
| --- | --- |
| `garmin_ai.py` | Main pipeline: data retrieval, validation, summaries, change detection, and AI analysis. |
| `start_garmin_ai.ps1` | Windows launcher and encrypted credential configuration. |
| `recovery_probe.py` | Recovery data retrieval and response structure inspection. |
| `recovery_summary.py` | Local recovery summaries with no API requests. |
| `ai_analysis.py` | Earlier standalone CSV analysis prototype. |
| `analyze_history.py` | Earlier activity-history processing prototype. |
| `analyze_activity.py` | Earlier single-activity reporting prototype. |

Use `start_garmin_ai.ps1` for the current integrated workflow. The earlier scripts are retained as development history and do not provide all current safeguards or features.

## Generated local files

| File | Contents |
| --- | --- |
| `running_history.csv` | Processed running records, including numeric and formatted duration/pace fields. |
| `recovery_data.json` | Raw recovery responses, source statuses, date range, and retrieval timestamp. |
| `recovery_summary.txt` | Daily recovery measurements and available-data averages. |
| `raport_ai.txt` | Program-generated summaries followed by AI interpretation. |
| `analysis_state.json` | Input signature, report checksum, and last successful report timestamp. |
| `.secrets.clixml` | Encrypted local API keys. |

These files are local application state and personal data, not repository source files.

## Configuration and personalization

The current main script uses:

| Setting | Current value |
| --- | --- |
| Running activity request limit | 50 |
| Recovery date window | 14 calendar days |
| OpenAI model | `gpt-5-mini` |
| Reasoning effort | `low` |
| Maximum output tokens | 8,000 |

These settings are currently defined in code rather than a configuration file.

The AI instructions also contain the original user's training schedule and a dated race goal. **Review and replace that personal context in `analyze()` before using the project for another person or training cycle.** This project currently supports one user; it is not a multi-user service.

## Data handling and privacy

- The integrated workflow sends prepared running and recovery summaries to OpenAI for analysis.
- API keys and raw Garmin profile identifiers are not included in the analysis payload.
- Raw recovery responses remain in the local JSON file and may contain personal identifiers.
- The OpenAI request sets `store=False`; this is not a claim that no provider-side retention can occur.
- Keep secrets, personal measurements, reports, and virtual environments out of Git.
- A private repository is not a substitute for excluding credentials and personal data.

Ensure `.gitignore` includes at least:

```gitignore
.secrets.clixml
.env
.venv/
__pycache__/
activities_history.json
activity_latest.json
running_history.csv
recovery_data.json
recovery_summary.txt
raport_ai.txt
analysis_state.json
*.tmp
```

Before publishing, inspect the staged file list and diff. Adding an entry to `.gitignore` does not remove files that Git already tracks or erase earlier commits. If a key was committed or otherwise exposed, revoke it and create a replacement.

## Interpretation limits

- Average session pace is not interval pace or a measured race-performance prediction.
- Duration is total session duration; it is not an average.
- Missing measurements are kept separate from zero values.
- Recovery summaries show how many days have usable measurements.
- Body Battery minimum and maximum are calculated from the returned samples. They may not represent the actual daily extremes.
- The last Body Battery sample is not necessarily an evening measurement.
- Garmin HRV status is reproduced from the source; it is not a diagnosis or proof of complete recovery.
- Today's recovery data may be incomplete.
- AI interpretation can contain errors even when the deterministic summaries are correct. Check important claims against the source measurements.

The application is a personal training-data assistant, not a medical diagnostic tool.

## Error handling

- Invalid running measurements stop analysis rather than being silently interpreted.
- Recovery endpoint failures are recorded and stop the integrated AI analysis; an older recovery file is not substituted as if it were current.
- An empty recovery response is distinct from a request failure and can appear as missing data.
- Incomplete or empty AI output is rejected.
- Analysis state is updated only after a complete report has been saved successfully.
- A missing or changed report prevents reuse of the saved analysis state.
- Console errors avoid printing raw API error bodies that could expose sensitive information.

If a run fails, read the displayed stage and error category. Verify key configuration, network access, API access, and file permissions as appropriate. Do not share credentials when reporting a problem.

## Current status and roadmap

Implemented: a local Windows workflow for running and recovery data, deterministic summaries, AI interpretation, and report reuse.

Planned, **not yet implemented**:

- A private browser-based dashboard usable from a phone or another computer.
- User authentication and cloud deployment.
- Durable database storage for history and reports.
- Scheduled background synchronization.
- Configuration outside the source code.
- More complete automated testing and dependency management.

The current version requires manual execution and a local Python environment. Publishing its source code to GitHub alone does not make it an online application.
