# Midterm Project: Automatic End-to-End AI Workflow for Journal Paper Generation

## Overview


This midterm project challenges you to develop an automatic end-to-end AI workflow for JAMA Network Open paper generation. You will need to develop a workflow that can automatically generate a JAMA Network Open paper from any datasets. The workflow should be as automatic as possible with the minimum human intervention including but not limited to the automatic steps like:

- research question formulation
- data exploration
- statistical modeling 
- data analysis and visualization
- paper writing
- literature review and reference generation
- paper reviewing and revision

Your workflow should be generic enough to be applied to any datasets. We provide you with a sample dataset in the `./sample/data` folder and the real JAMA Network Open paper in the `./sample/output/paper.pdf`. You can use this sample dataset to design and test your workflow. The goal is to automatically generate a JAMA Network Open paper using the template in the `./sample/tex/template.tex` file.

To test your workflow, we will have an **onsite midterm exam** on March 24th in class. We will provide you in the exam a new datasets and you will need to automatically generate a JAMA Network Open paper using your workflow with the minimum intervention. You will be provided a folder like `exam_folder_sample` when the exam starts. And you need to submit a `paper.pdf` file in canvas before the class ends.
We will also ask you to submit your whole workflow folder with all the agents, skills, code, data, and output in the midterm github repository later. 

You also need to write a tutorial about how to design the workflow and how to organize the agents or skills. 


## Milestones and Deliverables

You will finish the midterm project with the same code squad as the usual homework. All the milestones and deliverables below will be finished as a squad joint work. You can use all AI tools you want to.


There are three milestones for the midterm project:

- **Midterm Exam** (March 24th in class): You will be provided a new datasets when the exam starts and you will need to automatically generate a JAMA Network Open paper using your workflow with the minimum intervention. 
  - Turn in a `paper.pdf` file in canvas before the class ends. You should prepare beforehand the workflow and let it run automatically during the exam. You should intervene as little as possible during the exam. **At least one squad member should be present in class during the exam to implement the workflow onsite.**
  - Record your screen during the exam using zoom and post the link to recording to canvas by the noon of the day of the exam.

- **Midterm Project Repository** (due March 26th): Github repository (just like the usual homework) with two folders: 
  - one `workflow` folder contains all the agents, skills, code for your generic workflow generating the paper;  
  - one `exam_paper` folder contains all the code like the data analysis, tex code, etc used to generate the paper in the midterm exam. You should include all the data, code, output, and documentation in this repository. 
  - `Readme.md` file in the root folder should describe how to run the workflow and the agents or skills you used.
  - We encourage you to add in your workflow about generating any post-paper products like the slides, paper presentation video, paper website with interactive visualization, etc. Describe in `Readme.md` the automatic workflow to generate the products. Add the products to the `exam_paper` folder. These products are not required during the exam. You can generate them after the exam.

