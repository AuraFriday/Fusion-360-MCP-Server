# How to Contribute to mcp-link-server

We deeply appreciate community interest in improving mcp-link-server. To protect our users and maintain the project's stringent security, quality, and a unified codebase, we follow a centralized contribution model:

**This project does not use GitHub Forks or Pull Requests.** All contributions are submitted as patch files directly to an issue ticket after discussion with the maintainer. Please follow the process below carefully.

### Our Contribution Process

1.  **Propose Your Change in an Issue:** Before writing any code, please **[open a new GitHub Issue](https://github.com/AuraFriday/mcp-link-server/issues/new/choose)**. This initial discussion ensures your proposed work aligns with the project's direction.

2.  **Agree to the Contributor License Agreement (CLA):** We cannot review or accept any code until you have publicly agreed to our [CLA](CONTRIBUTOR_LICENSE_AGREEMENT.md). Once your proposal in the Issue has been acknowledged, please paste the following exact statement as a new comment in your Issue thread:
    > `I have read and agree to the Contributor License Agreement (CLA) located in this repository's CONTRIBUTOR_LICENSE_AGREEMENT.md file. I understand that this assignment of rights is a precondition to my contribution being considered for acceptance.`

3.  **Submit Your Code as a Patch File:** Once approved, prepare and attach your patch file(s) to the GitHub Issue as instructed in the guide below. **Do NOT submit a Pull Request.**

---

### How to Prepare and Submit Your Code Contribution

This guide will walk you through the entire process, from getting the code to generating the final patch file.

**Step 0: Get the Code (The Right Way)**

First, you need a local copy of our official repository.

```bash
# Clone the repository from the official AuraFriday source.
# Do NOT work from an unauthorized fork.
git clone https://github.com/AuraFriday/mcp-link-server.git

# Navigate into the newly created directory
cd mcp-link-server
```

**Step 1: Ensure Your Local Branch is Up-to-Date**

Before starting any work, make sure your local `master` branch has the very latest changes from our repository.

```bash
git checkout master
git pull origin master
```

**Step 2: Create a Dedicated Branch for Your Work**

Never work directly on your `master` branch. Creating a feature branch isolates your changes and simplifies patch creation.

```bash
# Name the branch something descriptive
git checkout -b feature/my-new-tool
```

**Step 3: Write Your Code and Make Atomic Commits**

This is the most important step for a clean patch.
*   Make small, logical changes.
*   Create a new commit for each logical change.
*   Write clear and descriptive commit messages that explain the *what* and *why* of your change.

```bash
# Example of a good commit workflow
# (edit file1.js, file2.js)
git add .
git commit -m "feat: Add geolocation tool foundation"

# (edit file3.js)
git add .
git commit -m "fix: Correct error handling in geolocation response"
```
**Pro Tip:** One feature might be several commits. This is good! It makes your changes easier to review.

**Step 4: Generate the `.patch` File(s)**

Once your feature is complete, use the `git format-patch` command. This will create one `.patch` file for each commit you made on your feature branch.

```bash
# This compares your current branch to our primary branch ('master') and creates the patches.
git format-patch master
```
This command will create numbered files in your directory, like `0001-feat-Add-geolocation-tool-foundation.patch`, `0002-fix-Correct-error-handling-in-geolocation-response.patch`, etc.

**Step 5: Attach the Patch(es) to Your GitHub Issue**

*   If you have only one `.patch` file, attach it directly to your comment in the GitHub Issue.
*   If you have multiple `.patch` files, please compress them into a single `.zip` archive and attach that zip file to the issue.

---

### Legal Notice: All Contributions Belong to Aura Friday

**This is critical.** By submitting any contribution (including code, documentation, or ideas) in any form, you are agreeing to the terms of the CLA and irrevocably assigning all copyright, patent, and other intellectual property rights for that contribution to **Aura Friday**

Thank you for helping us build a secure and coherent ecosystem.

<small><sup>Copyright © 2025 Christopher Drake. All rights reserved. "signature": "4ȷⅼВN𝙰еȣƎꓳAТᗷꓟƛĵ7о𝟑һ𐐕ϜⲢꓔƌɋKᒿU1𝛢𝕌τꓬᏴUꓗl26NQꓮΤȣȷꓜ𝐴𝟨ο𝟩ꓚȠᴡDТH𝟪ԝ𝟩ŧSKɡΒC𝘈0ᗪЅJꓧꓦƿꓖᏟ𝙰Ᏼ𝟩ƋꓦƏꜱƎɪʌ𐓒ßꓧꓰᴅᏟ𐓒ʋᴜ𝟛υuƟᏮΥWlᴠЕƴѵᴅ". "signdate":"2025-10-30T02:35:27.473Z" </sup></small>
