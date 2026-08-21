"""
What a 500 tells the caller, and what it tells us.

Twenty-nine handlers ended in the same two lines:

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

which is backwards in both directions at once.

**Outward**, `str(exc)` on an arbitrary exception is whatever the exception
happens to say. From psycopg2 that is table and column names, the text of the
failing statement, constraint names, and — on a connection failure — the host
and database from the DSN. That goes to any authenticated caller, which in this
product includes every officer at every institutional client. The playbook rates
a data controversy as existential; handing one tenant the shape of the database
another tenant's data sits in is a small, free step toward one.

**Inward**, none of it was logged. `logger.exception` was never called on these
paths, so the one place the traceback belonged — the server log an operator
reads at 2am — was the one place it did not go.

So: log the traceback, return a sentence that says what happened without saying
how, and give the caller a reference they can quote so support can find the log
line. The reference is random per occurrence and means nothing on its own.

WHAT THIS IS NOT FOR
--------------------
Deliberate 4xx messages. When a pure domain module raises `ValueError("A season
cannot be closed before it opens")`, that string is written for a farmer to
read, and `season_lifecycle_routes` turning it into a 409 detail is the design —
the frontend's `messageFor(kind, detail)` prefers it over the generic sentence
for exactly that reason. Those stay as they are. This is only for the catch-all
`except Exception`, where nobody chose the words.
"""

import logging
import uuid

from fastapi import HTTPException

logger = logging.getLogger("kurimasense")


def internal_error(exc: Exception) -> HTTPException:
    """
    Log an unhandled exception and build the 500 to raise for it.

    Returns rather than raises so the call site keeps its `raise`, which is what
    makes the control flow visible at the point it happens:

        except Exception as exc:
            raise internal_error(exc)

    `logger.exception` records the full traceback, so the failing file and line
    are in the log without the call site having to name itself — one less thing
    to get wrong when a handler is copied.
    """
    reference = uuid.uuid4().hex[:12]
    logger.exception("unhandled error [ref=%s]", reference)
    return HTTPException(
        status_code=500,
        detail=(
            "Something went wrong on our side. Nothing you did caused this. "
            f"If it keeps happening, quote reference {reference}."
        ),
    )
