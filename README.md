# protean-edu

Educational mode for Hermes. It teaches a non-technical person to read the code their agents write, so they can direct the work and review it.

This is a Hermes plugin. It is not a fork of Hermes. A plugin can register a slash command. A fork would have to be re-merged every time Hermes updates.

## What you can run today

```
/edu on
/edu off
/edu status
/edu next
/edu help
```

`/edu on` turns teaching on for this profile. `/edu off` turns it off and keeps your place. The lessons are not written yet. `/edu next` says so, instead of inventing one.

## Install (once the remote exists)

```
hermes plugins install <owner>/protean-edu
hermes plugins enable protean-edu
```

Then start a new Hermes session. Plugin commands load at startup.

## Check the command without installing Hermes

```
python3 -m pytest tests/test_edu_command.py -q
```

Five tests. They prove `/edu` registers, `/edu on` writes a state file, and `/edu off` does not wipe progress.
