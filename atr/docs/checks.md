# 2.3. Checks

**Up**: `2.` [User guide](user-guide)

**Prev**: `2.2.` [Signing artifacts](signing-artifacts)

**Next**: `2.4.` [License checks](license-checks)

**Sections**:

* [Overview](#overview)
* [How ATR selects checks](#how-atr-selects-checks)
* [Understanding check results and ignores](#understanding-check-results-and-ignores)
* [Individual checks](#individual-checks)
* [SBOM checks](#sbom-checks)
* [Check caching and reruns](#check-caching-and-reruns)
* [Project policy inputs](#project-policy-inputs)

## Overview

ATR runs automated checks on release artifacts so that you can validate compliance and completeness before a vote. The checks focus on signatures, hashes, archive layout, licensing, and software bill of materials (SBOM) content. This document explains what ATR checks, when those checks run, and how to interpret results.

Checks are recorded against the release revision that you upload, and the results remain visible to reviewers and voters. The checks run in the background and appear in the checks view for the revision as they complete.

## How ATR selects checks

When you create or update a draft revision, ATR scans the files in the revision directory and schedules checks based on file suffix and project policy. A signature file with the `.asc` suffix triggers signature verification. A checksum file with the `.sha256` or `.sha512` suffix triggers hash verification. Archive files with the `.tar.gz`, `.tgz`, or `.zip` suffix trigger archive integrity, archive structure, and license checks. Files with the `.cdx.json` suffix trigger SBOM analysis. ATR also runs a path and naming check across the entire revision.

Project policy tells ATR which artifacts are source artifacts and which are binary artifacts, and it supplies exclusion patterns for license related checks. Project policy also controls the license check mode for source artifacts. You can choose lightweight checks, Apache RAT, or both for source artifacts. Binary artifacts are not scanned by RAT, and always rely on the lightweight checks.

## Understanding check results and ignores

Each check result has a status of success, warning, failure, or exception. Success indicates that the check completed without issues. Warning indicates a potential policy concern that needs review. Failure indicates a clear problem such as a missing file, invalid signature, or invalid license. Exception indicates that the check could not complete due to some unexpected internal ATR error.

If certain checks are producing false positives, or outcomes that you'd like to ignore for reasons particular to your project, then you can ignore them using special rules. Please try to minimise the use of such rules. If you would like checks to change for all projects, you can file an ATR issue.

Ignore rules match on the checker key and other fields. Only warning, failure, and exception results can be ignored. Each check section below names the exact checker key that ATR records for that check.

You can [read more about check ignores](check-ignores).

## Individual checks

### Path and naming checks

ATR validates the file layout of the revision against ASF release rules. For each artifact it expects a matching signature file with the `.asc` suffix and at least one checksum file with the `.sha256` or `.sha512` suffix. It verifies that metadata files correspond to an existing artifact and warns when a metadata suffix is recommended against by policy. It rejects `.md5` checksums and `.sig` signature files and warns about `.sha1` and `.sha`. It rejects dotfiles except for those under the `.atr` directory, and it rejects a `KEYS` file inside the artifact bundle because keys are managed through the keys section. If the project is a podling, it requires the word "incubating" in artifact filenames.

This check records separate checker keys for errors, warnings, and success. Use `atr.tasks.checks.paths.check_errors` for failures and `atr.tasks.checks.paths.check_warnings` for warnings when you configure ignores.

(Success results use `atr.tasks.checks.paths.check_success` but are not eligible for ignores.)

### Hash verification

For each `.sha256` or `.sha512` file, ATR computes the hash of the referenced artifact and compares it with the expected value. It supports files that contain just the hash as well as files that include a filename and hash on the same line. If the suffix does not indicate `sha256` or `sha512`, the check fails.

The checker key is `atr.tasks.checks.hashing.check`.

### Signature verification

For each `.asc` signature file, ATR verifies the signature against the matching artifact using the public keys stored for the release committee. The signature is accepted only when it verifies and when the signing key is associated with an ASF UID or matches the committee private email address pattern of `private@`[_committee name_]`.apache.org`. If no suitable key is found or the signature does not match the artifact, the check fails.

The checker key is `atr.tasks.checks.signature.check`.

### Archive integrity checks

ATR checks that each `.tar.gz`, `.tgz`, or `.zip` archive can be read in full. For tar based archives it reads all members using the tar reader. For zip archives it lists members and verifies that the zip structure is valid. Archives that are corrupted or contain too many members fail this check.

The checker key for tar based archives is `atr.tasks.checks.targz.integrity`, and the checker key for zip archives is `atr.tasks.checks.zipformat.integrity`.

### Archive structure checks

ATR expects each archive to contain exactly one root directory. The expected root name is derived from the archive filename base, without extension. When the archive filename base ends with the suffix `source` or `src`, ATR accepts a root directory that either includes that suffix or omits it. When the archive filename base has no such suffix, the root directory must match the base. If the root does not match, ATR records a warning so that you can review project conventions. Structure checks are skipped for artifacts that are classified as binary by project policy.

ATR also recognizes `npm pack` archives. When the root directory is named package, ATR looks for a file named `package.json` and validates that it contains a name and version. If the file is present and valid, ATR treats this layout as acceptable. If the package name and version do not match the archive filename base, ATR records a warning.

The checker key for tar based structure checks is `atr.tasks.checks.targz.structure`. The checker key for zip structure checks is `atr.tasks.checks.zipformat.structure`.

### License files in archives

ATR checks for `LICENSE` and `NOTICE` files at the top level of the root directory each archive. It requires exactly one of each. The `LICENSE` content must match the Apache License text with only whitespace differences. The `NOTICE` file must be valid UTF-8 text and must include a product line, an ASF copyright statement, and the standard ASF attribution line. For podling projects ATR also requires a `DISCLAIMER` or `DISCLAIMER-WIP` file at the same level. These lightweight license checks can run for both source and binary archives but if your project selects Apache RAT only for source artifacts, the lightweight checks are skipped for source archives. They still run for binary archives.

The checker key is `atr.tasks.checks.license.files`.

You can [read more about license checks](license-checks).

### License headers in source files

ATR performs a lightweight scan of source files inside each archive to verify Apache License headers. It inspects the first four kilobytes of each file with a recognized source file suffix and checks for the standard Apache License header text. Files with generated file suffixes such as `.bundle.js`, `.chunk.js`, `.css.map`, `.js.map`, `.min.css`, `.min.js`, and `.min.map` are treated as generated and are skipped. Files that include generated markers such as `Generated By JJTree` or `Generated By JavaCC` are always accepted as valid. If you configure lightweight exclusions in your project policy, those patterns are also skipped for source artifacts.

The checker key is `atr.tasks.checks.license.headers`.

You can [read more about license checks](license-checks).

### Apache RAT license scan

ATR can run Apache RAT on source archives unless your project policy selects lightweight mode only. RAT runs in a temporary extraction directory, uses standard exclusions for common SCM and IDE files, and always excludes known generated file patterns. If the archive includes a RAT excludes file with the standard name `.rat-excludes`, ATR uses it as the exclusion file and sets the scan root to the directory that contains it. ATR records an error if more than one such file is present or if files exist outside that scan root. If no such file exists, ATR can apply project policy RAT exclusions and an extended set of standard exclusions. The check records failures for unapproved or unknown licenses, and records per file results for those files. RAT does not run for binary artifacts, even if those files are packaged in an archive format that otherwise triggers license checks.

The checker key is `atr.tasks.checks.rat.check`.

You can [read more about license checks](license-checks).

## SBOM checks

ATR recognizes CycloneDX SBOM files with the `.cdx.json` suffix. When you upload such a file, ATR runs a special scoring tool check that evaluates NTIA 2021 conformance, CycloneDX validation results, license signals, and vulnerability data derived from the SBOM. If a previous release exists, ATR compares current and prior license and vulnerability information and records that context with the result. ATR also provides additional SBOM tasks that you can run from the interface: you can ask ATR to generate a CycloneDX SBOM from an archive using the syft tool, to score a SBOM using SBOM QS, to augment an existing SBOM with NTIA properties, or to run an OSV vulnerability scan that updates the SBOM. These tasks may create a new revision because the SBOM file is updated with new content.

SBOM tasks record task results rather than check results, so there is no checker key to use in ignore rules for SBOM tasks. The results are presented separately from regular checks, on their own page.

## Check caching and reruns

To save time, ATR will sometimes reuse results from a prior revision when a file has not changed. The system computes a content hash and copies earlier results so that the same check does not run again.

_For debugging only_, if you need a fresh run, place a file named `.atr-no-cache` in the revision root. When that file is present, ATR does not reuse cached results for that revision. We may remove this functionality.

## Project policy inputs

Several checks depend on project policy. You can define which paths are considered source artifacts and which are considered binary artifacts, and you can define exclusion patterns for the RAT scan and for the lightweight license header check. These settings affect which checks run and which files are skipped. If no policy pattern matches a file, ATR treats it as a source artifact for the purpose of the lightweight and RAT license checks.
