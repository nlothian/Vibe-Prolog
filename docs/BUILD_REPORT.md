# Build Report

# What was easy

Getting a working Prolog interpreter that could handle most basic code. 

# What was hard

I decided without much thought that this should be an ISO-Standard implementation. I later discovered the ISO standard is $800 which I'm not prepared to pay. ChatGPT seems to know it quite well (better than Claude) and I wonder if it has been trained on it. 

I soon discoved most code relied on Prolog libraries which I didn't have. Without much though - again - I imported the (Scryer Prolog library)[https://github.com/mthom/scryer-prolog/tree/master/src/lib] to let me run programs and soon realized that library loading is completely non-standard.



## Things where AI didn't work

```
uv run vibeprolog.py ./examples/not\ yet\ working/sudoku.pl
Error loading program: error(syntax_error(No terminal matches 's' in the current parser context, at line 1 col 29

:- non_counted_backtracking setup_call_cleanup/3.
                            ^
Expected one of:
        * INFIX_XFY_600_17
        * INFIX_YFX_400_12
        * INFIX_YFX_400_11
        * INFIX_XFX_1200_38
        * INFIX_YFX_500_14
        * INFIX_XFX_700_29
        * INFIX_XFX_700_24
        * OPERATOR_ATOM
        * INFIX_YFX_400_10
        * INFIX_XFX_700_31
        * INFIX_XFX_700_28
        * INFIX_YFX_500_15
        * INFIX_XFY_1050_36
        * INFIX_XFX_700_21
        * INFIX_XFX_700_33
        * INFIX_XFX_700_27
        * INFIX_XFX_700_19
        * INFIX_YFX_500_16
        * INFIX_YFX_400_7
        * LPAR
        * INFIX_XFY_1100_37
        * INFIX_XFY_1000_35
        * INFIX_XFY_200_1
        * INFIX_XFX_700_18
        * INFIX_XFX_700_20
        * INFIX_XFX_700_23
        * INFIX_XFX_700_25
        * DCG_ARROW
        * INFIX_XFX_700_26
        * INFIX_XFY_200_2
        * INFIX_YFX_500_13
        * INFIX_XFX_700_22
        * INFIX_YFX_400_8
        * INFIX_XFX_700_30
        * INFIX_XFX_1200_39
        * INFIX_YFX_400_9
        * INFIX_YFX_400_5
        * INFIX_YFX_400_6
        * DOT
        * INFIX_XFX_700_32
), context(consult/1))
```

But *I* don't know what that means, so I ask AI:

> I run 
> ```
> paste error message here
> ```
> 
> What does this mean?

and then I have to decide what to do.

In this case I get:

```
  The error means Vibe-Prolog doesn't recognize non_counted_backtracking as a directive.                                                                 █
                                                                                                                                                         █
  This is a Scryer-Prolog specific directive (the library files are from Scryer). It's declared as a prefix operator in ops_and_meta_predicates.pl, but: █
                                                                                                                                                         █
  1. The operator is defined with op(700, fx, non_counted_backtracking)                                                                                  █
  2. When library(clpz) loads library(iso_ext), the parser encounters :- non_counted_backtracking setup_call_cleanup/3 before the operator definition    █
     is registered                                                                                                                                       █
                                                                                                                                                         █
  The parser sees non_counted_backtracking as a regular atom followed by setup_call_cleanup/3, but expects an operator between them (that's why it       █
  lists all those INFIX_* options).                                                                                                                      █
                                                                                                                                                         █
  Quick fix: These are Scryer-specific declarations that affect inference counting (for debugging). They can safely be ignored. You could either:        █
                                                                                                                                                         █
  1. Comment out those lines in the library files                                                                                                        █
  2. Add support for this directive to be silently ignored                                                                                               █
                                                                                                                                                         █
  Would you like me to implement support for ignoring this unknown directive?
```

This isn't something that I can delegate easily. I know from history there might be other similar directives, so just handling this 
as a one-off won't work. In this case - after further discussion - this is what I ended up:

```
 Use `gh issue` to raise 3 issues:                                                                                                                       │
 - add an ignore list with non_counted_backtracking and meta_predicate. Warn during the loading/parsing phase when these are encounted                   │
 - implement if/else/endif                                                                                                                               │
 - implement table - memoization                                                                                                                         │
                                                                                                                                                         │
 Be explicit in outlining exactly what needs to be done so an inexperienced developer can follow it.                                                     │
                                                                                                                                                         │
 Be sure to include the following in each issue                                                                                                          │
 - include comprehensive test coverage                                                                                                                   │
 - update FEATURES.md                                                                                                                                    │
                                                                                                                                                         │
 Don't include estimates or line numbers
```

This raise these three issues:
- https://github.com/nlothian/Vibe-Prolog/issues/268
- https://github.com/nlothian/Vibe-Prolog/issues/269
- https://github.com/nlothian/Vibe-Prolog/issues/270
  
It certianly did a better job raising them than I would have.
