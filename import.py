import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


f = open('books.csv')
reader = csv.reader(f)
next(reader, None)
for isbn, title, author, year in reader:
	# add author to authors table
	db.execute("INSERT INTO authors (name) VALUES (:name)", {'name': author})
	db.commit()
	# populate books table now because we know the foreign key for the author
	author_id = db.execute("SELECT id FROM authors WHERE name=(:name)", {'name': author}).fetchone()
	db.execute('INSERT INTO books (isbn, title, year, author_id) VALUES (:isbn, :title, :year, :author_id)', {'isbn': isbn, 'title': title, 'year': year, 'author_id':author_id[0]})
	db.commit()

