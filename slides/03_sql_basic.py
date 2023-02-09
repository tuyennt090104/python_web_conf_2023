### slide::
### title:: SQL Expression Language
# We begin with a Table object
from sqlalchemy import MetaData, Table, Column, String, Integer

metadata = MetaData()
user_table = Table(
    "user_account",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(50)),
    Column("fullname", String(50)),
)

### slide:: p
# new SQLite database and generate the table.

from sqlalchemy import create_engine

engine = create_engine("sqlite://")
with engine.begin() as conn:
    metadata.create_all(conn)

### slide::
# as we saw earlier, Table has a collection of Column objects,
# which we can access via table.    c.<columnname>

user_table.c.username

### slide::
# Column is part of a class known as "ColumnElement",
# which exhibit custom Python expression behavior.

user_table.c.username == "spongebob"

### slide::
# They are objects that can be **compiled** into a SQL string.   This
# process occurs when they are part of a statement to be executed.  It
# also can be viewed for debugging purposes by calling str() on the object.
str(user_table.c.username == "spongebob")

### slide:: i
# For more fine-grained inspection of the compilation process, the .compile()
# method provides the compiled form of the statement.   This includes the
# string statement itself, as well as the parameter values, which will
# have been taken from the literal values present in the statement.
compiled = (user_table.c.username == "spongebob").compile()
compiled.string
compiled.params


### slide::
### title:: Building bigger SQL constructs.
# ColumnElements are the basic building block of SQL statement objects.
# To compose more complex criteria, and_() and or_() for example provide the
# basic conjunctions of AND and OR.

from sqlalchemy import and_, or_

print(
    or_(
        user_table.c.username == "spongebob",
        user_table.c.username == "patrick"
    )
)

### slide:: i


print(
    and_(
        user_table.c.fullname == "spongebob squarepants",
        or_(
            user_table.c.username == "spongebob",
            user_table.c.username == "patrick",
        )
    )
)

### slide::
### title:: More Operators

# comparison operators =, !=, >, <, >=, =<, between()

print(and_(
    user_table.c.id >= 5,
    user_table.c.fullname.between('m', 'z'),
    user_table.c.fullname != 'plankton'
))

### slide:: i
# Compare to None produces IS NULL / IS NOT NULL

print(and_(
    user_table.c.username != None,
    user_table.c.fullname == None
))

### slide::
# Operators may also be type sensitive.
# "+" with numbers means "addition"....

print(user_table.c.id + 5)

### slide:: i
# ...with strings it means "string concatenation"

print(user_table.c.fullname + " Jr.")

### slide:: p
# the IN operator generates a special placeholder that will be filled
# in when the statement is executed
criteria = user_table.c.username.in_(["sandy", "squidward", "spongebob"])
print(criteria)

### slide:: pi
# When it is executed, bound parameters are generated as seen here
print(criteria.compile(compile_kwargs={'render_postcompile': True}))

### slide:: pi
# when given an empty collection, the placeholder generates a SQL
# subquery that represents an "empty set"

criteria = user_table.c.username.in_([])
print(criteria.compile(compile_kwargs={'render_postcompile': True}))



### slide:: p
### title:: Working with INSERT and SELECT Statements
# we can insert data using the insert() construct

insert_stmt = user_table.insert().values(
    username="spongebob", fullname="Spongebob Squarepants"
)

with engine.begin() as connection:
    connection.execute(insert_stmt)

### slide:: p
# The insert() statement, when not given values(), will generate the VALUES
# clause based on the list of parameters that are passed to execute().

with engine.begin() as connection:
    connection.execute(
        user_table.insert(), {"username": "sandy", "fullname": "Sandy Cheeks"}
    )

    # this format also accepts an "executemany" style that the DBAPI can optimize
    connection.execute(
        user_table.insert(),
        [
            {"username": "patrick", "fullname": "Patrick Star"},
            {"username": "squidward", "fullname": "Squidward Tentacles"},
        ],
    )

### slide:: p
# select() is used to produce any SELECT statement.

from sqlalchemy import select

with engine.connect() as connection:
    select_stmt = (
        select(user_table.c.username, user_table.c.fullname).
        where(user_table.c.username == "spongebob")
    )
    result = connection.execute(select_stmt)
    for row in result:
        print(row)

### slide:: lp
# select all columns from a table

with engine.connect() as connection:
    select_stmt = select(user_table)
    connection.execute(select_stmt).all()

### slide:: lp
# specify WHERE and ORDER BY

with engine.connect() as connection:
    select_stmt = select(user_table).where(
        or_(
            user_table.c.username == "spongebob",
            user_table.c.username == "sandy",
        )
    ).order_by(user_table.c.username)
    connection.execute(select_stmt).all()

### slide:: lp
# specify multiple WHERE, will be joined by AND

with engine.connect() as connection:
    select_stmt = (
        select(user_table)
        .where(user_table.c.username == "spongebob")
        .where(user_table.c.fullname == "Spongebob Squarepants")
        .order_by(user_table.c.username)
    )
    connection.execute(select_stmt).all()


### slide:: p
### title:: More Result Methods
# In the engine chapter, we were introduced to
# .all() and .first().   Result also has most of what
# previously was only in the ORM, such as the .one() and .one_or_none()
# methods.

connection = engine.connect()

# the one() method returns exactly one row
result = connection.execute(
    select(user_table.c.fullname).where(user_table.c.username == 'spongebob')
)
result.one()

### slide:: pi
# if there are no rows, or many rows, it raises an error.
result = connection.execute(
    select(user_table.c.fullname).order_by(user_table.c.username)
)
result.one()

### slide:: p
# one_or_none() will only raise if there are more than one row, but
# returns None for no result
result = connection.execute(
    select(user_table).where(user_table.c.username == 'nonexistent')
)
result.one_or_none()

### slide:: p
# result objects now support slicing at the result level.   We can SELECT
# some rows, and change the ordering and/or presence of columns after the
# fact using the .columns() method:

result = connection.execute(
    select(user_table).order_by(user_table.c.username)
)
for fullname, username in result.columns("fullname", "username"):
    print(f"{fullname} {username}")

### slide:: p
# a single column from the results can be delivered without using
# rows by applying the .scalars() modifier.   This accepts an optional
# column name, or otherwise assumes the first column:

result = connection.execute(
    select(user_table).order_by(user_table.c.username)
)
for fullname in result.scalars("fullname"):
    print(fullname)


### slide:: p
### title:: Working with UPDATE and DELETE Statements
# The update() construct is very similar to insert().  We can specify
# values(), which here refers to the SET clause of the UPDATE statement

with engine.begin() as connection:
    update_stmt = (
        user_table.update()
        .values(fullname="Patrick Star")
        .where(user_table.c.username == "patrick")
    )

    result = connection.execute(update_stmt)

### slide:: pi
# Like INSERT, it can also generate the SET clause based on the given
# parameters

with engine.begin() as connection:
    update_stmt = (
        user_table.update()
        .where(user_table.c.username == "patrick")
    )

    result = connection.execute(update_stmt, {"fullname": "Patrick Star"})

### slide:: p
# the update().values() method has an extra capability in that it can
# accommodate arbitrary SQL expressions as well

with engine.begin() as connection:
    update_stmt = (
        user_table.update().
        values(
            fullname=user_table.c.username + " " + user_table.c.fullname
        )
    )

    result = connection.execute(update_stmt)

### slide:: p
# and this is a DELETE

with engine.begin() as connection:
    delete_stmt = user_table.delete().where(user_table.c.username == "patrick")

    result = connection.execute(delete_stmt)


### slide::
### title:: Questions?

### slide::
