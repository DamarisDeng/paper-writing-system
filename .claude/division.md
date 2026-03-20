# BST236 Midterm project 

Given any public health dataset, this system generates a JAMA Network Open–style research paper. The pipeline has three layers: data analysis, orchestration, and paper writing. 

## Workflow
1.	EDA and data cleaning
2.	generate metadata (column names, data type, missingness, # of valid data)
3.	Research question generation
4.	Study design 
5.	Analysis
6.	visualization
7.	paper writing
8.	paper review and revision
9.	LaTeX paper generation

|     Step                            |     Input                                   |     Output                     |
|-------------------------------------|---------------------------------------------|--------------------------------|
|     EDA                             |     raw.csv   (or more than one)            |     cleaned_data.csv           |
|     Generate metadata               |     cleaned_data.csv                        |     profile.json               |
|     Research question generation    |     profile.json                            |     research_questions.json    |
|     Study design                    |     research_questions.json                 |     study_plan.json            |
|     Analysis                        |     cleaned_data.csv   + study_plan.json    |     results.json               |
|     Visualization                   |     results.json                            |     figures/,   tables/        |
|     Paper writing                   |     results.json   + study_plan.json        |     manuscript.json            |
|     Latex generation                |     manuscript.json                         |     paper.tex                  |
|     Paper review                    |     paper.pdf                               |     revision   ideas           |
|     Paper revise                    |     Paper.tex                               |     revised_paper.tex          |


## Person 1
Data analysis pipeline - Responsible for deterministic data processing and statistical results.

Tasks:
1.	Load and clean datasets, save the cleaned dataset
2.	Perform data profiling (generate profile.json), should contain all summary information about the dataset
3.	Detect variable types and missingness
4.	Implement statistical functions (descriptive stats, linear/logistic regression)
5.	Generate tables and figures (results.json, tables/, figures/) 
This person only need to write functions that conduct statistical test and plot, person 2 will write agent/skills that use these tools.

## Person 2
Research logic, pipeline orchestration, paper revision - Responsible for automation and workflow control.

Tasks:
1.	Generate candidate research questions from profile.json
2.	Select a feasible study design and produce study_plan.json
3.	Map outcome types to analysis methods
4.	Implement the main pipeline (run_pipeline.py or orchestrator agent) that executes each stage
5.	Validate consistency between outputs

# Person 3 
Paper Writing, LaTeX Generation, paper review - Responsible for converting results into a JAMA style paper.
Tasks:
1.	Generate paper sections (abstract, introduction, methods, results, discussion) using structured outputs (manuscript.json)
2.	Generate references or literature summaries
3.	Fill the LaTeX template (template.tex)
4.	Insert tables and figures and compile the final paper.pdf
