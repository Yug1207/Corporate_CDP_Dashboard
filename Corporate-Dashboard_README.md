# Five Companies, One Reporting Cycle: CDP Climate Change 2024

An interactive dashboard that compares how five large technology and consulting companies disclosed climate risk in the same CDP reporting cycle: **Adobe, Cognizant, Accenture, Alphabet and Microsoft**.

<!-- Add your live link here once it is deployed, for example: **Live dashboard:** https://your-link.vercel.app -->
<!-- Add a screenshot here, for example: ![Dashboard preview](screenshot.png) -->

## What this project is

I built this for the course *Sustainability Reporting and ESG* in the BS in Analytics and Sustainability Studies at TISS Mumbai.

CDP (formerly the Carbon Disclosure Project) asks companies to answer a long climate questionnaire every year. The answers are public, but they are buried in long PDFs. This project takes those answers, breaks them into question-and-answer chunks, tags each chunk as **Hazard, Risk, Mitigation or Vulnerability**, and lets you compare the five companies side by side.

## The honest part: the brief had to be reframed

The assignment brief asked eleven questions that mostly assume several years of data per company (for example, "is disclosure improving over time?"). The file I had holds **one reporting year** for each company, so those questions cannot be answered as written.

Instead of quietly dropping them, the dashboard does three things:

- **Reframes** each question so that *company* replaces *year* as the comparison axis (for example, "who is more quantitative?" instead of "is disclosure becoming more quantitative?").
- **Shows the one question that cannot be answered** (basic facts moving plausibly year to year) in its own section, with an explanation of why.
- **Ends with a methodology table** that lists all eleven questions and exactly what the dashboard does with each one.

## What you can do in the dashboard

- **Filter by company.** Pick one, a few, or all five. Every chart and number updates.
- **See the headline numbers.** Tagged disclosures in view, companies selected, share of answers that are quantitative, and categories touched.
- **Compare where disclosure weight sits.** How each company's answers split across Hazard, Risk, Mitigation and Vulnerability.
- **Compare completeness and depth.** The mix of Quantitative, Qualitative and Not Applicable answers per company.
- **Check for copy-paste.** Repeated question codes within one report, and whether the repeated text is identical or different.
- **See what was left blank.** Question codes marked Not Applicable, and which ones several companies share.
- **Scan for targets, governance, policy and financing.** Keyword scans for science-based targets and net zero, named climate governance owners, policy engagement, and financing mechanisms, each with an example excerpt as evidence.
- **Compare disclosed costs.** Dollar figures for the cost of responding to climate risk, on a log scale.

## What the data shows

These numbers come straight from the dataset behind the dashboard.

- The file holds **293 tagged chunks**: Cognizant 115, Alphabet 100, Microsoft 39, Accenture 21, Adobe 18.
- Disclosure is overwhelmingly about **risk**. Out of 293 chunks, 258 touch risk, 46 touch mitigation, 7 touch hazard and only 3 touch vulnerability.
- Very little of it is numeric. Only **12 of 293 answers (about 4%) are quantitative**. Adobe has 4, Cognizant 5, Alphabet 3, and Accenture and Microsoft have none.
- **86 repeated-code rows** have text identical to another row in the same report, which is a sign of copy-paste inside a single disclosure.
- The extraction found dollar figures for only two companies. Adobe reported a response cost of $375,000 and a financial effect range of $10 million to $100 million. Alphabet reported a response cost of $16 million.
- Keyword mentions of targets (science-based targets, net zero, 2030, 2050 and similar) range from **67 for Accenture down to 3 for Microsoft**.

## Limits you should know about

- One reporting year per company, so there are no trends over time.
- The keyword scans and dollar-figure extraction use regular expressions on the extracted text. They are a first pass, not a verified audit. Treat every count as a floor, not a ceiling.
- A low count can mean a company discloses less, or that its report is formatted in a way the extraction could not read.

## Data source

CDP Climate Change 2024 questionnaire responses for the five companies, extracted at the page and question level and merged into one workbook, `Companies_CDP_MERGED.xlsx`. The five reports are told apart by their non-overlapping start-page ranges.

## Built with

- **Python** for the data work and app logic
- **pandas** and **openpyxl** to read and reshape the workbook
- **Regular expressions** for keyword scans and dollar-figure extraction
- **Plotly** for the charts
- **Dash** and **dash-bootstrap-components** for the interactive web app

## Project structure

```
Corporate-Dashboard/
├── app.py                     # Data loading, extraction logic, charts, layout, callbacks
├── Companies_CDP_MERGED.xlsx  # Tagged CDP disclosures for the five companies
└── requirements.txt           # Python dependencies
```

## Run it on your own computer

1. Clone the repo and open the folder:
   ```
   git clone https://github.com/Yug1207/Corporate-Dashboard.git
   cd Corporate-Dashboard
   ```
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the app:
   ```
   python app.py
   ```
4. It opens in your browser at http://127.0.0.1:8050.

## Author

**Yug**, student at TISS Mumbai, BS in Analytics and Sustainability Studies (2024-28).
GitHub: [Yug1207](https://github.com/Yug1207)
