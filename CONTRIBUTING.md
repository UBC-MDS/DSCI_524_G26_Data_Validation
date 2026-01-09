# Contributing

Contributions of all kinds are welcome here, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

## Example Contributions

You can contribute in many ways, for example:

- [Contributing](#contributing)
  - [Example Contributions](#example-contributions)
    - [Report Bugs](#report-bugs)
    - [Fix Bugs](#fix-bugs)
    - [Implement Features](#implement-features)
    - [Write Documentation](#write-documentation)
    - [Submit Feedback](#submit-feedback)
  - [Get Started!](#get-started)
    - [Pull Request Guidelines](#pull-request-guidelines)

### Report Bugs

Report bugs at https://github.com/EduardoRasanmar/data_validation/issues.

**If you are reporting a bug, please follow the template guidelines. The more
detailed your report, the easier and thus faster we can help you.**

### Fix Bugs

Look through the GitHub issues for bugs. Anything labelled with `bug` and
`help wanted` is open to whoever wants to implement it. When you decide to work on such
an issue, please assign yourself to it and add a comment that you'll be working on that,
too. If you see another issue without the `help wanted` label, just post a comment, the
maintainers are usually happy for any support that they can get.

### Implement Features

Look through the GitHub issues for features. Anything labelled with
`enhancement` and `help wanted` is open to whoever wants to implement it. As
for [fixing bugs](#fix-bugs), please assign yourself to the issue and add a comment that
you'll be working on that, too. If another enhancement catches your fancy, but it
doesn't have the `help wanted` label, just post a comment, the maintainers are usually
happy for any support that they can get.

### Write Documentation

data_validation could always use more documentation, whether as
part of the official documentation, in docstrings, or even on the web in blog
posts, articles, and such. Just
[open an issue](https://github.com/EduardoRasanmar/data_validation/issues)
to let us know what you will be working on so that we can provide you with guidance.

### Submit Feedback

The best way to send feedback is to file an issue at
https://github.com/EduardoRasanmar/data_validation/issues. If your feedback fits the format of one of
the issue templates, please use that. Remember that this is a volunteer-driven
project and everybody has limited time.

## Get Started!

Follow these steps to set up the project locally and start contributing.

1. Fork the repository on GitHub:  
   https://github.com/UBC-MDS/DSCI_524_G26_Data_Validation

2. Clone your fork locally:

    ```shell
    git clone git@github.com:your_github_username/DSCI_524_G26_Data_Validation.git
    cd DSCI_524_G26_Data_Validation
    ```

3. Create and activate the Conda environment using the provided `environment.yml` file
   (this environment already includes Hatch):

    ```shell
    conda env create -f environment.yml
    conda activate data_validation
    ```

4. Create a new branch from the default branch (`main`).  
   Use `fix/` or `feat/` as a prefix for your branch name:

    ```shell
    git checkout main
    git pull
    git checkout -b fix-short-description
    ```

5. Make your changes locally. When finished, run the test suite:

    ```shell
    hatch run test:run
    ```

6. Commit your changes and push your branch to GitHub.  
   Please use [semantic commit messages](https://www.conventionalcommits.org/):

    ```shell
    git add .
    git commit -m "fix: short description of change"
    git push -u origin fix-short-description
    ```

7. Open a pull request against the `main` branch using the link shown after pushing.


### Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your
   new functionality into a function with a docstring.
3. Your pull request will automatically be checked by the full test suite.
   It needs to pass all of them before it can be considered for merging.
