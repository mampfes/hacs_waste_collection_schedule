<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Contributing To Waste Collection Schedule

![python badge](https://img.shields.io/badge/Made%20with-Python-orange)
![github contributors](https://img.shields.io/github/contributors/mampfes/hacs_waste_collection_schedule?color=orange)
![last commit](https://img.shields.io/github/last-commit/mampfes/hacs_waste_collection_schedule?color=orange)

There are several ways of contributing to this project, including:

- Providing new service providers
- Updating or improving the documentation
- Helping answer/fix any issues raised
- Join in with the Home Assistant Community discussion

## Adding New Service Providers

### Fork And Clone The Repository, And Checkout A New Branch

In GitHub, navigate to the repository [homepage](https://github.com/mampfes/hacs_waste_collection_schedule). Click the `fork` button at the top-right side of the page to fork the repository.

![fork](/images/wcs_fork_btn.png)

Navigate to your fork's homepage, click the `code` button and copy the url.

![code](/images/wcs_code_btn.png)

On your local machine, open a terminal and navigate to the location where you want the cloned directory. Type `git clone` and paste in the url copied earlier. It should look something like this, but with your username replacing `YOUR-GITHUB-USERNAME`:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/hacs_waste_collection_schedule
```

Before making any changes, create a new branch to work on.

```bash
git branch <new_branch_name>
```

For example, if you were adding a new provider called abc.com, you could do

```bash
git branch adding_abc_com
```

For more info on forking/cloning a repository, see GitHub's [fork-a-repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo) document.

### The 2 Ways of adding support for a new Service Provider

There are 2 ways to add support for a new service provider:

1. [Via the generic ICS source](contributing_ics.md)

   This is the preferred way of adding support for a new service provider, but only works if the service providers offers a so called "ical / webcal subscription" or at least a static link which doesn't change over time to an ICS file.

2. [Dedicated source](contributing_source.md)

   This is the fallback if the preferred way via the generic ICS source doesn't work.

### Sync Branch and Create A Pull Request

Having completed your changes, sync your local branch to your GitHub repo, and then create a pull request. When creating a pull request, please provide a meaningful description of what the pull request covers. Ideally it should cite the service provider, confirm the .py, .md, README and info.md files have all been updated, and the output of the test_sources.py script demonstrating functionality. Once submitted a number of automated tests are run against the updated files to confirm they can be merged into the master branch. Note: Pull requests from first time contributors also undergo a manual code review before a merge confirmation in indicated.

Once a pull request has been merged into the master branch, you'll receive a confirmation message. At that point you can delete your branch if you wish.

## Update Or Improve The Documentation

Non-code contributions are welcome. If you find typos, spelling mistakes, or think there are other ways to improve the documentation please submit a pull request with updated text. Sometimes a picture paints a thousand words, so if a screenshots would better explain something, those are also welcome.

## Help Answer/Fix Issues Raised

![GitHub issues](https://img.shields.io/github/issues-raw/mampfes/hacs_waste_collection_schedule?color=orange)

Open-source projects are always a work in progress, and [issues](https://github.com/mampfes/hacs_waste_collection_schedule/issues) arise from time-to-time. If you come across a new issue, please raise it. If you have a solution to an open issue, please raise a pull request with your solution.

## Join The Home Assistant Community Discussion

![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)

The main discussion thread on Home Assistant's Community forum can be found [here](https://community.home-assistant.io/t/waste-collection-schedule-framework/186492).
