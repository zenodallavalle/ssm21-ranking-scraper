# ssm21-scraper

- [ssm21-scraper](#ssm21-scraper)
  - [Description](#description)
  - [Features](#features)
  - [Usage](#usage)

## Description

A simple and **rapid** python script to scrape SSM-21 ranking in MS Excel format that can also compute minimum points required for every combination of residency, place and type of contract.

_An universitaly account is required. You also need to be signed-up for SSM-21 in order to see the ranking._

Un semplice e **rapido** script in python per scaricare la graduatoria SSM-21 in formato MS Excel che può anche calcolare i punteggi minimi per accedere a ogni combinazione di specializzazione, sede e tipo di contratto.

_Per poter visualizzare la graduatoria è necessario possedere un account universitaly ed essere iscritti al concorso SSM-21._

## Features

- **Pretty fast** (<10 seconds on my Intel i7-4710HQ);
- **Multiprocess-enabled** (default is number of processes = number of cores);
- Length dinamically determinated;
- Don't need selenium webdriver;
- Relatively light dependancies;
- Can compute minimum points per combination of residency, place and type of contract;
- Can be imported and called on-demand;

## Usage

1. Create and activate virtual env

   <code>python -m venv env</code>

   on windows <code>env\Scripts\activate</code>

   on linux or mac os <code>. env/Scripts/activate</code>

2. Install dependancies with

   <code>pip install -r requirements.txt</code>

3. Edit `credentials_model.json` and rename it to `credentials.json`:

   1. Edit email

   2. Edit password

4. Customize (if required)

5. Run

   <code>python ssm21_rank_scraper.py</code>
