# **che**[ck-e]**xtra** 🔎

[![python](https://img.shields.io/pypi/pyversions/chextra)](https://pdm.fming.dev)
[![pyPI](https://img.shields.io/pypi/v/chextra)](https://pypi.org/project/chextra)
[![docs](https://img.shields.io/badge/doc-pages-blue)](https://a-recknagel.github.io/chextra/)
[![pdm-managed](https://img.shields.io/badge/packaging-pdm-blueviolet)](https://pdm.fming.dev)
[![license](https://img.shields.io/pypi/l/chextra)](https://github.com/a-recknagel/chextra/blob/main/LICENSE)
[![chat](https://img.shields.io/badge/chat-gitter-mediumturquoise)](https://matrix.to/#/#chextra:gitter.im)

When you're writing a python library, being able to define [extras][1] is 
sweet. People who are either new to programming in general or python's
dynamic nature specifically might be caught off-guard by this feature though,
so it might be nice to give them a little help when they run into

```python
Traceback (most recent call last):
  File "/home/me/code.py", line 1, in <module>
    import foo
ModuleNotFoundError: No module named 'foo'
```

instead of letting them assume that you shipped them a broken distribution.

## Usage

This package can be pip-installed
```shell
pip install chextra
```

If you decide that this is a feature that you want in your library, you
have to [declare `chextra` as a project dependency][3] as well.

### Expected Project Layout

Code that relies on extras being installed will usually sit in a 
sub-package as a kind of barrier between it and the rest of the code.

It makes sense for the sub-package to have the same name as
the extra, since extras are supposed to denote a functionality, which
coincides with package naming conventions.

Given a distribution `foo` with an extra `bar`, this would be the expected
structure:

```text
foo
├── __init__.py
└── bar
    ├── __init__.py
    └── code.py 
```

### Triggering a Warning

You only need add the following code to the `__init__.py` of the sub-package:

```python title="foo/bar/__init__.py"
import chextra

chextra.warn(pkg="foo", extras="bar")
```
And you're done. If someone tries to run `import foo.bar` or `from foo.bar
import code`, they'll get the following message:

```text
/home/me/my_project.py:3: UserWarning: 
    The feature you're trying to use requires the extra 'bar', 
    install it by running `pip install foo[bar]`.
  chextra.warn(pkg="foo", extras="bar")
```

If the code is only executed within an attempted import and your extra has
the same [normalized][4] name as the sub-package, you can also omit the
arguments, since their values can be guessed from context.

```python title="foo/bar/__init__.py"
import chextra

chextra.warn()
```

## Focus

This package tries to be light-weight and not any fancier than it needs to.
Installing dependencies automatically when they were found to be missing
might sound great, but has been proven to be [a bad idea][2].

[1]: https://peps.python.org/pep-0508/#extras
[2]: https://pip.pypa.io/en/latest/user_guide/#using-pip-from-your-program
[3]: https://peps.python.org/pep-0621/#dependencies-optional-dependencies
[4]: https://peps.python.org/pep-0685/#specification