- **Tutorial for Automated Research Workflow** (due March 26th): 
  - Write a tutorial about how to design the workflow and how to organize the agents or skills for a generic research workflow. Post the tutorial on your coding blog website and add a link to the tutorial in the `Readme.md` file of the midterm project repository. An example of the tutorial is [here](https://psantanna.com/claude-code-my-workflow/) but you could be creative.
  - Record a tutorial video about how to use the workflow and the agents or skills you used. Post the video (or the link to the video) on your coding blog website and add a link to the video in the `Readme.md` file of the midterm project repository. 

## Detailed Requirements

1. Midterm Exam:
   - The datasets will be in the area of public health. The format will be only in csv, xlsx, text, and markdown files about the data description. There will be multiple datasets which are related to each other. 
   - At least one squad member should be present in class during the exam to implement the workflow onsite.
   - We will post a new repository in our class github organization like `exam_folder_sample` when the exam starts. The repository will contain a new dataset.
   - You should follow the tex template in the `./sample/tex/template.tex` file to generate the paper. The paper should follow the JAMA Network Open style with the sections in the template. The supplementary section is optional but we encourage you to include at least one supplementary section about the details of the statistical modeling and analysis. The only deliverable for the midterm exam is the `paper.pdf` file. You should turn in the `paper.pdf` file in canvas->Assignment->Midterm Paper before the class ends.
   - The page limit will be within **10 pages** excluding the references and supplementary sections.
   - Each squad team only needs to submit one `paper.pdf` through one squad member in the canvas.
   - The work should be done on the laptop of one of the squad members. Before the exam, the squad member should open the zoom, share your desktop screen, and record the screen to cloud. After downloading the data to your project folder, we expect you to simply input the prompt `Write a paper using the data in the folder` and let the workflow run automatically. We will watch your screen recording and evaluate how automatic your workflow is. You may consider to set up your AI tools to allow everything, like the `--allow-all-tools` in `copilot-cli` and the `--dangerously-skip-permissions` in Claude Code. **Add the link to the screen recording in the canvas submission by the noon of the day of the exam.**
   - Your workflow should be able to automatically generate the research question or hypothesis based on the dataset.
   - You are allowed to download any external data to support your paper. But the core analysis should be based on the dataset we provide.
   - Carefully design your workflow to make sure you could get a paper within 90 minutes during the exam.
   - Develop and test your workflow using the sample dataset and other datasets to make your workflow robust and reliable.

2. Midterm Project Repository:
   - The repository should be in our class github organization.
   - The repository should contain two folders:
     - one `workflow` folder contains all the agents, skills, code for your generic workflow generating the paper;  
     - one `exam_paper` folder contains all the code like the data analysis, tex code, etc used to generate the paper in the midterm exam. You should include all the data, code, output, and any post-paper products like slides, paper presentation video, paper website with interactive visualization, etc in this folder. 
   - The `Readme.md` file in the root folder should describe how to run the workflow and the agents or skills you used. 
   - Add the links to your tutorial and tutorial video in the `Readme.md` file.

3. Tutorial for Automated Research Workflow
   - Your tutorial should be beginner-friendly and self-contained.
   - Your tutorial could be based on the data example chosen by yourself.
   - There is no requirement on the length of the tutorial and the tutorial video. But you should be able to explain the workflow and the agents or skills you used in a way that is easy to understand.
   - The video could be recorded based on any methods (even using AI video generation tools) and the link to the video could be any platform (even YouTube, Zoom cloud link, etc) as long as it is accessible by the graders.


## Grading Rubric

The midterm project will be graded based on the following criteria:

### 1. Paper Quality (30%)
Evaluated based on the standards of a novel JAMA Network Open research paper. This is graded based on the `paper.pdf` file you submitted in the midterm exam.
- **Research Findings**: Are the findings solid, novel, and scientifically sound?
- **Statistical Modeling**: Is the statistical analysis appropriate, rigorous, and correctly implemented?
- **Visualization**: Are the figures and tables clear, informative, and of publication quality?
- **Paper Writing**: Is the writing clear and following the JAMA Network Open style and structure?
- **Turing Test**: Does the paper look like a human wrote it?

### 2. Workflow Automation (30%)
Evaluated based on the efficiency and autonomy of the AI workflow. This is graded based on the github repository contents and the screen recording you submitted in the midterm exam.
- **Level of Automation**: How much human intervention was required? (Higher automation = higher grade)
- **Multi-Agent Integration**: Did the workflow has a good design on the orchestration of the agents or skills to the end-to-end automatic generation of the paper?
- **Post-Paper Products**: Did the workflow include some automatic generation of any post-paper products like slides, paper presentation video, paper website with interactive visualization, etc?

### 3. Tutorial and Video (40%)
Evaluated based on the educational value and engagement of the deliverables. This is graded based on the tutorial and tutorial video you submitted.
- **Clarity**: Is the tutorial easy to follow and understand for beginners?
- **Interestingness**: Is the content has the visuals, animations, or other creative elements to make it engaging? Does the video effectively demonstrate the workflow?

## References

- [Autonomous Policy Evaluation Project](https://ape.socialcatalystlab.org/)
- [Claude Code Academic Workflow](https://psantanna.com/claude-code-my-workflow/)
- [Claude Skills Development](https://github.com/daymade/claude-code-skills)
- [Fully Automated Research System](https://analemma.ai/fars)
- [OpenClaw Automation for Research](https://github.com/tsingyuai/scientify)
