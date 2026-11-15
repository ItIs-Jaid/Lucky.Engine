# S-repo-map — PRE-LOOP

**Purpose** — never edit a file you have not located in the call graph.

## Do
1. Read the entry point and the test entry point.
2. `rg` the symbol you are changing. List every call site.
3. Name the invariant that must survive.
4. Stop when you can say what breaks if this change is wrong.

## Gate
Call sites enumerated and the invariant written in one sentence.
